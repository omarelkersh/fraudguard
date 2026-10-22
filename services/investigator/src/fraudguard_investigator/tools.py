import duckdb
import httpx


def get_transaction(con: duckdb.DuckDBPyConnection, transaction_id: str) -> dict | None:
    """Look up one transaction (no fraud label!). Returns None if it doesn't exist."""
    row = con.execute(
        "select * from fct_transactions where transaction_id = ?",  # ? = safe placeholder
        [transaction_id],
    ).fetchone()
    if row is None:
        return None
    columns = [c[0] for c in con.description]
    return dict(zip(columns, row, strict=True))


def get_account_history(
    con: duckdb.DuckDBPyConnection, account_id: str, limit: int = 10
) -> list[dict]:
    """The account's most recent transactions, newest first."""
    rows = con.execute(
        """
        select transaction_id, transaction_at, amount, channel, country
        from fct_transactions
        where account_id = ?
        order by transaction_at DESC          -- newest first
        limit ?
        """,
        [account_id, limit],
    ).fetchall()
    columns = [c[0] for c in con.description]
    return [dict(zip(columns, r, strict=True)) for r in rows]


def get_fraud_score(client: httpx.Client, features: dict) -> dict:
    """Ask the scoring API for a fraud probability. `features` must match the API's ScoreRequest."""
    response = client.post("/score", json=features)  # which HTTP method does /score use?
    response.raise_for_status()  # turn 4xx/5xx errors into exceptions
    return response.json()


def get_account_profile(con: duckdb.DuckDBPyConnection, transaction_id: str) -> dict:
    """Account ID, home country and typical amount, from the account's payments BEFORE this one."""
    row = con.execute(
        """
        select any_value(t.account_id) as account_id,
               count(p.transaction_id) as past_transactions,
               mode(p.country) as home_country,
               round(median(p.amount), 2) as typical_amount
        from fct_transactions t
        left join fct_transactions p  -- left: a first payment still returns its account
          on p.account_id = t.account_id and p.transaction_at < t.transaction_at
        where t.transaction_id = ?
        """,
        [transaction_id],
    ).fetchone()
    columns = [c[0] for c in con.description]
    return dict(zip(columns, row, strict=True))
