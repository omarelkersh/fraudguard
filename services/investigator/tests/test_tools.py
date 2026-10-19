import duckdb
import pytest

from fraudguard_investigator.tools import get_transaction


@pytest.fixture
def con():
    """An in-memory warehouse with two fake transactions."""
    con = duckdb.connect()
    con.execute("""
        create table fct_transactions as
        select * from (values
            ('tx-1', 'ACC-00000001', 1.20, 'online'),
            ('tx-2', 'ACC-00000001', 45.00, 'card_present')
        ) as t(transaction_id, account_id, amount, channel)
    """)
    return con


def test_get_transaction_returns_the_row(con):
    tx = get_transaction(con, "tx-1")
    assert tx["account_id"] == "ACC-00000001"
    assert tx["channel"] == "online"  # T1: what channel does tx-1 have?


def test_unknown_transaction_returns_none(con):
    assert get_transaction(con, "does-not-exist") is None  # T2
