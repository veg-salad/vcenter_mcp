"""Core read-only vCenter inventory tools."""

from __future__ import annotations

import re
from typing import Any

from vcenter_mcp.app import mcp
from vcenter_mcp.client import vcenter_get
from vcenter_mcp.registry import json_response, path_id, resolve_vcenter, split_csv
from vcenter_mcp.vsphere_ws import (
    get_cluster_cpu_memory_utilization_daily_rollup,
    get_cluster_cpu_memory_utilization_period,
    get_cluster_resource_utilization,
    get_host_detail,
    list_hosts_ws,
)


def _clean_params(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in (None, "", [])}


def _window_to_days(window: str) -> int:
    value = (window or "").strip().lower()
    if not value:
        raise ValueError("window cannot be empty. Use values like '24 hours' or '7 days'.")

    pattern = r"^(\d+)\s*(h|hr|hrs|hour|hours|d|day|days)$"
    match = re.match(pattern, value)
    if not match:
        raise ValueError("Unsupported window format. Use values like '24 hours', '4 days', or '7d'.")

    amount = int(match.group(1))
    unit = match.group(2)

    if unit in {"d", "day", "days"}:
        if amount < 1 or amount > 30:
            raise ValueError("days must be between 1 and 30.")
        return amount

    # Hours mode maps to full-day windows only for predictable rollups.
    if amount % 24 != 0:
        raise ValueError("hour-based windows must be a multiple of 24 (for example '24 hours' or '168 hours').")
    days = amount // 24
    if days < 1 or days > 30:
        raise ValueError("window must resolve to between 1 and 30 days.")
    return days


@mcp.tool()
def list_clusters(vcenter_name: str | None = None, clusters: str | None = None, datacenters: str | None = None) -> str:
    """List vCenter clusters, optionally filtered by cluster IDs or datacenter IDs."""
    params = _clean_params({"clusters": split_csv(clusters), "datacenters": split_csv(datacenters)})
    return json_response(vcenter_get("/api/vcenter/cluster", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_cluster(cluster: str, vcenter_name: str | None = None) -> str:
    """Get details for a specific cluster."""
    return json_response(vcenter_get(f"/api/vcenter/cluster/{path_id(cluster)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_cluster_resource_utilization_ws(cluster: str, vcenter_name: str | None = None) -> str:
    """Get cluster CPU, memory, storage, and IOPS utilization via the vSphere Web Services API."""
    connection = resolve_vcenter(vcenter_name)
    return json_response(get_cluster_resource_utilization(cluster_id=cluster, **connection))


@mcp.tool()
def get_cluster_cpu_memory_utilization_period_ws(
    cluster: str,
    days: int = 5,
    vcenter_name: str | None = None,
) -> str:
    """Get time-bound cluster CPU and memory utilization via Web Services (default 5 days)."""
    connection = resolve_vcenter(vcenter_name)
    return json_response(
        get_cluster_cpu_memory_utilization_period(
            cluster_id=cluster,
            days=days,
            **connection,
        )
    )


@mcp.tool()
def get_cluster_cpu_memory_daily_rollup_ws(
    cluster: str,
    days: int = 5,
    vcenter_name: str | None = None,
) -> str:
    """Get daily rollups for cluster CPU/memory utilization via Web Services (default 5 days)."""
    connection = resolve_vcenter(vcenter_name)
    return json_response(
        get_cluster_cpu_memory_utilization_daily_rollup(
            cluster_id=cluster,
            days=days,
            **connection,
        )
    )


@mcp.tool()
def get_cluster_cpu_memory_utilization_window_ws(
    cluster: str,
    window: str = "24 hours",
    per_day: bool = False,
    vcenter_name: str | None = None,
) -> str:
    """Get cluster CPU/memory utilization for windows like '24 hours' or '4 days', optionally as per-day averages."""
    days = _window_to_days(window)
    connection = resolve_vcenter(vcenter_name)

    if per_day:
        result = get_cluster_cpu_memory_utilization_daily_rollup(
            cluster_id=cluster,
            days=days,
            **connection,
        )
    else:
        result = get_cluster_cpu_memory_utilization_period(
            cluster_id=cluster,
            days=days,
            **connection,
        )

    result["window_input"] = {
        "requested": window,
        "normalized_days": days,
        "per_day": per_day,
    }
    return json_response(result)


@mcp.tool()
def list_datacenters(vcenter_name: str | None = None, datacenters: str | None = None, folders: str | None = None) -> str:
    """List datacenters visible in vCenter."""
    params = _clean_params({"datacenters": split_csv(datacenters), "folders": split_csv(folders)})
    return json_response(vcenter_get("/api/vcenter/datacenter", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_datacenter(datacenter: str, vcenter_name: str | None = None) -> str:
    """Get datacenter details."""
    return json_response(vcenter_get(f"/api/vcenter/datacenter/{path_id(datacenter)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_datastores(
    vcenter_name: str | None = None,
    datastores: str | None = None,
    names: str | None = None,
    folders: str | None = None,
    datacenters: str | None = None,
) -> str:
    """List datastores with optional filters."""
    params = _clean_params(
        {
            "datastores": split_csv(datastores),
            "names": split_csv(names),
            "folders": split_csv(folders),
            "datacenters": split_csv(datacenters),
        }
    )
    return json_response(vcenter_get("/api/vcenter/datastore", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_datastore(datastore: str, vcenter_name: str | None = None) -> str:
    """Get datastore details."""
    return json_response(vcenter_get(f"/api/vcenter/datastore/{path_id(datastore)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_folders(
    vcenter_name: str | None = None,
    folders: str | None = None,
    names: str | None = None,
    types: str | None = None,
    datacenters: str | None = None,
) -> str:
    """List folders with optional filters."""
    params = _clean_params(
        {
            "folders": split_csv(folders),
            "names": split_csv(names),
            "type": split_csv(types),
            "datacenters": split_csv(datacenters),
        }
    )
    return json_response(vcenter_get("/api/vcenter/folder", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_hosts(
    vcenter_name: str | None = None,
    hosts: str | None = None,
    names: str | None = None,
    clusters: str | None = None,
    datacenters: str | None = None,
) -> str:
    """List ESXi hosts with optional filters via the vSphere Web Services API."""
    connection = resolve_vcenter(vcenter_name)
    return json_response(
        list_hosts_ws(
            hosts=split_csv(hosts),
            names=split_csv(names),
            clusters=split_csv(clusters),
            datacenters=split_csv(datacenters),
            **connection,
        )
    )


@mcp.tool()
def get_host(host: str, vcenter_name: str | None = None) -> str:
    """Get details for a specific physical ESXi host via the vSphere Web Services API."""
    connection = resolve_vcenter(vcenter_name)
    return json_response(get_host_detail(host_id=host, **connection))


@mcp.tool()
def list_networks(
    vcenter_name: str | None = None,
    networks: str | None = None,
    names: str | None = None,
    datacenters: str | None = None,
) -> str:
    """List networks and distributed port groups."""
    params = _clean_params(
        {
            "networks": split_csv(networks),
            "names": split_csv(names),
            "datacenters": split_csv(datacenters),
        }
    )
    return json_response(vcenter_get("/api/vcenter/network", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_resource_pools(
    vcenter_name: str | None = None,
    resource_pools: str | None = None,
    names: str | None = None,
    hosts: str | None = None,
    clusters: str | None = None,
) -> str:
    """List resource pools with optional filters."""
    params = _clean_params(
        {
            "resource_pools": split_csv(resource_pools),
            "names": split_csv(names),
            "hosts": split_csv(hosts),
            "clusters": split_csv(clusters),
        }
    )
    return json_response(vcenter_get("/api/vcenter/resource-pool", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_resource_pool(resource_pool: str, vcenter_name: str | None = None) -> str:
    """Get resource pool details."""
    return json_response(vcenter_get(f"/api/vcenter/resource-pool/{path_id(resource_pool)}", **resolve_vcenter(vcenter_name)))


@mcp.tool()
def list_vms(
    vcenter_name: str | None = None,
    vms: str | None = None,
    names: str | None = None,
    power_states: str | None = None,
    hosts: str | None = None,
    clusters: str | None = None,
    folders: str | None = None,
    datacenters: str | None = None,
) -> str:
    """List VMs with optional inventory filters."""
    params = _clean_params(
        {
            "vms": split_csv(vms),
            "names": split_csv(names),
            "power_states": split_csv(power_states),
            "hosts": split_csv(hosts),
            "clusters": split_csv(clusters),
            "folders": split_csv(folders),
            "datacenters": split_csv(datacenters),
        }
    )
    return json_response(vcenter_get("/api/vcenter/vm", params=params, **resolve_vcenter(vcenter_name)))


@mcp.tool()
def get_vm(vm: str, vcenter_name: str | None = None) -> str:
    """Get VM summary details."""
    return json_response(vcenter_get(f"/api/vcenter/vm/{path_id(vm)}", **resolve_vcenter(vcenter_name)))
