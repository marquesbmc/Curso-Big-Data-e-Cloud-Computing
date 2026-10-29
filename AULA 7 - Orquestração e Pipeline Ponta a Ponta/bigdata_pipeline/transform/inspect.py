from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from .pipeline import sql_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspeciona datasets Parquet da Aula 5.")
    parser.add_argument("--layer", required=True, choices=["bronze", "silver", "quarantine"])
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    root = args.lake / args.layer / args.dataset
    files = list(root.rglob("*.parquet"))
    if not files:
        raise SystemExit(f"Dataset não encontrado: {root}")
    pattern = sql_path(root / "**" / "*.parquet")
    con = duckdb.connect()
    result = con.execute(
        f"SELECT * FROM read_parquet('{pattern}', union_by_name=true) LIMIT ?", [args.limit]
    )
    columns = [item[0] for item in result.description]
    rows = result.fetchall()
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join("NULL" if value is None else str(value) for value in row))
    print(f"\n{len(rows)} linha(s) exibida(s) de {root}")
    con.close()


if __name__ == "__main__":
    main()
