import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command=sys.executable, args=["-m", "fraudguard_investigator.mcp_server"]
    )
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        tools = await session.list_tools()
        print("Tools:", [t.name for t in tools.tools])

        result = await session.call_tool(
            "get_account_history", {"account_id": "ACC-00000137", "limit": 3}
        )
        for item in result.content:
            print(item.text)


asyncio.run(main())
