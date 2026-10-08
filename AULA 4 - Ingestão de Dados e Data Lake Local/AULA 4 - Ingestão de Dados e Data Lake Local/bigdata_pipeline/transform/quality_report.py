from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from .pipeline import sql_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Exibe o relatório de qualidade da Silver.")
    parser.add_argument("--lake", type=Path, default=Path("data/lake"))
    args = parser.parse_args()
    report_path = args.lake.parent / "quality" / "report.json"
    if not report_path.exists():
        raise SystemExit("Relatório ausente. Execute a Silver primeiro.")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    print("Fonte       Lidos     Aprovados   Quarentena   %")
    for name, values in report.items():
        print(f"{name:<12} {values['read']:>8} {values['approved']:>11} {values['quarantine']:>12} {values['percent']:>6.2f}")
    events = args.lake / "quarantine" / "events"
    if events.exists():
        con = duckdb.connect()
        rows = con.execute(f"""
            SELECT reason, count(*) AS occurrences
            FROM (
              SELECT unnest(string_split(motivos, ', ')) AS reason
              FROM read_parquet('{sql_path(events / '**' / '*.parquet')}')
            ) GROUP BY reason ORDER BY occurrences DESC, reason
        """).fetchall()
        print("\nMotivos dos eventos:")
        for reason, count in rows:
            print(f"{reason:<24} {count:>6}")
        con.close()


if __name__ == "__main__":
    main()
