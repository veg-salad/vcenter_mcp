# vcenter-mcp — Available Tools

All tools are **read-only**. No changes are made to your vCenter environment.

vCenter tools accept an optional `vcenter_name` parameter resolved from `inventory.yaml`.  
When only one entry is defined the parameter is optional and that entry is selected automatically.  
Identifiers returned by `list_*` tools should be used as input to related `get_*` tools.

---

## Inventory

| Tool | Module | Description |
|---|---|---|
| `list_vcenters` | `tools/inventory.py` | List all registered vCenter instances from `inventory.yaml`. Returns `vcenters` entries (use name as `vcenter_name`). |
| `get_vcenter_inventory` | `tools/inventory.py` | Return configured vCenter entries and usage guidance for the `vcenter_name` parameter. |

---

## vCenter Inventory tools — REST API

### Clusters

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_clusters` | `tools/vcenter_inventory.py` | `vcenter_name`, `clusters`, `datacenters` | All clusters: cluster ID, name, HA/DRS state, inventory placement. |
| `get_cluster` | `tools/vcenter_inventory.py` | `cluster`*, `vcenter_name` | Full cluster detail: name, DRS, HA, distributed switch and inventory references. |
| `get_cluster_resource_utilization_ws` | `tools/vcenter_inventory.py` | `cluster`*, `vcenter_name` | Cluster utilization via the vSphere Web Services API: CPU, memory, storage usage and IOPS metrics from PerformanceManager. |
| `get_cluster_cpu_memory_utilization_period_ws` | `tools/vcenter_inventory.py` | `cluster`*, `days`, `vcenter_name` | Time-bound cluster CPU/memory utilization via Web Services (defaults to 5 days): avg/min/max usage and utilization percentages. |
| `get_cluster_cpu_memory_daily_rollup_ws` | `tools/vcenter_inventory.py` | `cluster`*, `days`, `vcenter_name` | Per-day CPU/memory utilization rollups over a time window (defaults to 5 days): daily avg/min/max and utilization percentages. |
| `get_cluster_cpu_memory_utilization_window_ws` | `tools/vcenter_inventory.py` | `cluster`*, `window`, `per_day`, `vcenter_name` | Natural-language window tool for CPU/memory utilization. Examples: `window="24 hours"`, `window="4 days"`, `window="7 days"` with `per_day=true` for per-day averages. Limits: `1-30` days; hour values must be multiples of 24. Output depends on vCenter PerformanceManager retention and may include fewer samples than requested. |

### Datacenters

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_datacenters` | `tools/vcenter_inventory.py` | `vcenter_name`, `datacenters`, `folders` | All datacenters: ID, name, and folder placement. |
| `get_datacenter` | `tools/vcenter_inventory.py` | `datacenter`*, `vcenter_name` | Full datacenter detail: name and parent folder reference. |

### Datastores

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_datastores` | `tools/vcenter_inventory.py` | `vcenter_name`, `datastores`, `names`, `folders`, `datacenters` | All datastores: ID, name, type, capacity, free space, and accessibility. |
| `get_datastore` | `tools/vcenter_inventory.py` | `datastore`*, `vcenter_name` | Full datastore detail: capacity, free space, type, and placement. |

### Folders

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_folders` | `tools/vcenter_inventory.py` | `vcenter_name`, `folders`, `names`, `types`, `datacenters` | All folders: ID, name, type, and datacenter placement. |

### Hosts

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_hosts` | `tools/vcenter_inventory.py` | `vcenter_name`, `hosts`, `names`, `clusters`, `datacenters` | All ESXi hosts via the vSphere Web Services API: ID, name, connection state, power state, and placement. |
| `get_host` | `tools/vcenter_inventory.py` | `host`*, `vcenter_name` | Full ESXi host detail via the vSphere Web Services API: vendor, model, CPU, memory, runtime state, version, and usage summary. |

### Networks

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_networks` | `tools/vcenter_inventory.py` | `vcenter_name`, `networks`, `names`, `datacenters` | All networks and distributed port groups: ID, name, type, and placement. |

### Resource Pools

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_resource_pools` | `tools/vcenter_inventory.py` | `vcenter_name`, `resource_pools`, `names`, `hosts`, `clusters` | All resource pools: ID, name, and cluster or host placement. |
| `get_resource_pool` | `tools/vcenter_inventory.py` | `resource_pool`*, `vcenter_name` | Full resource pool detail: name and parent inventory placement. |

### Virtual Machines

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_vms` | `tools/vcenter_inventory.py` | `vcenter_name`, `vms`, `names`, `power_states`, `hosts`, `clusters`, `folders`, `datacenters` | All VMs: ID, name, power state, guest OS, CPU, memory, and placement. |
| `get_vm` | `tools/vcenter_inventory.py` | `vm`*, `vcenter_name` | Full VM summary: name, power state, guest OS, hardware version, placement, and boot status. |

## VM Detail tools — REST API

### Guest

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `get_vm_guest_identity` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Guest identity: hostname, family, and other VMware Tools guest properties. |
| `list_vm_guest_local_filesystems` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Guest local filesystems: mount points, capacity, and free space. |
| `list_vm_guest_network_interfaces` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Guest network interfaces: MAC, IP addressing, and connectivity details. |

### Hardware

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `get_vm_hardware` | `tools/vm_details.py` | `vm`*, `vcenter_name` | VM hardware summary: version, upgrade policy, and device inventory overview. |
| `get_vm_boot` | `tools/vm_details.py` | `vm`*, `vcenter_name` | VM boot configuration: firmware, boot delay, retry, and order settings. |
| `get_vm_cpu` | `tools/vm_details.py` | `vm`*, `vcenter_name` | VM CPU configuration: count, cores per socket, hot-add, and hot-remove settings. |
| `get_vm_memory` | `tools/vm_details.py` | `vm`*, `vcenter_name` | VM memory configuration: size and hot-add setting. |
| `list_vm_disks` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Virtual disks attached to a VM: disk IDs, type, capacity, and backing. |
| `get_vm_disk` | `tools/vm_details.py` | `vm`*, `disk`*, `vcenter_name` | Full detail for a specific virtual disk. |
| `list_vm_nics` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Virtual NICs attached to a VM: NIC IDs, backing, MAC address, and connection state. |
| `get_vm_nic` | `tools/vm_details.py` | `vm`*, `nic`*, `vcenter_name` | Full detail for a specific virtual NIC. |

---

## Appliance tools — REST API

### System

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `get_appliance_version` | `tools/appliance.py` | `vcenter_name` | Appliance version, build, product, and release information. |
| `get_appliance_time` | `tools/appliance.py` | `vcenter_name` | Current appliance time and synchronization settings. |

---

`*` = required parameter
