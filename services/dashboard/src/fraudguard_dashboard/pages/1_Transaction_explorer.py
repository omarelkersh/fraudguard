import asyncio
import os

import duckdb
import httpx
import pandas as pd
import streamlit as st

from fraudguard_dashboard.data import load_features
from fraudguard_investigator.agent import investigate
from fraudguard_investigator.tools import get_account_profile, get_fraud_score, get_transaction

WAREHOUSE = os.environ.get("WAREHOUSE_PATH", "pipelines/dbt/warehouse.duckdb")
SCORING_API = os.environ.get("SCORING_API_URL", "http://localhost:8000")

st.title("Transaction explorer")
tx_id = st.text_input("Transaction ID").strip()
if not tx_id:
    st.stop()  # nothing to show until an ID is entered

with duckdb.connect(WAREHOUSE, read_only=True) as con:
    tx = get_transaction(con, tx_id)
    if tx is None:
        st.error("No transaction with this ID.")
        st.stop()
    profile = get_account_profile(con, tx_id)
    features = load_features(con, tx_id)

left, right = st.columns(2)
left.subheader("Transaction")
left.table(pd.Series(tx, name="value").astype(str))
right.subheader("Account before this payment")
right.table(pd.Series(profile, name="value").astype(str))

st.subheader("Live fraud score")
if features is None:
    st.info("Not in the training set yet (no label), so there are no features to score.")
else:
    try:
        with httpx.Client(base_url=SCORING_API, timeout=10) as client:
            score = get_fraud_score(client, features)
        st.metric(
            "Fraud probability",
            f"{score['fraud_probability']:.1%}",
            help=f"Model version {score['model_version']}",
        )
    except httpx.HTTPError as e:  # the parent class of every httpx error
        st.warning(f"Scoring API unavailable at {SCORING_API}: {e}")

if st.button("Investigate with the AI agent"):
    with st.spinner("The agent is gathering evidence (about 30 s)..."):
        result = asyncio.run(investigate(tx_id))
    st.markdown(result["report"])
    tools = ", ".join(result["tool_calls"])
    st.caption(f"{result['seconds']} s, tools: {tools}, {result['model']}")
