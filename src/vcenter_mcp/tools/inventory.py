"""Inventory tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.registry import VCENTERS, json_response
from vcenter_mcp.security import guard_tool


@mcp.tool()
@guard_tool("list_vcenters")
def list_vcenters() -> str:
    """List configured vCenter instances from inventory.yaml."""
    return json_response({"vcenters": VCENTERS})


@mcp.tool()
@guard_tool("get_vcenter_inventory")
def get_vcenter_inventory(vcenter_name: str | None = None) -> str:
    """Return configured inventory entries and guidance for using vCenter tools."""
    selected = [entry for entry in VCENTERS if not vcenter_name or entry["name"].lower() == vcenter_name.lower()]
    return json_response(
        {
            "vcenters": selected,
            "usage": {
                "parameter": "vcenter_name",
                "note": "Pass vcenter_name when more than one vCenter is configured.",
            },
        }
    )
