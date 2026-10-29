from __future__ import annotations

"""
Gate de qualidade da Aurora Shop.

O gate fica entre a Silver e a Gold e responde a uma única pergunta:

    "Os dados desta execução podem seguir para o Data Warehouse?"

Ele aplica dois tipos de regra:

    BLOQUEANTE  interrompe o pipeline (código de saída 1).
                A Gold, as validações, a publicação e o modelo não rodam.

    ALERTA      registra o problema e deixa o pipeline seguir.
                Alguém precisa investigar, mas o dado continua válido.

Regras bloqueantes
------------------
1. percentual de quarentena acima do limite (padrão: 10%);
2. reconciliação: Bronze = Silver + Quarentena;
3. volume mínimo: entidades centrais da Silver não podem estar vazias.

Alertas
-------
1. pedido cancelado com entrega concluída (coerência entre fontes);
2. canal de campanha sem nenhum evento rastreado (lacuna de rastreamento).

Saídas
------
data/quality/gate.json            decisão da execução atual
data/quality/gate_history.jsonl   uma linha por execução (série histórica)
data/quality/alerts/*.csv         registros envolvidos em cada alerta
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from .pipeline import sql_path


DEFAULT_LAKE = Path("data/lake")
DEFAULT_MAX_QUARANTINE_PCT = 10.0

# Onde está cada conjunto de dados avaliado pela Silver.
# Catálogo e inventário dividem o prefixo bronze/csv; a coluna "marcadora"
# separa as linhas de cada um (mesma estratégia do validate.py).
DATASETS = {
    "catalog": {"bronze": "csv", "marker": "external_name IS NOT NULL"},
    "inventory": {"bronze": "csv", "marker": "snapshot_date IS NOT NULL"},
    "events": {"bronze": "events", "marker": None},
    "shipments": {"bronze": "api/shipments", "marker": None},
}

# Entidades sem as quais a Gold não faz sentido.
CORE_ENTITIES = ["customers", "products", "orders", "order_items", "payments", "events"]


def count_rows(con: duckdb.DuckDBPyConnection, folder: Path, where: str | None = None) -> int:
    """Conta as linhas de todos os Parquet de uma pasta; 0 se a pasta não existir."""

    if not folder.is_dir() or not any(folder.rglob("*.parquet")):
        return 0
    pattern = sql_path(folder / "**" / "*.parquet")
    condition = f" WHERE {where}" if where else ""
    return int(con.execute(
        f"SELECT count(*) FROM read_parquet('{pattern}', union_by_name=true){condition}"
    ).fetchone()[0])


def blocking_rules(
    con: duckdb.DuckDBPyConnection,
    lake: Path,
    report: dict,
    max_quarantine_pct: float,
) -> list[dict]:
    """Avalia as regras que podem interromper o pipeline."""

    rules: list[dict] = []

    # 1. Percentual de quarentena por conjunto de dados.
    for dataset, values in report.items():
        percent = float(values["percent"])
        rules.append({
            "regra": "percentual_quarentena",
            "dataset": dataset,
            "valor": percent,
            "limite": f"<= {max_quarantine_pct}%",
            "ok": percent <= max_quarantine_pct,
        })

    # 2. Reconciliação: nada pode sumir nem aparecer entre Bronze e Silver.
    for dataset, spec in DATASETS.items():
        bronze = count_rows(con, lake / "bronze" / spec["bronze"], spec["marker"])
        silver = count_rows(con, lake / "silver" / dataset)
        quarantine = count_rows(con, lake / "quarantine" / dataset)
        rules.append({
            "regra": "reconciliacao",
            "dataset": dataset,
            "valor": f"{bronze} = {silver} + {quarantine}",
            "limite": "Bronze = Silver + Quarentena",
            "ok": bronze == silver + quarantine,
        })

    # 3. Volume mínimo das entidades centrais.
    for entity in CORE_ENTITIES:
        rows = count_rows(con, lake / "silver" / entity)
        rules.append({
            "regra": "volume_minimo",
            "dataset": entity,
            "valor": rows,
            "limite": "> 0",
            "ok": rows > 0,
        })
    return rules


def alerts(con: duckdb.DuckDBPyConnection, lake: Path, alerts_dir: Path) -> list[dict]:
    """Avalia as regras de alerta e grava os registros envolvidos em CSV."""

    alerts_dir.mkdir(parents=True, exist_ok=True)
    found: list[dict] = []
    silver = lake / "silver"

    # Alerta 1: pedido cancelado no sistema de vendas, mas entregue segundo a transportadora.
    orders = silver / "orders"
    shipments = silver / "shipments"
    if orders.is_dir() and shipments.is_dir():
        target = alerts_dir / "pedido_cancelado_com_entrega_concluida.csv"
        query = f"""
            SELECT o.order_id, o.status AS status_pedido, o.updated_at AS pedido_atualizado_em,
                   s.shipment_id, s.carrier AS transportadora, s.status AS status_entrega,
                   s.delivered_at AS entregue_em
            FROM read_parquet('{sql_path(orders / '**' / '*.parquet')}') o
            JOIN read_parquet('{sql_path(shipments / '**' / '*.parquet')}') s USING (order_id)
            WHERE o.status = 'cancelled' AND s.status = 'delivered'
            ORDER BY o.order_id
        """
        total = int(con.execute(f"SELECT count(*) FROM ({query})").fetchone()[0])
        con.execute(f"COPY ({query}) TO '{sql_path(target)}' (HEADER, DELIMITER ',')")
        found.append({
            "alerta": "pedido_cancelado_com_entrega_concluida",
            "dimensao": "coerencia entre fontes",
            "ocorrencias": total,
            "arquivo": target.as_posix(),
            "acao": "Investigar com Comercial e Logística: estorno indevido ou entrega não cancelada?",
        })

    # Alerta 2: canal usado por campanha que nunca aparece nos eventos do site.
    campaigns = silver / "campaigns"
    events = silver / "events"
    if campaigns.is_dir() and events.is_dir():
        target = alerts_dir / "campanha_sem_rastreamento.csv"
        query = f"""
            SELECT c.campaign_id, c.name AS campanha, c.channel AS canal
            FROM read_parquet('{sql_path(campaigns / '**' / '*.parquet')}') c
            WHERE lower(c.channel) NOT IN (
                SELECT DISTINCT lower(source)
                FROM read_parquet('{sql_path(events / '**' / '*.parquet')}')
                WHERE source IS NOT NULL
            )
            ORDER BY c.campaign_id
        """
        total = int(con.execute(f"SELECT count(*) FROM ({query})").fetchone()[0])
        con.execute(f"COPY ({query}) TO '{sql_path(target)}' (HEADER, DELIMITER ',')")
        found.append({
            "alerta": "campanha_sem_rastreamento",
            "dimensao": "completude do rastreamento",
            "ocorrencias": total,
            "arquivo": target.as_posix(),
            "acao": "Pedir ao Marketing/Site a instrumentação do canal (UTM source).",
        })
    return found


def run_gate(lake: Path, max_quarantine_pct: float) -> dict:
    report_path = lake.parent / "quality" / "report.json"
    if not report_path.exists():
        raise SystemExit("Relatório de qualidade ausente. Execute a Silver antes do gate.")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    con = duckdb.connect()
    rules = blocking_rules(con, lake, report, max_quarantine_pct)
    found_alerts = alerts(con, lake, lake.parent / "quality" / "alerts")
    con.close()

    failed = [rule for rule in rules if not rule["ok"]]
    return {
        "run_id": os.getenv("AURORA_RUN_ID", "manual"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "max_quarantine_pct": max_quarantine_pct,
        "status": "aprovado" if not failed else "bloqueado",
        "regras": rules,
        "alertas": found_alerts,
    }


def print_result(result: dict) -> None:
    print("GATE DE QUALIDADE")
    print(f"limite de quarentena: {result['max_quarantine_pct']}%\n")
    print(f"{'resultado':<10} {'regra':<22} {'dataset':<12} {'valor':<28} limite")
    for rule in result["regras"]:
        status = "OK" if rule["ok"] else "BLOQUEIO"
        print(f"{status:<10} {rule['regra']:<22} {rule['dataset']:<12} {str(rule['valor']):<28} {rule['limite']}")
    print()
    for alert in result["alertas"]:
        status = "ALERTA" if alert["ocorrencias"] else "OK"
        print(f"{status:<10} {alert['alerta']:<40} ocorrências: {alert['ocorrencias']}")
        if alert["ocorrencias"]:
            print(f"{'':<10} arquivo: {alert['arquivo']}")
            print(f"{'':<10} ação:    {alert['acao']}")
    print()
    if result["status"] == "aprovado":
        print("DECISÃO: APROVADO. A Silver pode seguir para a Gold.")
    else:
        failed = [f"{r['regra']}({r['dataset']})" for r in result["regras"] if not r["ok"]]
        print("DECISÃO: BLOQUEADO. A Gold não será atualizada nesta execução.")
        print("Regras violadas: " + ", ".join(failed))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Gate de qualidade entre a Silver e a Gold.")
    parser.add_argument("--lake", type=Path, default=DEFAULT_LAKE)
    parser.add_argument(
        "--max-quarantine-pct", type=float, default=DEFAULT_MAX_QUARANTINE_PCT,
        help="Percentual máximo de registros em quarentena por conjunto de dados.",
    )
    args = parser.parse_args()

    result = run_gate(args.lake, args.max_quarantine_pct)
    quality_dir = args.lake.parent / "quality"
    (quality_dir / "gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    summary = {
        "run_id": result["run_id"],
        "checked_at": result["checked_at"],
        "status": result["status"],
        "max_quarantine_pct": result["max_quarantine_pct"],
        "quarentena_pct": {r["dataset"]: r["valor"] for r in result["regras"] if r["regra"] == "percentual_quarentena"},
        "alertas": {a["alerta"]: a["ocorrencias"] for a in result["alertas"]},
    }
    with (quality_dir / "gate_history.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")

    print_result(result)
    raise SystemExit(0 if result["status"] == "aprovado" else 1)


if __name__ == "__main__":
    main()
