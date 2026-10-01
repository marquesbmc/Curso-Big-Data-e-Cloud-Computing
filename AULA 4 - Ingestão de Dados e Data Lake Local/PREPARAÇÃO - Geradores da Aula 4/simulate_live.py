from __future__ import annotations

import argparse
import json
import random
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simula novas operações e eventos em tempo real.")
    parser.add_argument("--source", type=Path, default=Path("data/source"))
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--orders-per-batch", type=int, default=20)
    parser.add_argument("--events-per-order", type=int, default=8)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=3030)
    parser.add_argument("--forever", action="store_true")
    return parser.parse_args()


def next_id(connection: sqlite3.Connection, table: str, column: str) -> int:
    maximum = connection.execute(f"SELECT COALESCE(MAX({column}), 0) FROM {table}").fetchone()[0]
    return int(maximum) + 1


def append_jsonl(path: Path, documents: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", buffering=1024 * 1024) as stream:
        for document in documents:
            stream.write(json.dumps(document, ensure_ascii=False) + "\n")


def simulate_batch(
    connection: sqlite3.Connection,
    source: Path,
    rng: random.Random,
    orders_per_batch: int,
    events_per_order: int,
) -> dict:
    customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    products = dict(connection.execute("SELECT product_id, price_cents FROM products"))
    if not customer_count or not products:
        raise SystemExit("Banco sem clientes ou produtos. Execute generate.py primeiro.")

    order_id = next_id(connection, "orders", "order_id")
    item_id = next_id(connection, "order_items", "item_id")
    payment_id = next_id(connection, "payments", "payment_id")
    event_documents: list[dict] = []
    shipment_documents: list[dict] = []
    product_ids = list(products)

    for offset in range(orders_per_batch):
        current_order_id = order_id + offset
        customer_id = rng.randint(1, customer_count)
        created = datetime.now(timezone.utc)
        status = rng.choice(["paid", "paid", "paid", "shipped"])
        item_count = rng.randint(1, 4)
        total = 0
        current_items: list[tuple] = []

        for _ in range(item_count):
            product_id = rng.choice(product_ids)
            quantity = rng.randint(1, 3)
            unit_price = int(products[product_id])
            total += quantity * unit_price
            current_items.append(
                (item_id, current_order_id, product_id, quantity, unit_price, created.isoformat())
            )
            item_id += 1

        connection.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                current_order_id,
                customer_id,
                status,
                rng.choice(["web", "mobile", "store"]),
                total,
                created.isoformat(),
                created.isoformat(),
            ),
        )
        connection.executemany(
            "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
            current_items,
        )
        connection.execute(
            "INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                payment_id,
                current_order_id,
                rng.choice(["credit_card", "pix", "debit_card"]),
                "approved",
                total,
                created.isoformat(),
                created.isoformat(),
            ),
        )
        payment_id += 1

        session_id = f"live-session-{uuid.uuid4()}"
        for event_index in range(events_per_order):
            event_type = "purchase" if event_index == events_per_order - 1 else rng.choice(
                ["product_view", "search", "add_to_cart", "checkout_start"]
            )
            event_documents.append(
                {
                    "event_id": f"live-event-{uuid.uuid4()}",
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "product_id": rng.choice(product_ids),
                    "order_id": current_order_id if event_type == "purchase" else None,
                    "event_type": event_type,
                    "event_at": (created + timedelta(seconds=event_index)).isoformat(),
                    "device": rng.choice(["mobile", "desktop", "tablet"]),
                    "source": rng.choice(["organic", "email", "social", "direct"]),
                }
            )

        promised = created + timedelta(days=rng.randint(1, 10))
        shipment_documents.append(
            {
                "shipment_id": f"ship-{current_order_id:012d}",
                "source_sequence": current_order_id,
                "order_id": current_order_id,
                "carrier": rng.choice(["Rápido Sul", "Entrega Brasil", "Log Norte", "Expresso Rio"]),
                "created_at": created.isoformat(),
                "promised_at": promised.isoformat(),
                "delivered_at": None,
                "status": "created",
            }
        )

    connection.commit()
    day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    append_jsonl(source / "events" / f"events_live_{day_key}.jsonl", event_documents)
    append_jsonl(source / "api" / "shipments.jsonl", shipment_documents)
    return {
        "orders": orders_per_batch,
        "events": len(event_documents),
        "shipments": len(shipment_documents),
        "first_order_id": order_id,
        "last_order_id": order_id + orders_per_batch - 1,
    }


def main() -> None:
    args = parse_args()
    if args.batches < 1 or args.orders_per_batch < 1 or args.events_per_order < 1:
        raise SystemExit("Os parâmetros de volume devem ser maiores que zero.")
    db_path = args.source / "sqlite" / "commerce.db"
    if not db_path.exists():
        raise SystemExit(f"Banco não encontrado: {db_path}. Execute generate.py primeiro.")

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    rng = random.Random(args.seed)
    batch_number = 0
    try:
        while args.forever or batch_number < args.batches:
            batch_number += 1
            result = simulate_batch(
                connection,
                args.source,
                rng,
                args.orders_per_batch,
                args.events_per_order,
            )
            print(json.dumps({"batch": batch_number, **result}, ensure_ascii=False))
            if args.forever or batch_number < args.batches:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Simulação interrompida pelo usuário.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
