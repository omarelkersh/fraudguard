import duckdb


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
