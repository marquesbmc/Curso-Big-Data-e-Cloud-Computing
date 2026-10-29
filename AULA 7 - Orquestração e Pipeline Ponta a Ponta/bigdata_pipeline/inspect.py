from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def human_size(value: int) -> str:
    size = float(value)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def directory_info(path: Path, extensions: set[str] | None = None) -> dict:
    files = [file for file in path.rglob("*") if file.is_file()] if path.exists() else []
    if extensions is not None:
        files = [file for file in files if file.suffix.lower() in extensions]
    return {"files": len(files), "size": human_size(sum(file.stat().st_size for file in files))}


def main() -> None:
    parser = argparse.ArgumentParser(description="Mostra volumes gerados e capturados.")
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    source = args.data / "source"
    db_path = source / "sqlite" / "commerce.db"
    if not db_path.exists():
        db_path = source / "db" / "commerce.db"
    tables = {}
    if db_path.exists():
        connection = sqlite3.connect(db_path)
        for table in ["customers", "suppliers", "products", "orders", "order_items", "payments"]:
            tables[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        connection.close()

    csv_source = source / "csv" if (source / "csv").exists() else source / "files"
    json_source = source / "json" if (source / "json").exists() else source / "files"
    result = {
        "database_rows": tables,
        "source": directory_info(source),
        "source_csv": directory_info(csv_source, {".csv"}),
        "source_json": directory_info(json_source, {".json"}),
        "source_events": directory_info(source / "events"),
        "source_api": directory_info(source / "api"),
        "lake": directory_info(args.data / "lake"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

