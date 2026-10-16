from collections.abc import Iterable

from confluent_kafka import Producer

from fraudguard_generator.models import Transaction


def publish(producer: Producer, topic: str, events: Iterable[tuple[Transaction, bool]]) -> int:
    """Send each transaction to Kafka (without its label). Returns how many were sent."""
    sent = 0
    for transaction, _label in events:
        producer.produce(topic, key=transaction.account_id, value=transaction.model_dump_json())
        producer.poll(0)
        sent += 1
    producer.flush()  # wait until Kafka has received everything
    return sent
