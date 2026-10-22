import os
from typing import Annotated

import duckdb
from mcp.server import MCPServer
from pydantic import Field

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
def get_account_history(
    account_id: Annotated[str, Field(pattern=r"^ACC-\d{8}$")], limit: int = 10
) -> list[dict]:
    """The account's most recent transactions, newest first."""
    return tools.get_account_history(con, account_id, limit)


@mcp.tool()
def get_account_profile(transaction_id: str) -> dict:
    """Account ID, home country and typical amount, from payments BEFORE this transaction."""
    return tools.get_account_profile(con, transaction_id)


if __name__ == "__main__":
    mcp.run()
