"""vSphere Web Services helpers used where REST lacks host detail coverage."""

from __future__ import annotations

import ssl
from typing import Any

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim


def _to_filter_set(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    filtered = {value.strip().lower() for value in values if value and value.strip()}
    return filtered or None


def _resolve_datacenter_name(host_system: vim.HostSystem) -> str | None:
    current = host_system.parent
    while current is not None:
        if isinstance(current, vim.Datacenter):
            return current.name
        current = getattr(current, "parent", None)
    return None


def list_hosts_ws(
    *,
    host: str,
    username: str,
    password: str,
    verify_ssl: bool,
    hosts: list[str] | None = None,
    names: list[str] | None = None,
    clusters: list[str] | None = None,
    datacenters: list[str] | None = None,
) -> list[dict[str, Any]]:
    """List ESXi hosts via vSphere Web Services with optional filters."""
    host_filter = _to_filter_set(hosts)
    name_filter = _to_filter_set(names)
    cluster_filter = _to_filter_set(clusters)
    datacenter_filter = _to_filter_set(datacenters)

    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    try:
        content = service_instance.RetrieveContent()
        view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        try:
            results: list[dict[str, Any]] = []
            for host_system in view.view:
                summary = host_system.summary
                if summary.host is None:
                    continue

                host_id = summary.host._moId
                config = summary.config
                runtime = summary.runtime
                parent = host_system.parent
                cluster_name = parent.name if parent is not None else None
                datacenter_name = _resolve_datacenter_name(host_system)

                if host_filter and host_id.lower() not in host_filter:
                    continue
                if name_filter and config.name.lower() not in name_filter:
                    continue
                if cluster_filter and (not cluster_name or cluster_name.lower() not in cluster_filter):
                    continue
                if datacenter_filter and (not datacenter_name or datacenter_name.lower() not in datacenter_filter):
                    continue

                results.append(
                    {
                        "host": host_id,
                        "name": config.name,
                        "connection_state": str(runtime.connectionState),
                        "power_state": str(runtime.powerState),
                        "maintenance_mode": bool(runtime.inMaintenanceMode),
                        "cluster": cluster_name,
                        "datacenter": datacenter_name,
                    }
                )

            return sorted(results, key=lambda item: item["name"].lower())
        finally:
            view.Destroy()
    finally:
        try:
            Disconnect(service_instance)
        except Exception:
            pass


def get_host_detail(*, host_id: str, host: str, username: str, password: str, verify_ssl: bool) -> dict[str, Any]:
    """Return rich HostSystem detail for a physical ESXi host via vCenter."""
    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    try:
        content = service_instance.RetrieveContent()
        view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        try:
            for host_system in view.view:
                summary = host_system.summary
                if summary.host is None or summary.host._moId != host_id:
                    continue

                quick = summary.quickStats
                runtime = summary.runtime
                hardware = summary.hardware
                config = summary.config
                return {
                    "host": summary.host._moId,
                    "name": config.name,
                    "connection_state": str(runtime.connectionState),
                    "power_state": str(runtime.powerState),
                    "maintenance_mode": bool(runtime.inMaintenanceMode),
                    "vendor": hardware.vendor,
                    "model": hardware.model,
                    "cpu_model": hardware.cpuModel,
                    "cpu_packages": hardware.numCpuPkgs,
                    "cpu_cores": hardware.numCpuCores,
                    "cpu_threads": hardware.numCpuThreads,
                    "memory_size_bytes": hardware.memorySize,
                    "product_name": config.product.fullName,
                    "product_version": config.product.version,
                    "build": config.product.build,
                    "management_server_ip": summary.managementServerIp,
                    "overall_status": str(summary.overallStatus),
                    "reboot_required": bool(summary.rebootRequired),
                    "boot_time": runtime.bootTime,
                    "standby_mode": runtime.standbyMode,
                    "in_quarantine_mode": bool(runtime.inQuarantineMode),
                    "cpu_usage_mhz": quick.overallCpuUsage,
                    "memory_usage_mib": quick.overallMemoryUsage,
                }
        finally:
            view.Destroy()
    finally:
        try:
            Disconnect(service_instance)
        except Exception:
            pass

    raise ValueError(f"Host '{host_id}' was not found through the vSphere Web Services API.")
