from __future__ import annotations

import argparse
import csv
import json
import random
import sqlite3
import time
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path

from config import PROFILES, Profile
from generator_utils import ensure_empty_or_backup, write_json


FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela",
    "Henrique", "Isabela", "João", "Larissa", "Marcos", "Natália",
    "Otávio", "Paula", "Rafael", "Sofia", "Tiago", "Vitória", "Yasmin",
]
LAST_NAMES = [
    "Almeida", "Barbosa", "Cardoso", "Dias", "Ferreira", "Gomes", "Lima",
    "Martins", "Mendes", "Nascimento", "Oliveira", "Pereira", "Rocha",
    "Santos", "Silva", "Souza", "Teixeira", "Vieira",
]
STATES = ["RJ", "SP", "MG", "ES", "PR", "SC", "RS", "BA", "PE", "GO", "DF"]
CATEGORIES = [
    "Tecnologia", "Casa", "Esporte", "Livros", "Beleza", "Brinquedos",
    "Alimentos", "Papelaria", "Moda", "Eletrônicos", "Jardim", "Pet",
]
EVENT_TYPES = [
    ("product_view", 48),
    ("search", 16),
    ("add_to_cart", 14),
    ("remove_from_cart", 5),
    ("checkout_start", 7),
    ("purchase", 5),
    ("login", 5),
]


def random_datetime(rng: random.Random, start: datetime, end: datetime) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randrange(max(seconds, 1)))


def choose_event_type(rng: random.Random) -> str:
    roll = rng.randint(1, 100)
    total = 0
    for event_type, weight in EVENT_TYPES:
        total += weight
        if roll <= total:
            return event_type
    return EVENT_TYPES[-1][0]


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            supplier_id INTEGER NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            stock_quantity INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            channel TEXT NOT NULL,
            total_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE payments (
            payment_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );

        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_created ON orders(created_at);
        CREATE INDEX idx_items_order ON order_items(order_id);
        CREATE INDEX idx_items_product ON order_items(product_id);
        CREATE INDEX idx_payments_order ON payments(order_id);
        """
    )


def generate_database(
    root: Path,
    profile: Profile,
    rng: random.Random,
    start: datetime,
    end: datetime,
) -> dict[str, int]:
    db_dir = root / "sqlite"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "commerce.db"
    connection = sqlite3.connect(db_path)
    create_schema(connection)

    suppliers = []
    for supplier_id in range(1, profile.suppliers + 1):
        created = random_datetime(rng, start - timedelta(days=365), start)
        suppliers.append(
            (supplier_id, f"Fornecedor {supplier_id:04d}", rng.choice(STATES), created.isoformat())
        )
    connection.executemany(
        "INSERT INTO suppliers VALUES (?, ?, ?, ?)", suppliers
    )

    customers = []
    for customer_id in range(1, profile.customers + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        created = random_datetime(rng, start - timedelta(days=730), end)
        customers.append(
            (
                customer_id,
                f"{first} {last}",
                f"{first}.{last}.{customer_id}@example.test".lower(),
                rng.choice(STATES),
                created.isoformat(),
                created.isoformat(),
            )
        )
        if len(customers) >= 5_000:
            connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)
            customers.clear()
    if customers:
        connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)

    products = []
    prices: list[int] = [0] * (profile.products + 1)
    for product_id in range(1, profile.products + 1):
        created = random_datetime(rng, start - timedelta(days=500), start)
        price = rng.randint(500, 250_000)
        prices[product_id] = price
        products.append(
            (
                product_id,
                rng.randint(1, profile.suppliers),
                f"SKU-{product_id:07d}",
                f"Produto {product_id:07d}",
                rng.choice(CATEGORIES),
                price,
                rng.randint(0, 1_000),
                created.isoformat(),
                created.isoformat(),
            )
        )
        if len(products) >= 5_000:
            connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", products)
            products.clear()
    if products:
        connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", products)

    statuses = ["paid", "paid", "paid", "paid", "shipped", "delivered", "cancelled"]
    channels = ["web", "mobile", "store", "marketplace"]
    methods = ["credit_card", "pix", "debit_card", "bank_slip"]
    order_rows: list[tuple] = []
    item_rows: list[tuple] = []
    payment_rows: list[tuple] = []
    item_id = 0
    payment_id = 0

    for order_id in range(1, profile.orders + 1):
        created = random_datetime(rng, start, end)
        customer_id = rng.randint(1, profile.customers)
        status = rng.choice(statuses)
        item_count = rng.randint(1, 5)
        total = 0
        for _ in range(item_count):
            item_id += 1
            product_id = rng.randint(1, profile.products)
            quantity = rng.randint(1, 4)
            unit_price = prices[product_id]
            total += quantity * unit_price
            item_rows.append(
                (
                    item_id,
                    order_id,
                    product_id,
                    quantity,
                    unit_price,
                    created.isoformat(),
                )
            )

        updated = created + timedelta(minutes=rng.randint(1, 2_880))
        order_rows.append(
            (
                order_id,
                customer_id,
                status,
                rng.choice(channels),
                total,
                created.isoformat(),
                updated.isoformat(),
            )
        )
        payment_id += 1
        payment_status = "refunded" if status == "cancelled" else "approved"
        payment_rows.append(
            (
                payment_id,
                order_id,
                rng.choice(methods),
                payment_status,
                total,
                (created + timedelta(minutes=rng.randint(0, 60))).isoformat(),
                updated.isoformat(),
            )
        )

        if len(order_rows) >= 5_000:
            connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", order_rows)
            connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", item_rows)
            connection.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)", payment_rows)
            connection.commit()
            order_rows.clear()
            item_rows.clear()
            payment_rows.clear()

    if order_rows:
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", order_rows)
        connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", item_rows)
        connection.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)", payment_rows)
    connection.commit()
    connection.close()
    return {
        "customers": profile.customers,
        "suppliers": profile.suppliers,
        "products": profile.products,
        "orders": profile.orders,
        "order_items": item_id,
        "payments": payment_id,
    }


def maybe_corrupt_text(rng: random.Random, value: str, error_rate: float) -> str:
    if rng.random() >= error_rate:
        return value
    options = [value.lower(), value.upper(), f" {value} ", value.replace("o", "0")]
    return rng.choice(options)


def generate_batch_files(
    root: Path,
    profile: Profile,
    rng: random.Random,
    start_day: date,
    end_day: date,
    error_rate: float,
) -> dict[str, int]:
    csv_root = root / "csv"
    csv_root.mkdir(parents=True, exist_ok=True)
    json_root = root / "json"
    json_root.mkdir(parents=True, exist_ok=True)

    catalog_path = csv_root / "catalog.csv"
    with catalog_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["product_id", "external_name", "category", "supplier_code", "weight_kg"],
        )
        writer.writeheader()
        for product_id in range(1, profile.products + 1):
            category = maybe_corrupt_text(rng, rng.choice(CATEGORIES), error_rate)
            supplier = rng.randint(1, profile.suppliers)
            if rng.random() < error_rate / 4:
                supplier = profile.suppliers + rng.randint(1, 20)
            row = {
                "product_id": product_id,
                "external_name": f"Produto externo {product_id:07d}",
                "category": category,
                "supplier_code": f"FORN-{supplier:05d}",
                "weight_kg": round(rng.uniform(0.05, 30.0), 3),
            }
            if rng.random() < error_rate / 5:
                row["weight_kg"] = ""
            writer.writerow(row)
            if rng.random() < error_rate / 10:
                writer.writerow(row)

    snapshot_count = 0
    current = start_day
    while current <= end_day:
        if (current - start_day).days % 7 == 0:
            daily_dir = csv_root / current.isoformat()
            daily_dir.mkdir(parents=True, exist_ok=True)
            path = daily_dir / "inventory.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["product_id", "quantity", "snapshot_date", "warehouse"])
                for product_id in range(1, profile.products + 1):
                    quantity: int | str = rng.randint(0, 2_000)
                    if rng.random() < error_rate / 6:
                        quantity = -rng.randint(1, 50)
                    writer.writerow([product_id, quantity, current.isoformat(), rng.choice(["RJ01", "SP01", "MG01"])])
            snapshot_count += 1
        current += timedelta(days=1)

    campaigns = []
    for campaign_id in range(1, max(10, profile.days // 3) + 1):
        campaign_start = start_day + timedelta(days=rng.randint(0, max(profile.days - 1, 1)))
        campaigns.append(
            {
                "campaign_id": campaign_id,
                "name": f"Campanha {campaign_id:04d}",
                "channel": rng.choice(["email", "social", "search", "affiliate"]),
                "start_date": campaign_start.isoformat(),
                "end_date": (campaign_start + timedelta(days=rng.randint(2, 20))).isoformat(),
                "budget_cents": rng.randint(50_000, 5_000_000),
            }
        )
    write_json(json_root / "campaigns.json", campaigns)
    return {"catalog_rows": profile.products, "inventory_snapshots": snapshot_count, "campaigns": len(campaigns)}


def corrupt_event(
    rng: random.Random,
    event: dict,
    profile: Profile,
    error_rate: float,
) -> dict:
    if rng.random() >= error_rate:
        return event
    issue = rng.choice(["customer", "product", "timestamp", "type", "device"])
    if issue == "customer":
        event["customer_id"] = profile.customers + rng.randint(1, 1_000)
    elif issue == "product":
        event["product_id"] = profile.products + rng.randint(1, 1_000)
    elif issue == "timestamp":
        event["event_at"] = "data-invalida"
    elif issue == "type":
        event.pop("event_type", None)
    else:
        event["device"] = None
    event["injected_issue"] = issue
    return event


def generate_events(
    root: Path,
    profile: Profile,
    rng: random.Random,
    start: datetime,
    end: datetime,
    error_rate: float,
) -> dict[str, int]:
    event_root = root / "events"
    event_root.mkdir(parents=True, exist_ok=True)
    file_handles: dict[str, object] = {}
    counts: dict[str, int] = {}
    duplicates = 0
    try:
        for event_id in range(1, profile.events + 1):
            occurred = random_datetime(rng, start, end)
            day_key = occurred.strftime("%Y-%m-%d")
            if day_key not in file_handles:
                path = event_root / f"events_{day_key}.jsonl"
                file_handles[day_key] = path.open("w", encoding="utf-8", buffering=1024 * 1024)
                counts[day_key] = 0
            event_type = choose_event_type(rng)
            event = {
                "event_id": f"evt-{event_id:012d}",
                "session_id": f"sess-{rng.randint(1, max(profile.customers * 3, 1)):010d}",
                "customer_id": rng.randint(1, profile.customers),
                "product_id": rng.randint(1, profile.products),
                "order_id": rng.randint(1, profile.orders) if event_type == "purchase" else None,
                "event_type": event_type,
                "event_at": occurred.isoformat(),
                "device": rng.choice(["mobile", "desktop", "tablet"]),
                "source": rng.choice(["organic", "email", "social", "search", "direct"]),
            }
            event = corrupt_event(rng, event, profile, error_rate)
            encoded = json.dumps(event, ensure_ascii=False)
            handle = file_handles[day_key]
            handle.write(encoded + "\n")
            counts[day_key] += 1
            if rng.random() < error_rate / 10:
                handle.write(encoded + "\n")
                counts[day_key] += 1
                duplicates += 1
    finally:
        for handle in file_handles.values():
            handle.close()
    return {"events_requested": profile.events, "event_rows_written": sum(counts.values()), "duplicates_injected": duplicates}


def generate_api_data(
    root: Path,
    profile: Profile,
    rng: random.Random,
    start: datetime,
    end: datetime,
    error_rate: float,
) -> dict[str, int]:
    api_root = root / "api"
    api_root.mkdir(parents=True, exist_ok=True)
    path = api_root / "shipments.jsonl"
    carriers = ["Rápido Sul", "Entrega Brasil", "Log Norte", "Expresso Rio"]
    with path.open("w", encoding="utf-8", buffering=1024 * 1024) as stream:
        for order_id in range(1, profile.orders + 1):
            created = random_datetime(rng, start, end)
            promised_days = rng.randint(1, 12)
            delay = rng.choices([0, 1, 2, 5, 10], weights=[70, 12, 10, 5, 3], k=1)[0]
            shipment = {
                "shipment_id": f"ship-{order_id:012d}",
                "source_sequence": order_id,
                "order_id": order_id,
                "carrier": rng.choice(carriers),
                "created_at": created.isoformat(),
                "promised_at": (created + timedelta(days=promised_days)).isoformat(),
                "delivered_at": (created + timedelta(days=promised_days + delay)).isoformat(),
                "status": "delivered",
            }
            if rng.random() < error_rate:
                issue = rng.choice(["missing_order", "missing_delivery", "invalid_status"])
                shipment["injected_issue"] = issue
                if issue == "missing_order":
                    shipment["order_id"] = profile.orders + rng.randint(1, 1_000)
                elif issue == "missing_delivery":
                    shipment["delivered_at"] = None
                else:
                    shipment["status"] = "UNKNOWN_VALUE"
            stream.write(json.dumps(shipment, ensure_ascii=False) + "\n")
    return {"shipments": profile.orders}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera fontes sintéticas para o curso de Big Data.")
    parser.add_argument("--profile", choices=PROFILES, default="demo")
    parser.add_argument("--output", type=Path, default=Path("data/source"))
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--error-rate", type=float, default=0.02)
    parser.add_argument("--end-date", type=date.fromisoformat, default=date(2026, 9, 30))
    parser.add_argument("--reset", action="store_true", help="Move os dados atuais para backup antes de gerar.")
    parser.add_argument(
        "--reset-lake",
        action="store_true",
        help="Move o lake local atual para backup antes de gerar.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0 <= args.error_rate <= 0.25:
        raise SystemExit("--error-rate deve estar entre 0 e 0.25")

    profile = PROFILES[args.profile]
    if args.reset_lake:
        ensure_empty_or_backup(args.output.parent / "lake", reset=True)
    ensure_empty_or_backup(args.output, args.reset)
    rng = random.Random(args.seed)
    end = datetime.combine(args.end_date, dt_time(23, 59, 59), tzinfo=timezone.utc)
    start = end - timedelta(days=profile.days)
    started = time.perf_counter()

    print(f"Gerando perfil '{args.profile}' em {args.output}...")
    summary = {
        "profile": args.profile,
        "seed": args.seed,
        "error_rate": args.error_rate,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "database": generate_database(args.output, profile, rng, start, end),
        "batch_files": generate_batch_files(args.output, profile, rng, start.date(), end.date(), args.error_rate),
        "events": generate_events(args.output, profile, rng, start, end, args.error_rate),
        "api": generate_api_data(args.output, profile, rng, start, end, args.error_rate),
    }
    summary["elapsed_seconds"] = round(time.perf_counter() - started, 2)
    write_json(args.output / "generation_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Geração concluída.")


if __name__ == "__main__":
    main()
