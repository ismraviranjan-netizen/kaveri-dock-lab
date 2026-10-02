# E1 probe — talk to the server in-process (no stdio, no network)
import asyncio, json
from fastmcp import Client
from e1_kaveri_mcp import mcp

async def main():
    async with Client(mcp) as c:
        tools = await c.list_tools()
        print("tools/list     ->", [t.name for t in tools])
        print("resources/list ->", [str(r.uri) for r in await c.list_resources()])
        print("prompts/list   ->", [p.name for p in await c.list_prompts()])
        gss = next(t for t in tools if t.name == "get_shipment_status")
        print("inputSchema of get_shipment_status ->", json.dumps(gss.input_schema))
        sop = await c.read_resource("sop://214")
        print("resources/read sop://214 -> first line:", sop[0].text.splitlines()[0])
        res = await c.call_tool("get_shipment_status", {"consignment_id": "KF-2481"})
        print("tools/call get_shipment_status ->", res.data)

asyncio.run(main())
