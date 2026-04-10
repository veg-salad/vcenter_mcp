"""Read-only appliance tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.client import vcenter_get
from vcenter_mcp.registry import json_response, resolve_vcenter


@mcp.tool()
def get_appliance_version(vcenter_name: str | None = None) -> str:
    """Get appliance version information."""
    return json_response(vcenter_get("/api/appliance/system/version", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_time(vcenter_name: str | None = None) -> str:
    """Get current appliance time settings."""
    return json_response(vcenter_get("/api/appliance/system/time", **resolve_vcenter(vcenter_name)))
