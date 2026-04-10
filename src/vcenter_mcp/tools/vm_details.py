"""Read-only VM guest and hardware detail tools."""

from vcenter_mcp.app import mcp
from vcenter_mcp.client import vcenter_get
from vcenter_mcp.registry import json_response, path_id, resolve_vcenter


@mcp.tool()
def get_vm_guest_identity(vm: str, vcenter_name: str | None = None) -> str:
    """Get guest identity details for a VM."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/guest/identity", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_vm_guest_local_filesystems(vm: str, vcenter_name: str | None = None) -> str:
    """List guest local filesystems for a VM."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/guest/local-filesystem", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_vm_guest_network_interfaces(vm: str, vcenter_name: str | None = None) -> str:
    """List guest network interfaces for a VM."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/guest/networking/interfaces", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_hardware(vm: str, vcenter_name: str | None = None) -> str:
    """Get VM hardware summary."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_boot(vm: str, vcenter_name: str | None = None) -> str:
    """Get VM boot configuration."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/boot", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_cpu(vm: str, vcenter_name: str | None = None) -> str:
    """Get VM CPU configuration."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/cpu", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_memory(vm: str, vcenter_name: str | None = None) -> str:
    """Get VM memory configuration."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/memory", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_vm_disks(vm: str, vcenter_name: str | None = None) -> str:
    """List virtual disks for a VM."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/disk", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_disk(vm: str, disk: str, vcenter_name: str | None = None) -> str:
    """Get a virtual disk by disk identifier."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/disk/{path_id(disk)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_vm_nics(vm: str, vcenter_name: str | None = None) -> str:
    """List VM virtual NICs."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/ethernet", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm_nic(vm: str, nic: str, vcenter_name: str | None = None) -> str:
    """Get a single VM virtual NIC."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}/hardware/ethernet/{path_id(nic)}", **resolve_vcenter(vcenter_name)))

