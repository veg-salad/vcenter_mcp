"""vSphere Web Services helpers used where REST lacks host detail coverage."""

from __future__ import annotations

import ssl
from datetime import datetime, timedelta, timezone
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


def _percentage(used: int | float | None, capacity: int | float | None) -> float | None:
    if used is None or capacity is None or capacity <= 0:
        return None
    return round((float(used) / float(capacity)) * 100.0, 2)


def _find_cluster(content: vim.ServiceInstanceContent, cluster_id: str) -> vim.ClusterComputeResource | None:
    view = content.viewManager.CreateContainerView(content.rootFolder, [vim.ClusterComputeResource], True)
    try:
        for cluster in view.view:
            if cluster._moId == cluster_id:
                return cluster
    finally:
        view.Destroy()
    return None


def _pick_historical_interval_seconds(perf_manager: vim.PerformanceManager) -> int | None:
    intervals = [interval for interval in getattr(perf_manager, "historicalInterval", []) if getattr(interval, "enabled", False)]
    if not intervals:
        return None
    return min(interval.samplingPeriod for interval in intervals)


def _counter_id(
    perf_manager: vim.PerformanceManager,
    available_counter_ids: set[int],
    *,
    group: str,
    name: str,
    rollup: str,
) -> tuple[int, str] | None:
    for counter in perf_manager.perfCounter:
        if (
            counter.groupInfo.key == group
            and counter.nameInfo.key == name
            and str(counter.rollupType).lower() == rollup.lower()
            and counter.key in available_counter_ids
        ):
            return counter.key, str(counter.unitInfo.key)
    return None


def _series_summary(values: list[float], capacity: int | float | None) -> dict[str, Any]:
    if not values:
        return {
            "samples": 0,
            "avg": None,
            "min": None,
            "max": None,
            "avg_utilization_pct": None,
            "min_utilization_pct": None,
            "max_utilization_pct": None,
        }

    avg_value = sum(values) / len(values)
    min_value = min(values)
    max_value = max(values)
    return {
        "samples": len(values),
        "avg": round(avg_value, 2),
        "min": round(min_value, 2),
        "max": round(max_value, 2),
        "avg_utilization_pct": _percentage(avg_value, capacity),
        "min_utilization_pct": _percentage(min_value, capacity),
        "max_utilization_pct": _percentage(max_value, capacity),
    }


def _daily_rollups(samples: list[tuple[datetime, float]], capacity: int | float | None) -> list[dict[str, Any]]:
    by_day: dict[str, list[float]] = {}
    for timestamp, value in samples:
        day = timestamp.astimezone(timezone.utc).date().isoformat()
        by_day.setdefault(day, []).append(value)

    results: list[dict[str, Any]] = []
    for day in sorted(by_day.keys()):
        values = by_day[day]
        stats = _series_summary(values, capacity)
        results.append(
            {
                "date": day,
                "samples": stats["samples"],
                "avg": stats["avg"],
                "min": stats["min"],
                "max": stats["max"],
                "avg_utilization_pct": stats["avg_utilization_pct"],
                "min_utilization_pct": stats["min_utilization_pct"],
                "max_utilization_pct": stats["max_utilization_pct"],
            }
        )
    return results


def _query_cluster_iops(cluster: vim.ClusterComputeResource, perf_manager: vim.PerformanceManager) -> dict[str, Any]:
    provider = perf_manager.QueryPerfProviderSummary(entity=cluster)
    interval_id = provider.refreshRate if provider is not None and provider.currentSupported else None

    if interval_id is not None and interval_id > 0:
        available_metrics = perf_manager.QueryAvailablePerfMetric(entity=cluster, intervalId=interval_id)
    else:
        available_metrics = perf_manager.QueryAvailablePerfMetric(entity=cluster)

    available_counter_ids = {metric.counterId for metric in available_metrics}
    if not available_counter_ids:
        return {
            "read_per_second": None,
            "write_per_second": None,
            "total_per_second": None,
            "source_counters": {},
            "note": "No available performance counters were reported for this cluster.",
        }

    counter_index: dict[tuple[str, str], tuple[int, str]] = {}
    for counter in perf_manager.perfCounter:
        key = (counter.groupInfo.key, counter.nameInfo.key)
        full_name = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}"
        counter_index[key] = (counter.key, full_name)

    read_candidates = [
        ("datastore", "numberReadAveraged"),
        ("disk", "numberReadAveraged"),
    ]
    write_candidates = [
        ("datastore", "numberWriteAveraged"),
        ("disk", "numberWriteAveraged"),
    ]

    def pick_counter(candidates: list[tuple[str, str]]) -> tuple[int, str] | None:
        for candidate in candidates:
            entry = counter_index.get(candidate)
            if entry and entry[0] in available_counter_ids:
                return entry
        return None

    selected_read = pick_counter(read_candidates)
    selected_write = pick_counter(write_candidates)
    selected = [item for item in [selected_read, selected_write] if item is not None]

    if not selected:
        return {
            "read_per_second": None,
            "write_per_second": None,
            "total_per_second": None,
            "source_counters": {},
            "note": "Cluster IOPS counters were not available via PerformanceManager for this environment.",
        }

    metric_ids = [vim.PerformanceManager.MetricId(counterId=counter_id, instance="*") for counter_id, _ in selected]

    query_spec_kwargs: dict[str, Any] = {
        "entity": cluster,
        "metricId": metric_ids,
        "maxSample": 1,
    }
    if interval_id is not None and interval_id > 0:
        query_spec_kwargs["intervalId"] = interval_id

    query_spec = vim.PerformanceManager.QuerySpec(**query_spec_kwargs)
    metrics = perf_manager.QueryPerf(querySpec=[query_spec])

    sums_by_counter: dict[int, float] = {}
    for entity_metric in metrics:
        for value in getattr(entity_metric, "value", []):
            samples = getattr(value, "value", [])
            if not samples:
                continue
            latest = float(samples[-1])
            sums_by_counter[value.id.counterId] = sums_by_counter.get(value.id.counterId, 0.0) + latest

    read_value = sums_by_counter.get(selected_read[0]) if selected_read else None
    write_value = sums_by_counter.get(selected_write[0]) if selected_write else None
    total_value = None
    if read_value is not None or write_value is not None:
        total_value = (read_value or 0.0) + (write_value or 0.0)

    return {
        "read_per_second": None if read_value is None else round(read_value, 2),
        "write_per_second": None if write_value is None else round(write_value, 2),
        "total_per_second": None if total_value is None else round(total_value, 2),
        "source_counters": {
            "read": selected_read[1] if selected_read else None,
            "write": selected_write[1] if selected_write else None,
        },
    }


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


def get_cluster_resource_utilization(
    *,
    cluster_id: str,
    host: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> dict[str, Any]:
    """Return cluster CPU, memory, storage, and IOPS utilization through Web Services."""
    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    try:
        content = service_instance.RetrieveContent()
        cluster = _find_cluster(content, cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster '{cluster_id}' was not found through the vSphere Web Services API.")

        usage = cluster.GetResourceUsage()
        iops = _query_cluster_iops(cluster, content.perfManager)

        cpu_capacity_mhz = usage.cpuCapacityMHz
        cpu_used_mhz = usage.cpuUsedMHz
        mem_capacity_mb = usage.memCapacityMB
        mem_used_mb = usage.memUsedMB
        storage_capacity_mb = usage.storageCapacityMB
        storage_used_mb = usage.storageUsedMB

        return {
            "cluster": cluster._moId,
            "name": cluster.name,
            "cpu": {
                "capacity_mhz": cpu_capacity_mhz,
                "used_mhz": cpu_used_mhz,
                "utilization_pct": _percentage(cpu_used_mhz, cpu_capacity_mhz),
            },
            "memory": {
                "capacity_mb": mem_capacity_mb,
                "used_mb": mem_used_mb,
                "utilization_pct": _percentage(mem_used_mb, mem_capacity_mb),
            },
            "storage": {
                "capacity_mb": storage_capacity_mb,
                "used_mb": storage_used_mb,
                "utilization_pct": _percentage(storage_used_mb, storage_capacity_mb),
            },
            "iops": iops,
        }
    finally:
        try:
            Disconnect(service_instance)
        except Exception:
            pass


def get_cluster_cpu_memory_utilization_period(
    *,
    cluster_id: str,
    days: int,
    host: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> dict[str, Any]:
    """Return cluster CPU and memory utilization for a historical time window."""
    if days < 1 or days > 30:
        raise ValueError("days must be between 1 and 30.")

    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    try:
        content = service_instance.RetrieveContent()
        cluster = _find_cluster(content, cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster '{cluster_id}' was not found through the vSphere Web Services API.")

        perf_manager = content.perfManager
        interval_seconds = _pick_historical_interval_seconds(perf_manager)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        available_metrics = perf_manager.QueryAvailablePerfMetric(
            entity=cluster,
            beginTime=start_time,
            endTime=end_time,
            intervalId=interval_seconds,
        )
        available_counter_ids = {metric.counterId for metric in available_metrics}

        cpu_counter = _counter_id(
            perf_manager,
            available_counter_ids,
            group="cpu",
            name="usagemhz",
            rollup="average",
        )
        mem_counter = _counter_id(
            perf_manager,
            available_counter_ids,
            group="mem",
            name="consumed",
            rollup="average",
        )

        cpu_counter_id = cpu_counter[0] if cpu_counter else None
        mem_counter_id = mem_counter[0] if mem_counter else None
        mem_counter_unit = mem_counter[1] if mem_counter else None

        selected_counter_ids = [counter_id for counter_id in [cpu_counter_id, mem_counter_id] if counter_id is not None]
        if not selected_counter_ids:
            return {
                "cluster": cluster._moId,
                "name": cluster.name,
                "window": {
                    "days": days,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "interval_seconds": interval_seconds,
                },
                "cpu": _series_summary([], None),
                "memory": _series_summary([], None),
                "note": "No compatible CPU/memory historical counters were available for this cluster in the selected time window.",
            }

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=cluster,
            metricId=[vim.PerformanceManager.MetricId(counterId=counter_id, instance="*") for counter_id in selected_counter_ids],
            intervalId=interval_seconds,
            startTime=start_time,
            endTime=end_time,
        )
        metrics = perf_manager.QueryPerf(querySpec=[query_spec])

        cpu_samples: list[float] = []
        mem_samples: list[float] = []
        for entity_metric in metrics:
            for value in getattr(entity_metric, "value", []):
                series = [float(sample) for sample in getattr(value, "value", [])]
                if value.id.counterId == cpu_counter_id:
                    cpu_samples.extend(series)
                elif value.id.counterId == mem_counter_id:
                    mem_samples.extend(series)

        if mem_counter_unit in {"kiloBytes", "KB"}:
            mem_samples = [sample / 1024.0 for sample in mem_samples]

        usage = cluster.GetResourceUsage()
        cpu_capacity_mhz = usage.cpuCapacityMHz
        mem_capacity_mb = usage.memCapacityMB

        return {
            "cluster": cluster._moId,
            "name": cluster.name,
            "window": {
                "days": days,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "interval_seconds": interval_seconds,
            },
            "cpu": {
                "unit": "mhz",
                "capacity_mhz": cpu_capacity_mhz,
                **_series_summary(cpu_samples, cpu_capacity_mhz),
            },
            "memory": {
                "unit": "mb",
                "capacity_mb": mem_capacity_mb,
                **_series_summary(mem_samples, mem_capacity_mb),
            },
            "source_counters": {
                "cpu": "cpu.usagemhz.average" if cpu_counter_id is not None else None,
                "memory": "mem.consumed.average" if mem_counter_id is not None else None,
                "memory_counter_unit": mem_counter_unit,
            },
        }
    finally:
        try:
            Disconnect(service_instance)
        except Exception:
            pass


def get_cluster_cpu_memory_utilization_daily_rollup(
    *,
    cluster_id: str,
    days: int,
    host: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> dict[str, Any]:
    """Return cluster CPU and memory utilization daily rollups over a historical window."""
    if days < 1 or days > 30:
        raise ValueError("days must be between 1 and 30.")

    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    try:
        content = service_instance.RetrieveContent()
        cluster = _find_cluster(content, cluster_id)
        if cluster is None:
            raise ValueError(f"Cluster '{cluster_id}' was not found through the vSphere Web Services API.")

        perf_manager = content.perfManager
        interval_seconds = _pick_historical_interval_seconds(perf_manager)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        available_metrics = perf_manager.QueryAvailablePerfMetric(
            entity=cluster,
            beginTime=start_time,
            endTime=end_time,
            intervalId=interval_seconds,
        )
        available_counter_ids = {metric.counterId for metric in available_metrics}

        cpu_counter = _counter_id(
            perf_manager,
            available_counter_ids,
            group="cpu",
            name="usagemhz",
            rollup="average",
        )
        mem_counter = _counter_id(
            perf_manager,
            available_counter_ids,
            group="mem",
            name="consumed",
            rollup="average",
        )

        cpu_counter_id = cpu_counter[0] if cpu_counter else None
        mem_counter_id = mem_counter[0] if mem_counter else None
        mem_counter_unit = mem_counter[1] if mem_counter else None

        selected_counter_ids = [counter_id for counter_id in [cpu_counter_id, mem_counter_id] if counter_id is not None]
        if not selected_counter_ids:
            return {
                "cluster": cluster._moId,
                "name": cluster.name,
                "window": {
                    "days": days,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "interval_seconds": interval_seconds,
                },
                "cpu_daily": [],
                "memory_daily": [],
                "note": "No compatible CPU/memory historical counters were available for this cluster in the selected time window.",
            }

        query_spec = vim.PerformanceManager.QuerySpec(
            entity=cluster,
            metricId=[vim.PerformanceManager.MetricId(counterId=counter_id, instance="*") for counter_id in selected_counter_ids],
            intervalId=interval_seconds,
            startTime=start_time,
            endTime=end_time,
        )
        metrics = perf_manager.QueryPerf(querySpec=[query_spec])

        cpu_timestamped: list[tuple[datetime, float]] = []
        mem_timestamped: list[tuple[datetime, float]] = []
        for entity_metric in metrics:
            sample_infos = list(getattr(entity_metric, "sampleInfo", []))
            for value in getattr(entity_metric, "value", []):
                series = [float(sample) for sample in getattr(value, "value", [])]
                if sample_infos:
                    timestamps = [sample_infos[index].timestamp for index in range(min(len(sample_infos), len(series)))]
                    series_values = series[: len(timestamps)]
                elif interval_seconds is not None and interval_seconds > 0 and series:
                    timestamps = [
                        start_time + timedelta(seconds=interval_seconds * index) for index in range(len(series))
                    ]
                    series_values = series
                else:
                    timestamps = []
                    series_values = []

                if value.id.counterId == cpu_counter_id:
                    cpu_timestamped.extend(
                        (timestamps[index], series_values[index]) for index in range(len(timestamps))
                    )
                elif value.id.counterId == mem_counter_id:
                    mem_values = series_values
                    if mem_counter_unit in {"kiloBytes", "KB"}:
                        mem_values = [sample / 1024.0 for sample in mem_values]
                    mem_timestamped.extend(
                        (timestamps[index], mem_values[index]) for index in range(len(timestamps))
                    )

        usage = cluster.GetResourceUsage()
        cpu_capacity_mhz = usage.cpuCapacityMHz
        mem_capacity_mb = usage.memCapacityMB

        return {
            "cluster": cluster._moId,
            "name": cluster.name,
            "window": {
                "days": days,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "interval_seconds": interval_seconds,
            },
            "cpu": {
                "unit": "mhz",
                "capacity_mhz": cpu_capacity_mhz,
                **_series_summary([value for _, value in cpu_timestamped], cpu_capacity_mhz),
            },
            "memory": {
                "unit": "mb",
                "capacity_mb": mem_capacity_mb,
                **_series_summary([value for _, value in mem_timestamped], mem_capacity_mb),
            },
            "cpu_daily": _daily_rollups(cpu_timestamped, cpu_capacity_mhz),
            "memory_daily": _daily_rollups(mem_timestamped, mem_capacity_mb),
            "source_counters": {
                "cpu": "cpu.usagemhz.average" if cpu_counter_id is not None else None,
                "memory": "mem.consumed.average" if mem_counter_id is not None else None,
                "memory_counter_unit": mem_counter_unit,
            },
        }
    finally:
        try:
            Disconnect(service_instance)
        except Exception:
            pass
