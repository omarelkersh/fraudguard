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
