from datetime import UTC, datetime

from fraudguard_generator.generator import TransactionGenerator
from fraudguard_generator.models import Transaction

TIMESTAMP = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


def generate(seed: int, n: int) -> list[tuple[Transaction, bool]]:
    """Helper: n normal transactions from a fresh generator with the given seed."""
    generator = TransactionGenerator(seed=seed)
    return [generator.normal_transaction(TIMESTAMP) for _ in range(n)]


def test_generates_valid_transactions():
    # Pydantic validates on creation, so generating 1,000 without an error IS the check
    results = generate(seed=1, n=1000)
    assert all(isinstance(tx, Transaction) for tx, _ in results)


def test_same_seed_gives_same_transactions():
    # Pydantic models compare field by field, so == works directly
    assert generate(seed=42, n=10) == generate(seed=42, n=10)


def test_different_seeds_give_different_transactions():
    assert generate(seed=1, n=10) != generate(seed=2, n=10)


def test_most_transactions_happen_in_home_country():
    generator = TransactionGenerator(seed=7)
    home_country = {a.account_id: a.home_country for a in generator.accounts}
    results = [generator.normal_transaction(TIMESTAMP) for _ in range(1000)]

    in_home = sum(1 for tx, _ in results if tx.country == home_country[tx.account_id])
    assert in_home / len(results) >= 0.90


def test_normal_transactions_are_labelled_legit():
    results = generate(seed=3, n=100)
    assert all(label is False for _, label in results)
