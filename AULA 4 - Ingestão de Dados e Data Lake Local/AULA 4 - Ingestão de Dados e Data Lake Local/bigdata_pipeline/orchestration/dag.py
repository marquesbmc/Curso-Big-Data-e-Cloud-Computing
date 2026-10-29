from __future__ import annotations

"""
Definição única do DAG da Aurora Shop.

Este arquivo descreve O QUE precisa ser executado e EM QUE ORDEM.
Ele não executa nada. Dois executores leem esta mesma definição:

    bigdata_pipeline/orchestration/runner.py   orquestrador local (Windows, offline)
    dags/aurora_shop_dag.py                    DAG do Apache Airflow

Por isso, uma mudança de dependência feita aqui vale para os dois.

Grafo
-----

    aguardar_api_entregas ─────────────┐
                                       ▼
    el_sqlite  el_csv  el_json  el_eventos  el_api_entregas
         └────────┴───────┴──────────┴────────────┘
                              ▼
    aguardar_seaweedfs ─▶ sincronizar_landing
                              ▼
                        construir_bronze
                              ▼
                        construir_silver
                              ▼
                        gate_qualidade        ← regra bloqueante + alertas
                              ▼
                        construir_gold
                              ▼
                        validar_warehouse
                       ┌──────┴───────┐
                       ▼              ▼
              publicar_camadas   publicar_warehouse
                       └──────┬───────┘
                              ▼
                     treinar_modelo_atraso   ← gate do modelo
"""

from dataclasses import dataclass, field


DAG_ID = "aurora_shop_pipeline"
DESCRIPTION = "Fontes → Landing → SeaweedFS → Bronze → Silver → Gate → Gold → Validação → Publicação → Modelo"

# Expressão cron: todos os dias às 06:00. O runner local usa --every para simular o agendamento.
SCHEDULE = "0 6 * * *"

# Parâmetros que podem ser alterados a cada execução (no Airflow: "Trigger DAG w/ config").
PARAMS: dict[str, object] = {
    "max_quarantine_pct": 10,
    "min_auc": 0.60,
    "api_url": "http://127.0.0.1:8001",
}

# Pools limitam quantas tarefas de um grupo rodam ao mesmo tempo.
# Os cinco ELs leem e regravam o mesmo data/lake/control/capture_state.json.
# Se rodassem em paralelo, um poderia apagar a watermark gravada pelo outro.
POOLS: dict[str, int] = {"capture_state": 1}

# Variáveis usadas pelo boto3 e pelo SeaweedFS (as mesmas das tasks 50–53 e 91).
S3_ENV: dict[str, str] = {
    "AWS_ACCESS_KEY_ID": "admin",
    "AWS_SECRET_ACCESS_KEY": "bigdata-secret",
    "S3_BUCKET": "curso-bigdata",
    "S3_ENDPOINT_URL": "http://127.0.0.1:8333",
}


@dataclass(frozen=True)
class Task:
    task_id: str
    module: str
    args: tuple[str, ...] = ()
    upstream: tuple[str, ...] = ()
    group: str = ""
    retries: int = 0
    retry_delay: int = 5          # segundos entre tentativas
    timeout: int = 600            # segundos até a tarefa ser interrompida
    pool: str | None = None
    doc: str = ""
    env: dict[str, str] = field(default_factory=dict)


SOURCE = ("--source", "data/source", "--lake", "data/lake")
ELS = ("el_sqlite", "el_csv", "el_json", "el_eventos", "el_api_entregas")

TASKS: list[Task] = [
    # ── Sensores: esperam a infraestrutura ficar disponível ──────────────
    Task("aguardar_seaweedfs", "bigdata_pipeline.orchestration.sensors",
         ("--s3", "--poke-interval", "5", "--timeout", "60"),
         group="sensores", doc="Espera o endpoint S3 do SeaweedFS responder e o bucket existir."),
    Task("aguardar_api_entregas", "bigdata_pipeline.orchestration.sensors",
         ("--http", "{api_url}/health", "--poke-interval", "5", "--timeout", "60"),
         group="sensores", doc="Espera a API da transportadora responder em /health."),

    # ── Ingestão (Aula 4) ────────────────────────────────────────────────
    Task("el_sqlite", "bigdata_pipeline.el.sqlite", SOURCE, group="ingestao",
         retries=1, pool="capture_state", doc="Novos registros do sistema de vendas (watermark por ID)."),
    Task("el_csv", "bigdata_pipeline.el.csv", SOURCE, group="ingestao",
         retries=1, pool="capture_state", doc="Arquivos CSV novos ou alterados (manifest SHA-256)."),
    Task("el_json", "bigdata_pipeline.el.json", SOURCE, group="ingestao",
         retries=1, pool="capture_state", doc="Campanhas de marketing em JSON."),
    Task("el_eventos", "bigdata_pipeline.el.events", SOURCE, group="ingestao",
         retries=1, pool="capture_state", doc="Eventos de navegação em JSON Lines."),
    Task("el_api_entregas", "bigdata_pipeline.el.api", (*SOURCE, "--api-url", "{api_url}"),
         upstream=("aguardar_api_entregas",), group="ingestao",
         retries=2, retry_delay=10, pool="capture_state",
         doc="Entregas paginadas da API (sequência). Rede falha: por isso 2 novas tentativas."),

    # ── Data Lake (Aula 4) ───────────────────────────────────────────────
    Task("sincronizar_landing", "bigdata_pipeline.lake.sync", ("--source", "data/lake/landing"),
         upstream=(*ELS, "aguardar_seaweedfs"), group="lake", retries=2, retry_delay=10,
         doc="Envia ao SeaweedFS somente objetos novos ou alterados (SHA-256)."),

    # ── Transformação (Aula 5) ───────────────────────────────────────────
    Task("construir_bronze", "bigdata_pipeline.transform.pipeline", ("--stage", "bronze"),
         upstream=("sincronizar_landing",), group="transformacao",
         doc="Landing → Parquet com linhagem."),
    Task("construir_silver", "bigdata_pipeline.transform.pipeline", ("--stage", "silver"),
         upstream=("construir_bronze",), group="transformacao",
         doc="Regras de qualidade: Silver + Quarentena + relatório."),
    Task("gate_qualidade", "bigdata_pipeline.transform.quality_gate",
         ("--max-quarantine-pct", "{max_quarantine_pct}"),
         upstream=("construir_silver",), group="transformacao", retries=0,
         doc="Regras bloqueantes e alertas. Sem novas tentativas: repetir não corrige dado ruim."),
    Task("construir_gold", "bigdata_pipeline.transform.pipeline", ("--stage", "gold"),
         upstream=("gate_qualidade",), group="warehouse",
         doc="Dimensões, fatos e marts no aurora.duckdb."),
    Task("validar_warehouse", "bigdata_pipeline.transform.validate", ("--all",),
         upstream=("construir_gold",), group="warehouse", retries=0,
         doc="Reconciliação, grão, chaves duplicadas e chaves órfãs."),

    # ── Publicação ───────────────────────────────────────────────────────
    Task("publicar_camadas", "bigdata_pipeline.transform.publish",
         ("--lake", "data/lake", "--layers", "bronze", "silver", "quarantine"),
         upstream=("validar_warehouse",), group="publicacao", retries=2, retry_delay=10,
         doc="Bronze, Silver e Quarentena no SeaweedFS."),
    Task("publicar_warehouse", "bigdata_pipeline.transform.publish",
         ("--lake", "data", "--layers", "warehouse", "quality"),
         upstream=("validar_warehouse",), group="publicacao", retries=2, retry_delay=10,
         doc="aurora.duckdb, relatório, gate e alertas no SeaweedFS."),

    # ── Produto de dados ─────────────────────────────────────────────────
    Task("treinar_modelo_atraso", "bigdata_pipeline.ml.risco_atraso", ("--min-auc", "{min_auc}"),
         upstream=("publicar_camadas", "publicar_warehouse"), group="produtos",
         doc="Dataset versionado, treino temporal e gate do modelo."),
]


def tasks_by_id() -> dict[str, Task]:
    return {task.task_id: task for task in TASKS}


def downstream_of(task_id: str) -> set[str]:
    """Todas as tarefas que dependem, direta ou indiretamente, de task_id."""

    children: dict[str, set[str]] = {task.task_id: set() for task in TASKS}
    for task in TASKS:
        for parent in task.upstream:
            children[parent].add(task.task_id)
    found: set[str] = set()
    pending = [task_id]
    while pending:
        current = pending.pop()
        for child in children[current]:
            if child not in found:
                found.add(child)
                pending.append(child)
    return found


def topological_order() -> list[str]:
    """Ordena as tarefas respeitando as dependências; falha se houver ciclo."""

    index = tasks_by_id()
    for task in TASKS:
        for parent in task.upstream:
            if parent not in index:
                raise ValueError(f"{task.task_id} depende de tarefa inexistente: {parent}")
    remaining = {task.task_id: set(task.upstream) for task in TASKS}
    order: list[str] = []
    while remaining:
        ready = [tid for tid, ups in remaining.items() if not ups]
        if not ready:
            raise ValueError(f"Ciclo detectado entre: {sorted(remaining)}")
        for tid in ready:  # mantém a ordem de declaração entre tarefas do mesmo nível
            order.append(tid)
            del remaining[tid]
        for ups in remaining.values():
            ups.difference_update(ready)
    return order


def levels() -> list[list[str]]:
    """Agrupa as tarefas em níveis: tarefas do mesmo nível podem rodar em paralelo."""

    index = tasks_by_id()
    depth: dict[str, int] = {}
    for tid in topological_order():
        ups = index[tid].upstream
        depth[tid] = 1 + max((depth[u] for u in ups), default=-1)
    result: list[list[str]] = [[] for _ in range(max(depth.values()) + 1)]
    for tid, d in depth.items():
        result[d].append(tid)
    return result


def render(value: str, params: dict[str, object]) -> str:
    """Substitui {parametro} pelo valor da execução (no Airflow vira {{ params.x }})."""

    return value.format(**{key: str(val) for key, val in params.items()})


def to_mermaid() -> str:
    lines = ["flowchart TD"]
    for task in TASKS:
        lines.append(f"    {task.task_id}[{task.task_id}]")
    for task in TASKS:
        for parent in task.upstream:
            lines.append(f"    {parent} --> {task.task_id}")
    return "\n".join(lines)
