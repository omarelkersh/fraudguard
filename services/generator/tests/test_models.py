from datetime import datetime, timezone 
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from fraudguard_generator.models import Transaction

def valid_transaction_data() -> dict:
    return {
        "transaction_id": uuid4(),
        "account_id": "ACC-12345678",
        "merchant_id": "MER-87654321",
        "amount": Decimal("100.00"),
        "currency": "USD",
        "timestamp": datetime(2026,10,7,12,0,tzinfo=timezone.utc),
        "channel": "online",
        "country": "US",
    }

def test_valid_transaction_is_accepted():
    data = valid_transaction_data()
    transaction = Transaction(**data)
    assert transaction.transaction_id == data["transaction_id"]
    assert transaction.account_id == data["account_id"]
    assert transaction.merchant_id == data["merchant_id"]
    assert transaction.amount == data["amount"]
    assert transaction.currency == data["currency"]
    assert transaction.timestamp == data["timestamp"]
    assert transaction.channel == data["channel"]
    assert transaction.country == data["country"]

@pytest.mark.parametrize("bad_amount",["0","-5.00", "10.123"])
def test_invalid_amount_is_rejected(bad_amount):
    data = valid_transaction_data()
    data["amount"] = Decimal(bad_amount)
    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_timestamp_is_rejected():
    data = valid_transaction_data()
    data["timestamp"] = datetime(2026,10,7,12,0)  # naive datetime
    with pytest.raises(ValidationError):
        Transaction(**data)

@pytest.mark.parametrize("bad_account_id", ["acc-00012345", "CAC-09263456", "aCC-87612354", "ACC-1234567", "ACC-123456789"])
def test_invalid_account_id_is_rejected(bad_account_id):
    data = valid_transaction_data()
    data["account_id"] = bad_account_id
    with pytest.raises(ValidationError):
        Transaction(**data)

@pytest.mark.parametrize("bad_merchant_id", ["mer-00012345", "MER-1234567800", "invalid-merchant-id"])
def test_invalid_merchant_id_is_rejected(bad_merchant_id):
    data = valid_transaction_data()
    data["merchant_id"] = bad_merchant_id
    with pytest.raises(ValidationError):
        Transaction(**data)

@pytest.mark.parametrize("bad_currency", ["GBP", "NTD", "JPY"])
def test_invalid_currency_is_rejected(bad_currency):
    data = valid_transaction_data()
    data["currency"] = bad_currency
    with pytest.raises(ValidationError):
        Transaction(**data)

@pytest.mark.parametrize("bad_channel", ["invalid_channel", "INVALID-CHANNEL"])
def test_invalid_channel_is_rejected(bad_channel):
    data = valid_transaction_data()
    data["channel"] = bad_channel
    with pytest.raises(ValidationError):
        Transaction(**data)

@pytest.mark.parametrize("bad_country", ["USA", "uss", "U!",""])
def test_invalid_country_is_rejected(bad_country):
    data = valid_transaction_data()
    data["country"] = bad_country
    with pytest.raises(ValidationError):
        Transaction(**data)
