from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


QUERIES = {
    "receita-categoria": """
        SELECT categoria, sum(receita) AS receita, sum(pedidos) AS pedidos
        FROM gold.mart_receita_categoria_dia GROUP BY categoria ORDER BY receita DESC
    """,
    "funil-origem": "SELECT * FROM gold.mart_funil_origem ORDER BY sessoes DESC",
    "entregas-transportadora": "SELECT * FROM gold.mart_entregas_transportadora ORDER BY percentual_no_prazo DESC NULLS LAST",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa consultas de negócio na Gold.")
    parser.add_argument("--name", required=True, choices=sorted(QUERIES))
    parser.add_argument("--warehouse", type=Path, default=Path("data/warehouse/aurora.duckdb"))
    args = parser.parse_args()
    con = duckdb.connect(str(args.warehouse), read_only=True)
    result = con.execute(QUERIES[args.name])
    columns = [item[0] for item in result.description]
    print(" | ".join(columns))
    for row in result.fetchall():
        print(" | ".join(str(value) for value in row))
    if args.name == "receita-categoria":
        approved = con.execute("SELECT sum(receita) FROM gold.mart_receita_categoria_dia").fetchone()[0]
        gross = con.execute("SELECT sum(valor_bruto) FROM gold.fato_vendas").fetchone()[0]
        print(f"\nReceita aprovada: R$ {approved}")
        print(f"Receita bruta:    R$ {gross}")
    con.close()


if __name__ == "__main__":
    main()
