import os
from datetime import UTC, datetime

from confluent_kafka import Producer

from fraudguard_generator.generator import TransactionGenerator
from fraudguard_generator.producer import publish


def main() -> None:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")  # default for your Mac
    n = int(os.environ.get("N_TRANSACTIONS", "1000"))

    producer = Producer({"bootstrap.servers": bootstrap})
    events = TransactionGenerator(seed=42).stream(datetime.now(UTC), n=n, fraud_rate=0.02)
    sent = publish(producer, "transactions", events)
    print(f"Sent {sent} transactions to {bootstrap}")
