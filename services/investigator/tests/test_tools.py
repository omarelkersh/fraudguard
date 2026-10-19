import duckdb
import pytest

from fraudguard_investigator.tools import get_account_history, get_transaction


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
    assert tx["channel"] == "online"  # T1: what channel does tx-1 have?


def test_unknown_transaction_returns_none(con):
    assert get_transaction(con, "does-not-exist") is None  # T2


def test_account_history_is_newest_first_and_only_that_account(con):
    history = get_account_history(con, "ACC-00000001")
    assert [tx["transaction_id"] for tx in history] == ["tx-2", "tx-1"]
