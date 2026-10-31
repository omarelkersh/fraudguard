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
