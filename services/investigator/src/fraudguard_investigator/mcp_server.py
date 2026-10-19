import os

import duckdb
from mcp.server import MCPServer

from fraudguard_investigator import tools

con = duckdb.connect(
    os.environ.get("WAREHOUSE_PATH", "pipelines/dbt/warehouse.duckdb"), read_only=True
)
mcp = MCPServer("fraudguard")


@mcp.tool()
def get_transaction(transaction_id: str) -> dict | None:
    """Look up one transaction by its ID."""
    return tools.get_transaction(con, transaction_id)


@mcp.tool()
def get_account_history(account_id: str, limit: int = 10) -> list[dict]:
    """The account's most recent transactions, newest first."""
    return tools.get_account_history(con, account_id, limit)


if __name__ == "__main__":
    mcp.run()
