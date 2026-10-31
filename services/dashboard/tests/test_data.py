import duckdb
import pandas as pd

from fraudguard_dashboard.data import kpis, load_features


def test_fraud_rate_is_weighted_by_volume():
    daily = pd.DataFrame(
        {
            "transactions": [3, 997],
            "frauds": [3, 7],
            "fraud_rate": [1.0, 0.007],
            "total_amount": [10.0, 90.0],
        }
    )
    # the mean of the rates would be 50%; the real rate is 10 / 1000 = 1%
    assert kpis(daily)["fraud_rate"] == 0.01


def test_load_features_matches_the_api_request():
    con = duckdb.connect()
    con.execute("""
        create table ml_training_set as select * from (values
            ('tx-1', 1.20::decimal(12, 2), 0.02::double, 9, false, 'online', true)
        ) as t(transaction_id, amount, amount_vs_account_avg, tx_last_10min, is_foreign,
               channel, is_fraud)
    """)
    assert load_features(con, "tx-1") == {
        "amount": 1.20,
        "amount_vs_account_avg": 0.02,
        "tx_last_10min": 9,
        "is_foreign": False,
        "channel": "online",
    }
    assert load_features(con, "nope") is None
