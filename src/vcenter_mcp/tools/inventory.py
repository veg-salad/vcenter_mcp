"""Inventory tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.registry import VCENTERS, json_response


@mcp.tool()
def list_vcenters() -> str:
    """List configured vCenter instances from inventory.yaml."""
    return json_response({"vcenters": VCENTERS})


@mcp.tool()
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
