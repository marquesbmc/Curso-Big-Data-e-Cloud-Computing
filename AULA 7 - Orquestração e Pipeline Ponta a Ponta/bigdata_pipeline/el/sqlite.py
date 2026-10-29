from __future__ import annotations

import json
import sqlite3

from .common import CaptureRun, run_single_capture


TABLE_KEYS = {
    "customers": "customer_id",
    "suppliers": "supplier_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "item_id",
    "payments": "payment_id",
}


def capture(run: CaptureRun) -> dict[str, int]:
    db_path = run.source / "sqlite" / "commerce.db"
    if not db_path.exists():
        db_path = run.source / "db" / "commerce.db"
    if not db_path.exists():
        raise SystemExit(f"Banco SQLite não encontrado: {db_path}")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    database_state = run.state.setdefault("database_watermarks", {})
    result = {}
    try:
        for table, key in TABLE_KEYS.items():
            watermark = int(database_state.get(table, 0))
            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {key} > ? ORDER BY {key}",
                (watermark,),
            )
            output_dir = run.landing / "sqlite" / table
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{table}_{run.run_id}.jsonl"
            count = 0
            maximum = watermark
            with output_path.open("w", encoding="utf-8") as stream:
                for row in rows:
                    document = dict(row)
                    stream.write(json.dumps(document, ensure_ascii=False) + "\n")
                    maximum = max(maximum, int(document[key]))
                    count += 1
            if count == 0:
                output_path.unlink()
            else:
                database_state[table] = maximum
            result[table] = count
    finally:
        connection.close()
    return result


def main() -> None:
    run_single_capture("sqlite", capture, "Captura incremental das tabelas SQLite.")


if __name__ == "__main__":
    main()