from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    customers: int
    products: int
    orders: int
    events: int
    days: int
    suppliers: int


PROFILES = {
    "demo": Profile(
        customers=1_000,
        products=500,
        orders=10_000,
        events=100_000,
        days=30,
        suppliers=30,
    ),
    "medium": Profile(
        customers=10_000,
        products=2_000,
        orders=100_000,
        events=1_000_000,
        days=180,
        suppliers=100,
    ),
    "large": Profile(
        customers=50_000,
        products=10_000,
        orders=1_000_000,
        events=10_000_000,
        days=365,
        suppliers=500,
    ),
}

