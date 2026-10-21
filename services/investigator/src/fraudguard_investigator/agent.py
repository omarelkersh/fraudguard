import asyncio
import sys
import time

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool, tool
from langchain_ollama import ChatOllama
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from qdrant_client import QdrantClient

from fraudguard_investigator import rag

qdrant = QdrantClient(url="http://localhost:6333")
ollama = httpx.Client(base_url="http://localhost:11434", timeout=120)


@tool
def search_policy(question: str) -> str:
    """Search the bank's AML/fraud policy for rules relevant to the question."""
    return "\n\n".join(rag.search_policy(qdrant, ollama, question, k=2))


def mcp_to_langchain(session: ClientSession, listed) -> list[StructuredTool]:
    """Wrap every tool from the MCP server as a LangChain tool the agent can call."""
    tools = []
    for t in listed.tools:

        async def call(_name: str = t.name, **kwargs) -> str:
            result = await session.call_tool(_name, kwargs)
            return "\n".join(item.text for item in result.content) or "no result"

        tools.append(
            StructuredTool.from_function(
                coroutine=call,
                name=t.name,  # B1: the MCP tool's name
                description=t.description or "",
                args_schema=t.input_schema,  # the tool's JSON schema (MCP 2.x name)
            )
        )
    return tools  # B2: what do we return?


SYSTEM = (
    "You are a fraud investigator. Steps: "
    "1) Get the transaction. "
    "2) Get the account history and look for patterns: how many payments happened "
    "within 10 minutes of this one, unusually large amounts, and payments outside "
    "the home country. "
    "3) Search the policy by describing the PATTERN you found (for example "
    "'many small online payments within minutes'), not just the amount. "
    "4) Write a short report: verdict (suspicious / not suspicious), evidence with "
    "transaction IDs, amounts and times, and the policy rule IDs that apply. "
    "Only state facts returned by tools."
)


async def investigate(transaction_id: str) -> str:
    server = StdioServerParameters(
        command=sys.executable, args=["-m", "fraudguard_investigator.mcp_server"]
    )
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = mcp_to_langchain(session, await session.list_tools()) + [search_policy]
        llm = ChatOllama(model="qwen3:8b", temperature=0, reasoning=False).bind_tools(tools)

        async def agent_node(state: MessagesState) -> dict:
            return {"messages": [await llm.ainvoke(state["messages"])]}

        graph = StateGraph(MessagesState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", ToolNode(tools))
        graph.add_edge(START, "agent")  # G1: where does it start?
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")  # G2: after a tool runs, go back to…?
        app = graph.compile()

        result = await app.ainvoke(
            {
                "messages": [
                    SystemMessage(SYSTEM),
                    HumanMessage(f"Investigate transaction {transaction_id}."),
                ]
            },
            {"recursion_limit": 12},  # safety stop: max steps
        )

        for message in result["messages"]:
            for call in getattr(message, "tool_calls", []) or []:
                print("TOOL CALL:", call["name"], call["args"])

        return result["messages"][-1].content


if __name__ == "__main__":
    start = time.time()
    print(asyncio.run(investigate(sys.argv[1])))
    print(f"--- {time.time() - start:.1f}s")
