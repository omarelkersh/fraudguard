import json
from datetime import UTC, datetime

from fraudguard_generator.generator import TransactionGenerator
from fraudguard_generator.producer import publish


class FakeProducer:
    """Pretends to be Kafka: stores every message instead of sending it."""

    def __init__(self):
        self.messages = []

    def produce(self, topic, key, value):
        self.messages.append((topic, key, value))

    def poll(self, timeout):
        pass

    def flush(self):
        pass


def test_publish_sends_every_transaction_keyed_by_account():
    events = list(TransactionGenerator(seed=1).stream(datetime(2026, 10, 16, tzinfo=UTC), n=20))
    fake = FakeProducer()

    sent = publish(fake, "transactions", events)

    assert sent == 20
    topic, key, value = fake.messages[0]
    assert key == json.loads(value)["account_id"]
