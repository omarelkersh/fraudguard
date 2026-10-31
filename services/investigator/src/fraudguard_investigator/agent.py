import asyncio
import os
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

qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
ollama = httpx.Client(base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"), timeout=120)


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
    "You are a fraud investigator. Call ONE tool at a time and use IDs exactly "
    "as tools return them. Steps: "
    "1) Get the transaction. "
    "2) Get the account profile (home country, typical amount), then the account "
    "history using the account_id from the profile. "
    "Compare this payment with them: how many payments happened within 10 minutes, "
    "how many times larger than the typical amount it is, and whether the country "
    "differs from the home country. "
    "3) Search the policy by describing the pattern you ACTUALLY found in the tool "
    "results. If the account has no other payments, say so: do not invent a pattern. "
    "4) Write a short report: verdict (suspicious / not suspicious), evidence with "
    "transaction IDs, amounts and times, and the policy rule IDs that apply. "
    "Cite a rule ONLY if all of its conditions are met by the evidence (amounts, "
    "channel, country, time window). If no rule fits, the verdict is not suspicious. "
    "Only state facts returned by tools."
    " End the report with one line: 'Rules: ' followed by the cited rule IDs, or 'Rules: none'."
)


async def investigate(transaction_id: str, model: str = "qwen3:8b") -> dict:
    start = time.perf_counter()
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "fraudguard_investigator.mcp_server"],
        # MCP passes only a safe env subset to the server, so hand over the warehouse path
        env={"WAREHOUSE_PATH": os.environ.get("WAREHOUSE_PATH", "pipelines/dbt/warehouse.duckdb")},
    )
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = mcp_to_langchain(session, await session.list_tools()) + [search_policy]
        llm = ChatOllama(model=model, temperature=0, reasoning=False).bind_tools(tools)

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

        messages = result["messages"]
        usage = [m.usage_metadata for m in messages if getattr(m, "usage_metadata", None)]
        return {
            "model": model,
            "report": messages[-1].content,
            "seconds": round(time.perf_counter() - start, 1),
            "input_tokens": sum(u["input_tokens"] for u in usage),
            "output_tokens": sum(u["output_tokens"] for u in usage),
            "tool_calls": [
                c["name"] for m in messages for c in (getattr(m, "tool_calls", None) or [])
            ],
        }


if __name__ == "__main__":
    model = sys.argv[2] if len(sys.argv) > 2 else "qwen3:8b"
    outcome = asyncio.run(investigate(sys.argv[1], model))
    print(outcome["report"])
    print({k: v for k, v in outcome.items() if k != "report"})
