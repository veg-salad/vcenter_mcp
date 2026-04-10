"""vSphere Web Services helpers used where REST lacks host detail coverage."""

from __future__ import annotations

import ssl
from typing import Any

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim


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
