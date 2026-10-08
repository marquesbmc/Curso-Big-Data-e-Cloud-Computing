from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from .pipeline import sql_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Exibe a linhagem de um item vendido.")
    parser.add_argument("--item-id", type=int, required=True)
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    parser.add_argument("--warehouse", type=Path, default=Path("data/warehouse/aurora.duckdb"))
    args = parser.parse_args()
    con = duckdb.connect(str(args.warehouse), read_only=True)
    source = con.execute(
        f"SELECT _source_file FROM read_parquet('{sql_path(args.lake / 'silver/order_items/**/*.parquet')}') WHERE item_id = ?",
        [args.item_id],
    ).fetchone()
    fact = con.execute(
        "SELECT order_id, sk_data, sk_cliente, sk_produto, valor_bruto FROM gold.fato_vendas WHERE item_id = ?",
        [args.item_id],
    ).fetchone()
    if not source or not fact:
        raise SystemExit(f"item_id {args.item_id} não encontrado.")
    print(f"Landing  : {source[0]}")
    print(f"Bronze   : {Path(source[0]).with_suffix('.parquet').as_posix()}")
    print("Silver   : silver/order_items/order_items.parquet")
    print(f"Gold     : fato_vendas[item_id={args.item_id}] -> {fact}")
    print("Mart     : gold.mart_receita_categoria_dia")
    con.close()


if __name__ == "__main__":
    main()
