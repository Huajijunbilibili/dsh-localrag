"""Standalone smoke test for localrag-mcp - no harness needed.

Run:  python test-client.py
It starts server.py as a stdio child, indexes ./docs, and runs one search.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).resolve().parent


async def main() -> None:
    params = StdioServerParameters(
        command="python",
        args=[str(BASE_DIR / "server.py")],
        cwd=str(BASE_DIR),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])

            r = await session.call_tool("index_documents", {"path": str(BASE_DIR / "docs")})
            print("index:", r.content[0].text if r.content else r)

            r = await session.call_tool(
                "search", {"query": "LangGraph 多 agent 是怎么协作的", "k": 2}
            )
            for item in r.content:
                print("search:", item.text)

            r = await session.call_tool("list_documents", {})
            for item in r.content:
                print("docs:", item.text)


if __name__ == "__main__":
    asyncio.run(main())
