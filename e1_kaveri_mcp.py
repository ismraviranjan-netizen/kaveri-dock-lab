# E1 · The standard connector — tools, a resource, a prompt (objective 3.7)
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("kaveri")                       # tools appear as mcp__kaveri__<name>

@mcp.tool()
def get_shipment_status(consignment_id: str) -> dict:
    """Return the current status of one consignment by its id (e.g. KF-2481)."""
    return {"id": consignment_id, "status": "CUSTOMS_HOLD", "missing": "e-way bill"}

@mcp.tool()
def find_alternate_carriers(lane: str) -> list:
    """List carriers that can take a lane (e.g. Pune-Chennai) within 48 hours."""
    return ["BlueDart", "Delhivery", "Gati"]

@mcp.resource("sop://214")
def sop_214() -> str:
    """SOP 214: customs holds and e-way bill re-filing."""
    return Path(__file__).with_name("sops").joinpath("sop_214.md").read_text(encoding="utf-8")

@mcp.prompt()
def customs_triage(consignment_id: str) -> str:
    """Triage one consignment in a customs hold using SOP 214."""
    return f"Consignment {consignment_id} is in a customs hold. Using SOP 214 section 4, list the re-filing steps."

if __name__ == "__main__":          # the guard: importing this file never starts the server
    mcp.run()
