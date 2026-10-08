from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from .pipeline import sql_path


def count_parquet(con: duckdb.DuckDBPyConnection, root: Path) -> int:
    return int(con.execute(
        f"SELECT count(*) FROM read_parquet('{sql_path(root / '**' / '*.parquet')}', union_by_name=true)"
    ).fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida as camadas da Aula 5.")
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    parser.add_argument("--warehouse", type=Path, default=Path("data/warehouse/aurora.duckdb"))
    parser.add_argument("--check", choices=["fact-grain"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.warehouse.exists():
        raise SystemExit("Warehouse ausente. Execute a Gold primeiro.")
    con = duckdb.connect(str(args.warehouse), read_only=True)
    rows, distinct_items = con.execute(
        "SELECT count(*), count(DISTINCT item_id) FROM gold.fato_vendas"
    ).fetchone()
    if args.check == "fact-grain":
        print(f"fato_vendas.linhas          = {rows}")
        print(f"fato_vendas.itens_distintos = {distinct_items}")
        print(f"resultado                   = {'OK' if rows == distinct_items else 'FALHA'}")
        raise SystemExit(0 if rows == distinct_items else 1)

    results: list[tuple[str, bool]] = []
    for dataset in ["catalog", "inventory", "events", "shipments"]:
        bronze = count_parquet(con, args.lake / "bronze" / ("csv" if dataset in {"catalog", "inventory"} else "api/shipments" if dataset == "shipments" else dataset))
        if dataset in {"catalog", "inventory"}:
            # Os CSVs dividem o mesmo prefixo; selecionamos pelas colunas características.
            pattern = sql_path(args.lake / "bronze" / "csv" / "**" / "*.parquet")
            marker = "external_name IS NOT NULL" if dataset == "catalog" else "snapshot_date IS NOT NULL"
            bronze = int(con.execute(
                f"SELECT count(*) FROM read_parquet('{pattern}', union_by_name=true) WHERE {marker}"
            ).fetchone()[0])
        silver = count_parquet(con, args.lake / "silver" / dataset)
        quarantine = count_parquet(con, args.lake / "quarantine" / dataset)
        results.append((f"{dataset}: Bronze = Silver + Quarentena", bronze == silver + quarantine))
    duplicate_events = int(con.execute(
        f"SELECT count(*) FROM (SELECT event_id FROM read_parquet('{sql_path(args.lake / 'silver/events/**/*.parquet')}') GROUP BY event_id HAVING count(*) > 1)"
    ).fetchone()[0])
    results.append(("Silver não possui event_id duplicado", duplicate_events == 0))
    results.append(("fato_vendas respeita o grão de item", rows == distinct_items))
    for table, key in [("dim_cliente", "sk_cliente"), ("dim_produto", "sk_produto"), ("dim_data", "sk_data")]:
        total, distinct = con.execute(f"SELECT count(*), count(DISTINCT {key}) FROM gold.{table}").fetchone()
        results.append((f"{table} não possui chaves duplicadas", total == distinct))
    orphan = int(con.execute("""
        SELECT count(*) FROM gold.fato_vendas f
        LEFT JOIN gold.dim_cliente c USING (sk_cliente)
        LEFT JOIN gold.dim_produto p USING (sk_produto)
        LEFT JOIN gold.dim_data d USING (sk_data)
        WHERE c.sk_cliente IS NULL OR p.sk_produto IS NULL OR d.sk_data IS NULL
    """).fetchone()[0])
    results.append(("fato_vendas não possui chaves órfãs", orphan == 0))
    con.close()
    failures = 0
    for label, ok in results:
        print(f"[{'OK' if ok else 'FALHA'}] {label}")
        failures += not ok
    print(f"\n{len(results) - failures} verificações aprovadas; {failures} falha(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
