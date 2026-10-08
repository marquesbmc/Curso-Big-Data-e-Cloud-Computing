from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb


DEFAULT_SOURCE = Path("data/lake/landing")
DEFAULT_LAKE = Path("data/lake")
DEFAULT_WAREHOUSE = Path("data/warehouse/aurora.duckdb")


def sql_path(path: Path | str) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def parquet_glob(root: Path, relative: str) -> str:
    return sql_path(root / relative / "**" / "*.parquet")


def copy_query(con: duckdb.DuckDBPyConnection, query: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    con.execute(
        f"COPY ({query}) TO '{sql_path(target)}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD)"
    )


def read_expr(path: Path) -> str:
    p = sql_path(path)
    if path.suffix.lower() == ".csv":
        return f"read_csv('{p}', header=true, all_varchar=true)"
    if path.suffix.lower() in {".json", ".jsonl"}:
        return f"read_json_auto('{p}')"
    raise ValueError(f"Formato não suportado: {path}")


def bronze(source: Path, lake: Path) -> dict[str, object]:
    if not source.is_dir():
        raise SystemExit(f"Landing não encontrada: {source}")
    target_root = lake / "bronze"
    con = duckdb.connect()
    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".json", ".jsonl"}
    )
    ingested_at = datetime.now(timezone.utc).isoformat()
    rows = 0
    for path in files:
        relative = path.relative_to(source)
        target = (target_root / relative).with_suffix(".parquet")
        source_file = relative.as_posix().replace("'", "''")
        query = (
            "SELECT *, "
            f"'{source_file}' AS _source_file, "
            f"TIMESTAMPTZ '{ingested_at}' AS _ingested_at "
            f"FROM {read_expr(path)}"
        )
        rows += int(con.execute(f"SELECT count(*) FROM ({query})").fetchone()[0])
        copy_query(con, query, target)
    con.close()
    return {
        "stage": "bronze",
        "source_files": len(files),
        "written_files": len(files),
        "rows": rows,
        "target": str(target_root),
        "status": "success",
    }


def create_latest_table(
    con: duckdb.DuckDBPyConnection,
    name: str,
    source_glob: str,
    key: str,
    order_column: str | None = None,
) -> None:
    order = f"{order_column} DESC, _ingested_at DESC" if order_column else "_ingested_at DESC"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {name} AS
        SELECT * FROM read_parquet('{source_glob}', union_by_name=true)
        QUALIFY row_number() OVER (PARTITION BY {key} ORDER BY {order}) = 1
        """
    )


def export_table(con: duckdb.DuckDBPyConnection, table: str, target: Path) -> None:
    copy_query(con, f"SELECT * FROM {table}", target)


def silver(lake: Path) -> dict[str, object]:
    bronze_root = lake / "bronze"
    if not bronze_root.is_dir():
        raise SystemExit("Bronze não encontrada. Execute --stage bronze primeiro.")
    silver_root = lake / "silver"
    quarantine_root = lake / "quarantine"
    con = duckdb.connect()

    specs = {
        "customers": ("customer_id", "updated_at"),
        "suppliers": ("supplier_id", None),
        "products": ("product_id", "updated_at"),
        "orders": ("order_id", "updated_at"),
        "order_items": ("item_id", None),
        "payments": ("payment_id", "updated_at"),
    }
    for dataset, (key, updated_at) in specs.items():
        create_latest_table(
            con,
            f"stg_{dataset}",
            parquet_glob(bronze_root, f"sqlite/{dataset}"),
            key,
            updated_at,
        )

    con.execute("""
        CREATE OR REPLACE TABLE customers AS
        SELECT customer_id, trim(name) AS name, lower(trim(email)) AS email,
               upper(trim(state)) AS state, try_cast(created_at AS TIMESTAMPTZ) AS created_at,
               try_cast(updated_at AS TIMESTAMPTZ) AS updated_at, _source_file, _ingested_at
        FROM stg_customers
    """)
    con.execute("""
        CREATE OR REPLACE TABLE suppliers AS
        SELECT supplier_id, trim(name) AS name, upper(trim(state)) AS state,
               try_cast(created_at AS TIMESTAMPTZ) AS created_at, _source_file, _ingested_at
        FROM stg_suppliers
    """)
    con.execute("""
        CREATE OR REPLACE TABLE products AS
        SELECT product_id, supplier_id, trim(sku) AS sku, trim(name) AS name,
               trim(category) AS category,
               CAST(price_cents / 100.0 AS DECIMAL(12,2)) AS price,
               stock_quantity, try_cast(created_at AS TIMESTAMPTZ) AS created_at,
               try_cast(updated_at AS TIMESTAMPTZ) AS updated_at, _source_file, _ingested_at
        FROM stg_products
    """)
    con.execute("""
        CREATE OR REPLACE TABLE orders AS
        SELECT order_id, customer_id, lower(trim(status)) AS status,
               lower(trim(channel)) AS channel,
               CAST(total_cents / 100.0 AS DECIMAL(12,2)) AS total,
               try_cast(created_at AS TIMESTAMPTZ) AS created_at,
               try_cast(updated_at AS TIMESTAMPTZ) AS updated_at, _source_file, _ingested_at
        FROM stg_orders
    """)
    con.execute("""
        CREATE OR REPLACE TABLE order_items AS
        SELECT item_id, order_id, product_id, quantity,
               CAST(unit_price_cents / 100.0 AS DECIMAL(12,2)) AS unit_price,
               try_cast(created_at AS TIMESTAMPTZ) AS created_at, _source_file, _ingested_at
        FROM stg_order_items
    """)
    con.execute("""
        CREATE OR REPLACE TABLE payments AS
        SELECT payment_id, order_id, lower(trim(method)) AS method,
               lower(trim(status)) AS status,
               CAST(amount_cents / 100.0 AS DECIMAL(12,2)) AS amount,
               try_cast(created_at AS TIMESTAMPTZ) AS created_at,
               try_cast(updated_at AS TIMESTAMPTZ) AS updated_at, _source_file, _ingested_at
        FROM stg_payments
    """)

    categories = [
        "Alimentos", "Beleza", "Brinquedos", "Casa", "Eletrônicos", "Esporte",
        "Jardim", "Livros", "Moda", "Papelaria", "Pet", "Tecnologia",
    ]
    values = ",".join(f"('{c}')" for c in categories)
    con.execute(f"CREATE OR REPLACE TABLE domain_category AS SELECT * FROM (VALUES {values}) t(category)")
    catalog_glob = parquet_glob(bronze_root, "csv")
    con.execute(f"""
        CREATE OR REPLACE TABLE chk_catalog AS
        WITH base AS (
            SELECT *, row_number() OVER (PARTITION BY try_cast(product_id AS INTEGER)
                                         ORDER BY _source_file) AS occurrence
            FROM read_parquet('{catalog_glob}', union_by_name=true)
            WHERE product_id IS NOT NULL AND external_name IS NOT NULL
        ), normalized AS (
            SELECT b.*, d.category AS normalized_category,
                   try_cast(regexp_extract(supplier_code, '[0-9]+') AS INTEGER) AS supplier_id_value
            FROM base b LEFT JOIN domain_category d
              ON lower(d.category) = lower(trim(replace(b.category, '0', 'o')))
        )
        SELECT n.*,
               concat_ws(', ',
                 CASE WHEN occurrence > 1 THEN 'duplicado' END,
                 CASE WHEN try_cast(weight_kg AS DECIMAL(12,3)) IS NULL THEN 'peso_ausente' END,
                 CASE WHEN s.supplier_id IS NULL THEN 'fornecedor_inexistente' END,
                 CASE WHEN normalized_category IS NULL THEN 'categoria_invalida' END
               ) AS motivos
        FROM normalized n LEFT JOIN suppliers s ON s.supplier_id = n.supplier_id_value
    """)
    con.execute("""
        CREATE OR REPLACE TABLE catalog AS
        SELECT try_cast(product_id AS INTEGER) AS product_id, trim(external_name) AS external_name,
               normalized_category AS category, supplier_id_value AS supplier_id,
               try_cast(weight_kg AS DECIMAL(12,3)) AS weight_kg, _source_file, _ingested_at
        FROM chk_catalog WHERE motivos = ''
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE chk_inventory AS
        SELECT *, CASE WHEN try_cast(quantity AS INTEGER) < 0 THEN 'estoque_negativo'
                       WHEN try_cast(quantity AS INTEGER) IS NULL THEN 'quantidade_invalida'
                       ELSE '' END AS motivos
        FROM read_parquet('{catalog_glob}', union_by_name=true)
        WHERE snapshot_date IS NOT NULL
    """)
    con.execute("""
        CREATE OR REPLACE TABLE inventory AS
        SELECT try_cast(product_id AS INTEGER) AS product_id,
               try_cast(quantity AS INTEGER) AS quantity,
               try_cast(snapshot_date AS DATE) AS snapshot_date, trim(warehouse) AS warehouse,
               _source_file, _ingested_at FROM chk_inventory WHERE motivos = ''
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE chk_events AS
        WITH base AS (
          SELECT *, row_number() OVER (PARTITION BY event_id ORDER BY _source_file) AS occurrence
          FROM read_parquet('{parquet_glob(bronze_root, 'events')}', union_by_name=true)
        )
        SELECT b.*,
          concat_ws(', ',
            CASE WHEN occurrence > 1 THEN 'duplicado' END,
            CASE WHEN event_type IS NULL OR trim(event_type) = '' THEN 'tipo_ausente' END,
            CASE WHEN try_cast(event_at AS TIMESTAMPTZ) IS NULL THEN 'data_invalida' END,
            CASE WHEN device IS NULL OR trim(device) = '' THEN 'dispositivo_ausente' END,
            CASE WHEN c.customer_id IS NULL THEN 'cliente_inexistente' END,
            CASE WHEN b.product_id IS NOT NULL AND p.product_id IS NULL THEN 'produto_inexistente' END
          ) AS motivos
        FROM base b
        LEFT JOIN customers c ON c.customer_id = b.customer_id
        LEFT JOIN products p ON p.product_id = b.product_id
    """)
    con.execute("""
        CREATE OR REPLACE TABLE events AS
        SELECT event_id, session_id, customer_id, product_id, order_id,
               lower(trim(event_type)) AS event_type,
               try_cast(event_at AS TIMESTAMPTZ) AS event_at,
               lower(trim(device)) AS device, lower(trim(source)) AS source,
               _source_file, _ingested_at
        FROM chk_events WHERE motivos = ''
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE chk_shipments AS
        SELECT s.*,
          concat_ws(', ',
            CASE WHEN lower(trim(s.status)) = 'delivered' AND s.delivered_at IS NULL THEN 'entrega_sem_data' END,
            CASE WHEN o.order_id IS NULL THEN 'pedido_inexistente' END,
            CASE WHEN lower(trim(s.status)) NOT IN ('created','in_transit','delivered','cancelled')
                 THEN 'status_invalido' END
          ) AS motivos
        FROM read_parquet('{parquet_glob(bronze_root, 'api/shipments')}', union_by_name=true) s
        LEFT JOIN orders o ON o.order_id = s.order_id
    """)
    con.execute("""
        CREATE OR REPLACE TABLE shipments AS
        SELECT shipment_id, source_sequence, order_id, trim(carrier) AS carrier,
               try_cast(created_at AS TIMESTAMPTZ) AS created_at,
               try_cast(promised_at AS TIMESTAMPTZ) AS promised_at,
               try_cast(delivered_at AS TIMESTAMPTZ) AS delivered_at,
               lower(trim(status)) AS status, _source_file, _ingested_at
        FROM chk_shipments WHERE motivos = ''
    """)

    campaign_files = list((bronze_root / "json").rglob("*.parquet"))
    if campaign_files:
        create_latest_table(con, "campaigns", parquet_glob(bronze_root, "json"), "campaign_id")

    for table in [*specs, "catalog", "inventory", "events", "shipments"]:
        export_table(con, table, silver_root / table / f"{table}.parquet")
    if campaign_files:
        export_table(con, "campaigns", silver_root / "campaigns" / "campaigns.parquet")

    checks = {
        "catalog": "chk_catalog",
        "inventory": "chk_inventory",
        "events": "chk_events",
        "shipments": "chk_shipments",
    }
    report: dict[str, dict[str, float | int]] = {}
    for dataset, table in checks.items():
        read = int(con.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        rejected = int(con.execute(f"SELECT count(*) FROM {table} WHERE motivos <> ''").fetchone()[0])
        approved = read - rejected
        report[dataset] = {
            "read": read,
            "approved": approved,
            "quarantine": rejected,
            "percent": round((rejected / read * 100) if read else 0, 2),
        }
        copy_query(
            con,
            f"SELECT *, current_timestamp AS quarantined_at FROM {table} WHERE motivos <> ''",
            quarantine_root / dataset / f"{dataset}.parquet",
        )
    quality_dir = lake.parent / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    con.close()
    return {"stage": "silver", "datasets": report, "status": "success"}


def gold(lake: Path, warehouse: Path) -> dict[str, object]:
    silver_root = lake / "silver"
    if not silver_root.is_dir():
        raise SystemExit("Silver não encontrada. Execute --stage silver primeiro.")
    warehouse.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(warehouse))
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    for dataset in ["customers", "suppliers", "products", "orders", "order_items", "payments", "catalog", "events", "shipments"]:
        con.execute(
            f"CREATE OR REPLACE TEMP VIEW {dataset} AS SELECT * FROM read_parquet("
            f"'{parquet_glob(silver_root, dataset)}', union_by_name=true)"
        )
    con.execute("""
        CREATE OR REPLACE TABLE gold.dim_cliente AS
        SELECT row_number() OVER (ORDER BY customer_id) AS sk_cliente,
               customer_id, name AS nome, state AS uf, CAST(created_at AS DATE) AS cliente_desde
        FROM customers
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold.dim_produto AS
        SELECT row_number() OVER (ORDER BY p.product_id) AS sk_produto,
               p.product_id, p.sku, p.name AS nome, p.category AS categoria,
               p.price AS preco_atual, c.weight_kg AS peso_kg,
               s.name AS fornecedor, s.state AS uf_fornecedor
        FROM products p LEFT JOIN catalog c USING (product_id)
        LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold.dim_data AS
        WITH dates AS (
          SELECT CAST(created_at AS DATE) AS data FROM orders
          UNION SELECT CAST(event_at AS DATE) FROM events
          UNION SELECT CAST(created_at AS DATE) FROM shipments
        )
        SELECT CAST(strftime(data, '%Y%m%d') AS INTEGER) AS sk_data, data,
               year(data) AS ano, month(data) AS mes, day(data) AS dia,
               dayofweek(data) AS dia_semana, dayofweek(data) IN (0,6) AS fim_de_semana
        FROM dates WHERE data IS NOT NULL
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold.fato_vendas AS
        SELECT i.item_id, o.order_id, CAST(strftime(CAST(o.created_at AS DATE), '%Y%m%d') AS INTEGER) AS sk_data,
               c.sk_cliente, p.sk_produto, o.channel AS canal, o.status AS status_pedido,
               pay.status AS status_pagamento, pay.method AS metodo_pagamento,
               i.quantity AS quantidade, i.unit_price AS preco_unitario,
               CAST(i.quantity * i.unit_price AS DECIMAL(14,2)) AS valor_bruto
        FROM order_items i JOIN orders o USING (order_id)
        JOIN gold.dim_cliente c ON c.customer_id = o.customer_id
        JOIN gold.dim_produto p ON p.product_id = i.product_id
        LEFT JOIN payments pay ON pay.order_id = o.order_id
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold.fato_eventos AS
        SELECT e.event_id, e.session_id,
               CAST(strftime(CAST(e.event_at AS DATE), '%Y%m%d') AS INTEGER) AS sk_data,
               c.sk_cliente, p.sk_produto, e.order_id, e.event_type, e.device, e.source
        FROM events e JOIN gold.dim_cliente c ON c.customer_id = e.customer_id
        LEFT JOIN gold.dim_produto p ON p.product_id = e.product_id
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold.fato_entregas AS
        SELECT s.shipment_id, s.order_id,
               CAST(strftime(CAST(s.created_at AS DATE), '%Y%m%d') AS INTEGER) AS sk_data,
               s.carrier AS transportadora, s.status,
               date_diff('day', CAST(s.promised_at AS DATE), CAST(s.delivered_at AS DATE)) AS dias_atraso,
               s.delivered_at IS NOT NULL AND s.delivered_at <= s.promised_at AS entregue_no_prazo
        FROM shipments s
    """)
    con.execute("""
        CREATE OR REPLACE VIEW gold.mart_receita_categoria_dia AS
        SELECT d.data, p.categoria, count(DISTINCT f.order_id) AS pedidos,
               sum(f.quantidade) AS itens, sum(f.valor_bruto) AS receita
        FROM gold.fato_vendas f JOIN gold.dim_data d USING (sk_data)
        JOIN gold.dim_produto p USING (sk_produto)
        WHERE f.status_pedido <> 'cancelled' AND f.status_pagamento = 'approved'
        GROUP BY ALL
    """)
    con.execute("""
        CREATE OR REPLACE VIEW gold.mart_funil_origem AS
        SELECT source AS origem, count(DISTINCT session_id) AS sessoes,
          count(DISTINCT CASE WHEN event_type='page_view' THEN session_id END) AS page_view,
          count(DISTINCT CASE WHEN event_type='view_product' THEN session_id END) AS view_product,
          count(DISTINCT CASE WHEN event_type='add_to_cart' THEN session_id END) AS add_to_cart,
          count(DISTINCT CASE WHEN event_type='checkout' THEN session_id END) AS checkout,
          count(DISTINCT CASE WHEN event_type='purchase' THEN session_id END) AS purchase
        FROM gold.fato_eventos GROUP BY source
    """)
    con.execute("""
        CREATE OR REPLACE VIEW gold.mart_entregas_transportadora AS
        SELECT transportadora, count(*) AS entregas,
               count_if(entregue_no_prazo) AS no_prazo,
               round(100.0 * count_if(entregue_no_prazo) / nullif(count_if(status='delivered'),0), 2) AS percentual_no_prazo,
               round(avg(dias_atraso) FILTER (WHERE status='delivered'), 2) AS atraso_medio,
               count_if(status <> 'delivered') AS nao_concluidas
        FROM gold.fato_entregas GROUP BY transportadora
    """)
    con.execute("""
        CREATE OR REPLACE VIEW gold.mart_campanhas AS
        SELECT source AS canal, count(DISTINCT session_id) AS sessoes,
               count(DISTINCT CASE WHEN event_type='purchase' THEN order_id END) AS compras
        FROM gold.fato_eventos GROUP BY source
    """)
    counts = {
        name: int(con.execute(f"SELECT count(*) FROM gold.{name}").fetchone()[0])
        for name in ["dim_data", "dim_cliente", "dim_produto", "fato_vendas", "fato_eventos", "fato_entregas"]
    }
    con.close()
    return {"stage": "gold", "warehouse": str(warehouse), "tables": counts, "status": "success"}


def check(source: Path) -> dict[str, object]:
    files = list(source.rglob("*")) if source.exists() else []
    return {
        "landing": str(source),
        "landing_files": sum(path.is_file() for path in files),
        "duckdb": duckdb.__version__,
        "status": "ok" if source.is_dir() else "missing",
    }


def reset(lake: Path, warehouse: Path) -> dict[str, object]:
    removed: list[str] = []
    for path in [lake / "bronze", lake / "silver", lake / "quarantine", lake.parent / "quality"]:
        if path.exists():
            shutil.rmtree(path)
            removed.append(str(path))
    if warehouse.exists():
        warehouse.unlink()
        removed.append(str(warehouse))
    return {"removed": removed, "landing_preserved": str(lake / "landing")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline Bronze, Silver e Gold da Aula 5.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--lake", type=Path, default=DEFAULT_LAKE)
    parser.add_argument("--warehouse", type=Path, default=DEFAULT_WAREHOUSE)
    parser.add_argument("--stage", choices=["bronze", "silver", "gold"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        result: object = check(args.source)
    elif args.reset:
        result = reset(args.lake, args.warehouse)
    elif args.all:
        result = [bronze(args.source, args.lake), silver(args.lake), gold(args.lake, args.warehouse)]
    elif args.stage == "bronze":
        result = bronze(args.source, args.lake)
    elif args.stage == "silver":
        result = silver(args.lake)
    elif args.stage == "gold":
        result = gold(args.lake, args.warehouse)
    else:
        raise SystemExit("Informe --check, --stage, --all ou --reset.")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
