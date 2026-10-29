from __future__ import annotations

"""
Orquestrador local do DAG da Aurora Shop.

Executa o grafo definido em dag.py com os mesmos conceitos do Apache Airflow,
mas sem servidor, banco de metadados ou Linux: roda no Windows, offline.

    Conceito do Airflow        Aqui
    ─────────────────────      ─────────────────────────────────────────────
    DAG                        dag.TASKS (definição única)
    DAG Run / run_id           data/orchestration/runs/<run_id>/run.json
    Task Instance + log        data/orchestration/runs/<run_id>/<tarefa>.log
    retries / retry_delay      Task.retries / Task.retry_delay
    execution_timeout          Task.timeout
    upstream_failed            falha_upstream
    pool                       Task.pool + POOLS
    params / Trigger w/ config --param chave=valor
    Clear (failed)             --resume <run_id>
    airflow tasks test         --only <tarefa>
    max_active_runs = 1        trava em data/orchestration/runner.lock
    scheduler                  --every <segundos>

Exemplos:

    python -m bigdata_pipeline.orchestration.runner --graph
    python -m bigdata_pipeline.orchestration.runner
    python -m bigdata_pipeline.orchestration.runner --param max_quarantine_pct=2
    python -m bigdata_pipeline.orchestration.runner --resume last
    python -m bigdata_pipeline.orchestration.runner --history
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

from . import dag as dag_module
from .dag import DAG_ID, PARAMS, POOLS, S3_ENV, TASKS, Task, downstream_of, levels, render, tasks_by_id, topological_order


STATE_DIR = Path("data/orchestration")
RUNS_DIR = STATE_DIR / "runs"

# Estados de uma tarefa (entre parênteses, o nome equivalente no Airflow).
AGUARDANDO = "aguardando"            # (scheduled)
EXECUTANDO = "executando"            # (running)
NOVA_TENTATIVA = "nova_tentativa"    # (up_for_retry)
SUCESSO = "sucesso"                  # (success)
FALHOU = "falhou"                    # (failed)
FALHA_UPSTREAM = "falha_upstream"    # (upstream_failed)
REAPROVEITADA = "reaproveitada"      # sucesso de uma execução anterior (--resume)
NAO_SELECIONADA = "nao_selecionada"  # fora do recorte (--start-at / --only)
INTERROMPIDA = "interrompida"        # Ctrl+C

DONE_OK = {SUCESSO, REAPROVEITADA, NAO_SELECIONADA}
DONE_BAD = {FALHOU, FALHA_UPSTREAM, INTERROMPIDA}

_print_lock = threading.Lock()


def now() -> datetime:
    return datetime.now(timezone.utc)


def say(message: str) -> None:
    with _print_lock:
        print(f"{datetime.now():%H:%M:%S}  {message}", flush=True)


# ────────────────────────────────────────────────────────────────────────────
# Trava: no máximo uma execução do DAG por vez (max_active_runs = 1).
# O DuckDB aceita um único processo gravando no aurora.duckdb.
# ────────────────────────────────────────────────────────────────────────────
class RunLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle = None

    def __enter__(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise SystemExit(
                "Já existe uma execução do DAG em andamento (max_active_runs = 1). "
                "Aguarde terminar ou feche o terminal que a está executando."
            )
        return self

    def __exit__(self, *exc) -> None:
        try:
            if os.name == "nt":
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        self.handle.close()


# ────────────────────────────────────────────────────────────────────────────
# Execução
# ────────────────────────────────────────────────────────────────────────────
class DagRun:
    def __init__(
        self,
        run_id: str,
        run_type: str,
        params: dict[str, object],
        selected: set[str],
        reused: set[str] | None = None,
        max_parallel: int = 4,
    ) -> None:
        self.run_id = run_id
        self.run_type = run_type
        self.params = params
        self.max_parallel = max_parallel
        self.index = tasks_by_id()
        self.order = topological_order()
        self.dir = RUNS_DIR / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.started_at = now()
        self.finished_at: datetime | None = None
        self.lock = threading.Lock()
        self.tasks: dict[str, dict] = {}
        reused = reused or set()
        for tid in self.order:
            if tid in reused:
                status = REAPROVEITADA
            elif tid in selected:
                status = AGUARDANDO
            else:
                status = NAO_SELECIONADA
            self.tasks[tid] = {
                "status": status, "tentativas": 0, "inicio": None, "fim": None,
                "duracao_s": None, "codigo_saida": None, "log": (self.dir / f"{tid}.log").as_posix(),
            }

    # ── estado ──────────────────────────────────────────────────────────
    def status(self) -> str:
        values = {info["status"] for info in self.tasks.values()}
        if values & DONE_BAD:
            return "falhou"
        if values <= DONE_OK:
            return "sucesso"
        return "executando"

    def save(self) -> None:
        with self.lock:
            record = {
                "dag_id": DAG_ID,
                "run_id": self.run_id,
                "tipo": self.run_type,
                "params": self.params,
                "inicio": self.started_at.isoformat(),
                "fim": self.finished_at.isoformat() if self.finished_at else None,
                "status": self.status(),
                "tarefas": self.tasks,
            }
            (self.dir / "run.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )

    def set(self, tid: str, **values) -> None:
        with self.lock:
            self.tasks[tid].update(values)
        self.save()

    # ── uma tarefa (executada em uma thread) ────────────────────────────
    def command(self, task: Task) -> list[str]:
        return [sys.executable, "-m", task.module, *(render(arg, self.params) for arg in task.args)]

    def environment(self) -> dict[str, str]:
        env = dict(os.environ)
        # As credenciais do laboratório substituem as do sistema: se o aluno tiver
        # credenciais AWS reais configuradas, elas não podem ser usadas no SeaweedFS.
        env.update(S3_ENV)
        env.update({
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "AURORA_DAG_ID": DAG_ID,
            "AURORA_RUN_ID": self.run_id,
        })
        return env

    def execute(self, tid: str) -> str:
        task = self.index[tid]
        cmd = self.command(task)
        attempts = task.retries + 1
        log_path = self.dir / f"{tid}.log"
        for attempt in range(1, attempts + 1):
            started = now()
            self.set(tid, status=EXECUTANDO, tentativas=attempt, inicio=started.isoformat())
            say(f"[INICIO]  {tid:<24} tentativa {attempt}/{attempts}")
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"=== {tid} | tentativa {attempt}/{attempts} | {started.isoformat()} ===\n")
                log.write("$ " + " ".join(cmd) + "\n\n")
                log.flush()
                try:
                    result = subprocess.run(
                        cmd, stdout=log, stderr=subprocess.STDOUT, env=self.environment(),
                        timeout=task.timeout,
                    )
                    code = result.returncode
                except subprocess.TimeoutExpired:
                    log.write(f"\nTempo limite de {task.timeout}s excedido.\n")
                    code = -1
            finished = now()
            duration = round((finished - started).total_seconds(), 2)
            self.set(tid, fim=finished.isoformat(), duracao_s=duration, codigo_saida=code)
            if code == 0:
                self.set(tid, status=SUCESSO)
                say(f"[OK]      {tid:<24} {duration:>6.1f}s")
                return SUCESSO
            if attempt < attempts:
                self.set(tid, status=NOVA_TENTATIVA)
                say(f"[RETRY]   {tid:<24} falhou (código {code}); nova tentativa em {task.retry_delay}s")
                time.sleep(task.retry_delay)
        self.set(tid, status=FALHOU)
        say(f"[FALHA]   {tid:<24} código {code} após {attempts} tentativa(s)")
        return FALHOU

    # ── o laço do agendador ─────────────────────────────────────────────
    def run(self) -> str:
        self.save()
        say(f"DAG {DAG_ID} | run_id {self.run_id} | params {self.params}")
        pool_use = {name: 0 for name in POOLS}
        running: dict[Future, str] = {}
        try:
            with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                while True:
                    # 1. Propaga falhas: quem depende de tarefa que falhou não executa.
                    for tid in self.order:
                        info = self.tasks[tid]
                        if info["status"] != AGUARDANDO:
                            continue
                        if any(self.tasks[up]["status"] in DONE_BAD for up in self.index[tid].upstream):
                            self.set(tid, status=FALHA_UPSTREAM)
                            say(f"[PULADA]  {tid:<24} dependência falhou (falha_upstream)")

                    # 2. Inicia as tarefas prontas, respeitando paralelismo e pools.
                    for tid in self.order:
                        task = self.index[tid]
                        if self.tasks[tid]["status"] != AGUARDANDO or len(running) >= self.max_parallel:
                            continue
                        if not all(self.tasks[up]["status"] in DONE_OK for up in task.upstream):
                            continue
                        if task.pool and pool_use[task.pool] >= POOLS[task.pool]:
                            continue
                        if task.pool:
                            pool_use[task.pool] += 1
                        self.set(tid, status=EXECUTANDO)
                        running[executor.submit(self.execute, tid)] = tid

                    if not running:
                        break

                    # 3. Espera alguma tarefa terminar.
                    done, _ = wait(running, timeout=0.5, return_when=FIRST_COMPLETED)
                    for future in done:
                        tid = running.pop(future)
                        future.result()
                        pool = self.index[tid].pool
                        if pool:
                            pool_use[pool] -= 1
        except KeyboardInterrupt:
            for tid, info in self.tasks.items():
                if info["status"] in {EXECUTANDO, AGUARDANDO, NOVA_TENTATIVA}:
                    info["status"] = INTERROMPIDA
            say("Execução interrompida pelo usuário.")
        self.finished_at = now()
        self.save()
        return self.status()


# ────────────────────────────────────────────────────────────────────────────
# Relatórios
# ────────────────────────────────────────────────────────────────────────────
def tail(path: Path, lines: int = 12) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


def summarize(run: DagRun) -> None:
    total = (run.finished_at - run.started_at).total_seconds()
    print()
    print(f"{'tarefa':<24} {'estado':<16} {'tentativas':>10} {'duração':>9}")
    print("-" * 62)
    for tid in run.order:
        info = run.tasks[tid]
        duration = f"{info['duracao_s']:.1f}s" if info["duracao_s"] is not None else "-"
        print(f"{tid:<24} {info['status']:<16} {info['tentativas']:>10} {duration:>9}")
    print("-" * 62)
    print(f"Execução {run.run_id}: {run.status().upper()} em {total:.1f}s")
    print(f"Registro: {(run.dir / 'run.json').as_posix()}")

    gate = Path("data/quality/gate.json")
    if run.tasks["gate_qualidade"]["status"] in {SUCESSO, FALHOU} and gate.exists():
        result = json.loads(gate.read_text(encoding="utf-8"))
        alerts = ", ".join(f"{a['alerta']}={a['ocorrencias']}" for a in result["alertas"] if a["ocorrencias"])
        print(f"Gate de qualidade: {result['status']}" + (f" | alertas: {alerts}" if alerts else ""))

    registry = Path("data/models/risco_atraso/registry.json")
    if run.tasks["treinar_modelo_atraso"]["status"] == SUCESSO and registry.exists():
        last = json.loads(registry.read_text(encoding="utf-8"))[-1]
        m = last["metricas"]
        print(f"Modelo risco_atraso: {last['status']} (AUC {m['auc_modelo']} | baseline {m['auc_baseline']})")

    failed = [tid for tid in run.order if run.tasks[tid]["status"] == FALHOU]
    for tid in failed:
        print(f"\nÚltimas linhas do log de {tid}:")
        print(tail(run.dir / f"{tid}.log"))
    if failed:
        print(f"\nCorrija a causa e retome sem repetir o que já deu certo:")
        print(f"  python -m bigdata_pipeline.orchestration.runner --resume {run.run_id}")
        alert = {
            "dag_id": DAG_ID, "run_id": run.run_id, "momento": now().isoformat(),
            "tarefas_com_falha": failed,
            "tarefas_nao_executadas": [t for t in run.order if run.tasks[t]["status"] == FALHA_UPSTREAM],
        }
        with (STATE_DIR / "alerts.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(alert, ensure_ascii=False) + "\n")
        print(f"Alerta registrado em {(STATE_DIR / 'alerts.jsonl').as_posix()}")


def load_runs() -> list[dict]:
    records = []
    for path in RUNS_DIR.glob("*/run.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return sorted(records, key=lambda r: r["inicio"])


def show_history(limit: int) -> None:
    runs = load_runs()[-limit:]
    if not runs:
        print("Nenhuma execução registrada.")
        return
    print(f"{'run_id':<34} {'tipo':<10} {'status':<9} {'duração':>8}  {'tarefas ok':>10}  observação")
    for r in runs:
        start = datetime.fromisoformat(r["inicio"])
        end = datetime.fromisoformat(r["fim"]) if r.get("fim") else None
        duration = f"{(end - start).total_seconds():.0f}s" if end else "-"
        considered = [t for t in r["tarefas"].values() if t["status"] != NAO_SELECIONADA]
        ok = sum(t["status"] in {SUCESSO, REAPROVEITADA} for t in considered)
        failed = [tid for tid, t in r["tarefas"].items() if t["status"] == FALHOU]
        note = f"falhou em {', '.join(failed)}" if failed else ""
        if r.get("params") != PARAMS:
            changed = {k: v for k, v in r.get("params", {}).items() if PARAMS.get(k) != v}
            if changed:
                note = (note + " " if note else "") + f"params {changed}"
        print(f"{r['run_id']:<34} {r['tipo']:<10} {r['status']:<9} {duration:>8}  "
              f"{ok:>5}/{len(considered):<4}  {note}")


def show_graph() -> None:
    index = tasks_by_id()
    print(f"DAG {DAG_ID}  |  agenda: {dag_module.SCHEDULE}  |  {len(TASKS)} tarefas\n")
    for number, level in enumerate(levels(), start=1):
        print(f"Nível {number}:" + ("  (tarefas que podem rodar em paralelo)" if len(level) > 1 else ""))
        for tid in level:
            task = index[tid]
            ups = ", ".join(task.upstream) or "-"
            extras = []
            if task.retries:
                extras.append(f"retries={task.retries}")
            if task.pool:
                extras.append(f"pool={task.pool}")
            print(f"  {tid:<24} depende de: {ups}" + (f"  [{' '.join(extras)}]" if extras else ""))
    print("\nMermaid (cole em https://mermaid.live ou em um .md):\n")
    print(dag_module.to_mermaid())


def show_list(params: dict[str, object]) -> None:
    index = tasks_by_id()
    for tid in topological_order():
        task = index[tid]
        args = " ".join(render(a, params) for a in task.args)
        print(f"{tid:<24} [{task.group}] python -m {task.module} {args}")
        print(f"{'':<24} {task.doc}")


# ────────────────────────────────────────────────────────────────────────────
# Linha de comando
# ────────────────────────────────────────────────────────────────────────────
def parse_params(items: list[str]) -> dict[str, object]:
    params = dict(PARAMS)
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Parâmetro inválido: {item}. Use chave=valor.")
        key, value = item.split("=", 1)
        if key not in PARAMS:
            raise SystemExit(f"Parâmetro desconhecido: {key}. Disponíveis: {', '.join(PARAMS)}")
        default = PARAMS[key]
        if isinstance(default, str):
            params[key] = value
            continue
        try:  # parâmetros numéricos: aceita 2, 2.5 ou 0.65
            number = float(value)
        except ValueError:
            raise SystemExit(f"Valor inválido para {key}: {value}")
        params[key] = int(number) if number.is_integer() else number
    return params


def new_run_id(kind: str) -> str:
    base = f"{kind}__{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    run_id, counter = base, 1
    while (RUNS_DIR / run_id).exists():  # duas execuções no mesmo segundo
        counter += 1
        run_id = f"{base}_{counter}"
    return run_id


def execute_once(args: argparse.Namespace, kind: str) -> str:
    params = parse_params(args.param)
    all_ids = set(tasks_by_id())
    reused: set[str] = set()

    if args.resume:
        runs = load_runs()
        if not runs:
            raise SystemExit("Nenhuma execução anterior para retomar.")
        previous = runs[-1] if args.resume == "last" else next(
            (r for r in runs if r["run_id"] == args.resume), None)
        if previous is None:
            raise SystemExit(f"Execução não encontrada: {args.resume}")
        reused = {tid for tid, t in previous["tarefas"].items() if t["status"] in {SUCESSO, REAPROVEITADA}}
        selected = all_ids - reused
        # Mantém os parâmetros da execução original; --param só altera o que for informado.
        overrides = {k: v for k, v in parse_params(args.param).items() if any(i.startswith(f"{k}=") for i in args.param)}
        params = {**previous.get("params", PARAMS), **overrides}
        say(f"Retomando {previous['run_id']}: {len(reused)} tarefa(s) reaproveitada(s), "
            f"{len(selected)} a executar.")
        kind = "retomada"
    elif args.only:
        selected = {args.only}
        kind = "teste"  # equivalente ao "airflow tasks test"
    elif args.start_at:
        selected = {args.start_at} | downstream_of(args.start_at)
    else:
        selected = all_ids

    run = DagRun(new_run_id(kind), kind, params, selected, reused, args.max_parallel)
    run.run()
    summarize(run)
    return run.status()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Orquestrador local do DAG da Aurora Shop.")
    view = parser.add_mutually_exclusive_group()
    view.add_argument("--graph", action="store_true", help="Mostra o grafo em níveis e em Mermaid.")
    view.add_argument("--list", action="store_true", help="Lista as tarefas e os comandos.")
    view.add_argument("--history", nargs="?", const=10, type=int, metavar="N",
                      help="Mostra as últimas N execuções.")
    view.add_argument("--dry-run", action="store_true", help="Mostra a ordem de execução sem executar.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--start-at", choices=sorted(tasks_by_id()), help="Executa a tarefa e tudo que depende dela.")
    scope.add_argument("--only", choices=sorted(tasks_by_id()), help="Executa uma única tarefa, ignorando dependências.")
    scope.add_argument("--resume", metavar="RUN_ID", help="Reexecuta apenas o que falhou em uma execução ('last' = a última).")
    parser.add_argument("--param", action="append", default=[], metavar="CHAVE=VALOR",
                        help=f"Altera um parâmetro da execução. Disponíveis: {', '.join(PARAMS)}")
    parser.add_argument("--max-parallel", type=int, default=4)
    parser.add_argument("--every", type=int, metavar="SEGUNDOS", help="Agenda execuções periódicas.")
    parser.add_argument("--max-runs", type=int, help="Com --every: encerra após N execuções.")
    args = parser.parse_args()

    if args.graph:
        show_graph()
        return
    if args.list:
        show_list(parse_params(args.param))
        return
    if args.history is not None:
        show_history(args.history)
        return
    if args.dry_run:
        for number, level in enumerate(levels(), start=1):
            print(f"{number:>2}. {' | '.join(level)}")
        return

    with RunLock(STATE_DIR / "runner.lock"):
        if not args.every:
            status = execute_once(args, "manual")
            raise SystemExit(0 if status == "sucesso" else 1)

        executed = 0
        say(f"Agendador iniciado: uma execução a cada {args.every}s. Ctrl+C para parar.")
        try:
            while True:
                tick = time.monotonic()
                execute_once(args, "agendada")
                executed += 1
                if args.max_runs and executed >= args.max_runs:
                    break
                wait_s = max(0, args.every - (time.monotonic() - tick))
                say(f"Próxima execução em {wait_s:.0f}s.")
                time.sleep(wait_s)
        except KeyboardInterrupt:
            say("Agendador encerrado.")


if __name__ == "__main__":
    main()
