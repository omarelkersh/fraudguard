import os
from datetime import UTC, datetime

from confluent_kafka import Producer

from fraudguard_generator.generator import TransactionGenerator
from fraudguard_generator.producer import publish, publish_labels


def main() -> None:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")  # default for your Mac
    n = int(os.environ.get("N_TRANSACTIONS", "1000"))

    producer = Producer({"bootstrap.servers": bootstrap})
    generator = TransactionGenerator(seed=42)
    events = list(generator.stream(datetime.now(UTC), n=n, fraud_rate=0.02))

    sent = publish(producer, "transactions", events)
    labels = [generator.label_for(tx, is_fraud) for tx, is_fraud in events]
    labelled = publish_labels(producer, "fraud_labels", labels)  # the labels topic name
    print(f"Sent {sent} transactions and {labelled} labels to {bootstrap}")
