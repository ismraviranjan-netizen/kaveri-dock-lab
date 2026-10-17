# E1 · The standard connector: tools, a resource, a prompt, and a model that uses all three  (objective 3.7, Law 1)
#
#   Server:  one FastMCP server exposes two TOOLS (forklifts), one RESOURCE (the manifest on the rack),
#            one PROMPT (the laminated card). Clients discover each with */list, then call or read.
#   Probe:   an in-process client lists the three primitives. No stdio, no network, no model, no cost.
#   Model:   the server's tool list becomes the model's tool list. The model asks for a tool;
#            the CODE dispatches the call through the MCP client and sends the result back.
#
# Needs:  pip install fastmcp
# Run on battery:  DRY_RUN=1 python e1_connector.py       (Windows:  set DRY_RUN=1  first)
# Run live:        python e1_connector.py                 (needs ANTHROPIC_API_KEY, see common.py)

import asyncio
from pathlib import Path
from common import make_client, trace, text_of, tool_result, MODEL, MAX_TOKENS, SOP_PATH, DRY_RUN

try:
    from fastmcp import FastMCP, Client
except ImportError:
    raise SystemExit("E1 needs the MCP SDK:  pip install fastmcp")


# ---------------------------------------------------------------
# STEP 0. The server. The name "kaveri" becomes the namespace: clients see mcp__kaveri__<tool>.
# ---------------------------------------------------------------

mcp = FastMCP("kaveri")


@mcp.tool()
def get_shipment_status(consignment_id: str) -> dict:
    """Return the current status of one consignment by its id (e.g. KF-2481)."""
    return {"id": consignment_id, "status": "CUSTOMS_HOLD", "missing": "e-way bill", "leg": "ICD Pune"}
# The schema is written by the TYPE HINT, the description by the DOCSTRING, the name by the function.
# Sabotage: change the hint to int and watch the schema say "integer" without a single error.


@mcp.tool()
def find_alternate_carriers(lane: str) -> list:
    """List carriers that can take a lane (e.g. Pune-Chennai) within 48 hours."""
    return ["BlueDart", "Delhivery", "Gati"]


@mcp.resource("sop://214")                      # data, not action: no side effects, no tool-call round-trip
def sop_214() -> str:
    """SOP 214: customs holds and e-way bill re-filing."""
    return Path(SOP_PATH).read_text(encoding="utf-8")


@mcp.prompt()                                   # a reusable template, versioned on the server
def customs_triage(consignment_id: str) -> str:
    """Triage one consignment in a customs hold using SOP 214."""
    return ("Consignment " + consignment_id + " is in a customs hold. Check its status, then using SOP 214 "
            "section 4 list the re-filing steps. Never promise a release date.")


# ---------------------------------------------------------------
# STEP 1. The probe: list the three primitives through an in-process client. Free.
# ---------------------------------------------------------------

async def probe():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        print("tools/list     ->", [t.name for t in tools])
        print("resources/list ->", [str(r.uri) for r in resources])
        print("prompts/list   ->", [p.name for p in prompts])
        for t in tools:
            if t.name == "get_shipment_status":
                print("inputSchema of get_shipment_status ->", t.input_schema)
        sop = await client.read_resource("sop://214")
        print("resources/read sop://214 -> first line:", sop[0].text.splitlines()[0])


# ---------------------------------------------------------------
# STEP 2. Translate: an MCP tool listing becomes the Messages API's tool list.
#         Same three fields. This is the whole bridge between the two standards.
# ---------------------------------------------------------------

async def api_tools_from_server(client):
    tools = []
    for t in await client.list_tools():
        tools.append({"name": t.name, "description": t.description or "", "input_schema": t.input_schema})
    return tools


# ---------------------------------------------------------------
# STEP 3. One ticket through the connector: resource into the system prompt, prompt as the user turn,
#         tools dispatched through the client when the model asks.
# ---------------------------------------------------------------

async def work_ticket(consignment_id):
    model_client = make_client()

    async with Client(mcp) as server:
        # 3a. The RESOURCE is read into context. Costs no tool call. Tools act; resources inform.
        sop_text = (await server.read_resource("sop://214"))[0].text
        system = "You are KAVI, the Kaveri Freight dispatcher's assistant. The relevant SOP follows.\n\n" + sop_text

        # 3b. The PROMPT template is fetched from the server and becomes the first user message.
        card = await server.get_prompt("customs_triage", {"consignment_id": consignment_id})
        conversation = [{"role": "user", "content": card.messages[0].content.text}]

        # 3c. The TOOLS the server lists are the tools the model may ask for.
        tools = await api_tools_from_server(server)

        # 3d. A short bounded loop: tool_use -> dispatch through MCP -> send the result back.
        for turn in range(1, 5):
            reply = model_client.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS, system=system, tools=tools, messages=conversation,
            )
            trace(turn, reply)

            if reply.stop_reason == "tool_use":
                conversation.append({"role": "assistant", "content": reply.content})
                results = []
                for block in reply.content:
                    if block.type == "tool_use":
                        outcome = await server.call_tool(block.name, block.input)   # tools/call over MCP
                        results.append(tool_result(block, outcome.data))
                conversation.append({"role": "user", "content": results})
                continue

            if reply.stop_reason == "refusal":
                return "The model declined to answer."
            return text_of(reply)

    return "ESCALATED: tool budget exhausted"


if __name__ == "__main__":                       # the guard: importing this file never starts the server
    print("# E1 · standard connector · " + ("DRY_RUN" if DRY_RUN else "LIVE · " + MODEL))
    print("=== Probe: the three primitives, in-process ===")
    asyncio.run(probe())
    print()
    print("=== One ticket: resource in context, prompt as the user turn, tools via MCP ===")
    print(asyncio.run(work_ticket("KF-2481")))
    # To run the server on stdio for a real client (Claude Code, an IDE):  python -c "from e1_connector import mcp; mcp.run()"
