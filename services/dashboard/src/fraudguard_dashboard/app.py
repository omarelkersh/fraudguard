import os

import duckdb
import streamlit as st

from fraudguard_dashboard.data import kpis, load_daily

WAREHOUSE = os.environ.get("WAREHOUSE_PATH", "pipelines/dbt/warehouse.duckdb")


@st.cache_data(ttl=60)  # re-read the warehouse at most once a minute
def daily():
    with duckdb.connect(WAREHOUSE, read_only=True) as con:  # the dashboard never writes
        return load_daily(con)


st.set_page_config(page_title="FraudGuard", layout="wide")
st.title("FraudGuard: fraud overview")

df = daily()
k = kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{k['transactions']:,}")
c2.metric("Frauds", f"{k['frauds']:,}")
c3.metric("Fraud rate", f"{k['fraud_rate']:.1%}")
c4.metric("Amount", f"{k['total_amount']:,.0f}")

st.subheader("Fraud rate per day")
by_day = df.groupby("day")[["transactions", "frauds"]].sum()
by_day["fraud_rate"] = by_day["frauds"] / by_day["transactions"]  # weighted, like kpis()
st.line_chart(by_day["fraud_rate"])

left, right = st.columns(2)
left.subheader("Frauds by channel")
left.bar_chart(df.groupby("channel")["frauds"].sum())
right.subheader("Frauds by country")
right.bar_chart(df.groupby("country")["frauds"].sum())
