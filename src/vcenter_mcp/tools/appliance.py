"""Read-only appliance tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.client import vcenter_get
from vcenter_mcp.registry import json_response, path_id, resolve_vcenter


@mcp.tool()
def get_appliance_version(vcenter_name: str | None = None) -> str:
    """Get appliance version information."""
    return json_response(vcenter_get("/api/appliance/system/version", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_time(vcenter_name: str | None = None) -> str:
    """Get current appliance time settings."""
    return json_response(vcenter_get("/api/appliance/system/time", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_timezone(vcenter_name: str | None = None) -> str:
    """Get appliance timezone configuration."""
    return json_response(vcenter_get("/api/appliance/system/time/timezone", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_ntp(vcenter_name: str | None = None) -> str:
    """Get appliance NTP configuration."""
    return json_response(vcenter_get("/api/appliance/ntp", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_update(vcenter_name: str | None = None) -> str:
    """Get appliance update configuration."""
    return json_response(vcenter_get("/api/appliance/update", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_update_pending(vcenter_name: str | None = None) -> str:
    """Get pending appliance updates."""
    return json_response(vcenter_get("/api/appliance/update/pending", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_appliance_services(vcenter_name: str | None = None) -> str:
    """List appliance services."""
    return json_response(vcenter_get("/api/appliance/services", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_service(service: str, vcenter_name: str | None = None) -> str:
    """Get a specific appliance service."""
    return json_response(vcenter_get(f"/api/appliance/services/{path_id(service)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_health(vcenter_name: str | None = None) -> str:
    """Get overall appliance health."""
    return json_response(vcenter_get("/api/appliance/health/system", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_health_cpu(vcenter_name: str | None = None) -> str:
    """Get appliance CPU health."""
    return json_response(vcenter_get("/api/appliance/health/load", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_health_memory(vcenter_name: str | None = None) -> str:
    """Get appliance memory health."""
    return json_response(vcenter_get("/api/appliance/health/mem", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_health_storage(vcenter_name: str | None = None) -> str:
    """Get appliance storage health."""
    return json_response(vcenter_get("/api/appliance/health/storage", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_health_swap(vcenter_name: str | None = None) -> str:
    """Get appliance swap health."""
    return json_response(vcenter_get("/api/appliance/health/swap", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_appliance_network_interfaces(vcenter_name: str | None = None) -> str:
    """List appliance network interfaces."""
    return json_response(vcenter_get("/api/appliance/networking/interfaces", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_network_interface(interface: str, vcenter_name: str | None = None) -> str:
    """Get an appliance network interface."""
    return json_response(vcenter_get(f"/api/appliance/networking/interfaces/{path_id(interface)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_appliance_local_accounts(vcenter_name: str | None = None) -> str:
    """List appliance local accounts."""
    return json_response(vcenter_get("/api/appliance/local-accounts", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_appliance_local_account(username: str, vcenter_name: str | None = None) -> str:
    """Get an appliance local account."""
    return json_response(vcenter_get(f"/api/appliance/local-accounts/{path_id(username)}", **resolve_vcenter(vcenter_name)))
