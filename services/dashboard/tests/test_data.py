import pandas as pd

from fraudguard_dashboard.data import kpis


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
