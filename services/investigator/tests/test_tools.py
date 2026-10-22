import duckdb
import httpx
import pytest

from fraudguard_investigator.tools import (
    get_account_history,
    get_account_profile,
    get_fraud_score,
    get_transaction,
)


@pytest.fixture
def con():
    """An in-memory warehouse with two fake transactions."""
    con = duckdb.connect()
    con.execute("""
        create table fct_transactions as
        select * from (values
            ('tx-1', 'ACC-00000001', timestamp '2026-10-01 10:00', 1.20,  'online',       'DE'),
            ('tx-2', 'ACC-00000001', timestamp '2026-10-01 10:01', 45.00, 'card_present', 'DE'),
            ('tx-3', 'ACC-00000002', timestamp '2026-10-01 10:02', 9.99,  'online',       'US')
        ) as t(transaction_id, account_id, transaction_at, amount, channel, country)
    """)
    return con


def test_get_transaction_returns_the_row(con):
    tx = get_transaction(con, "tx-1")
    assert tx["account_id"] == "ACC-00000001"
    assert tx["channel"] == "online"


def test_unknown_transaction_returns_none(con):
    assert get_transaction(con, "does-not-exist") is None


def test_account_history_is_newest_first_and_only_that_account(con):
    history = get_account_history(con, "ACC-00000001")
    assert [tx["transaction_id"] for tx in history] == ["tx-2", "tx-1"]


def test_get_fraud_score_calls_the_api():
    def fake_api(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/score"
        return httpx.Response(
            200, json={"fraud_probability": 0.97, "is_fraud": True, "model_version": "1"}
        )

    client = httpx.Client(base_url="http://scoring-api", transport=httpx.MockTransport(fake_api))
    assert get_fraud_score(client, {"amount": 1.2})["fraud_probability"] == 0.97


def test_account_profile_uses_only_earlier_payments(con):
    profile = get_account_profile(con, "tx-2")
    assert profile["past_transactions"] == 1  # only tx-1 is before tx-2
    assert profile["home_country"] == "DE"


def test_first_payment_has_empty_profile(con):
    profile = get_account_profile(con, "tx-1")
    assert profile["past_transactions"] == 0
    assert profile["account_id"] == "ACC-00000001"  # still known, so the agent can continue
