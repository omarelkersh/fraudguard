import duckdb
import pandas as pd


def load_daily(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """The daily fraud mart, oldest day first."""
    return con.sql("select * from agg_daily_fraud order by day").df()


def kpis(daily: pd.DataFrame) -> dict:
    """Headline numbers. The fraud rate is weighted: total frauds over total transactions."""
    transactions = int(daily["transactions"].sum())
    frauds = int(daily["frauds"].sum())
    return {
        "transactions": transactions,
        "frauds": frauds,
        "fraud_rate": frauds / transactions if transactions > 0 else 0,
        "total_amount": float(daily["total_amount"].sum()),
    }


def load_features(con: duckdb.DuckDBPyConnection, transaction_id: str) -> dict | None:
    """The model's input features for one transaction, as computed for training."""
    row = con.execute(
        """
        select cast(amount as double), amount_vs_account_avg, tx_last_10min, is_foreign, channel
        from ml_training_set
        where transaction_id = ?
        """,
        [transaction_id],
    ).fetchone()
    if row is None:
        return None
    names = ["amount", "amount_vs_account_avg", "tx_last_10min", "is_foreign", "channel"]
    return dict(zip(names, row, strict=True))
