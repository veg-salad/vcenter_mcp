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
| `get_cluster_evc_mode` | `tools/vcenter_inventory.py` | `cluster`*, `vcenter_name` | EVC mode configured on the target cluster. |

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
| `get_datastore_default_policy` | `tools/vcenter_inventory.py` | `datastore`*, `vcenter_name` | Default storage policy associated with the datastore. |

### Folders

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_folders` | `tools/vcenter_inventory.py` | `vcenter_name`, `folders`, `names`, `types`, `datacenters` | All folders: ID, name, type, and datacenter placement. |
| `get_folder` | `tools/vcenter_inventory.py` | `folder`*, `vcenter_name` | Full folder detail: name, type, and parent inventory reference. |

### Hosts

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_hosts` | `tools/vcenter_inventory.py` | `vcenter_name`, `hosts`, `names`, `clusters`, `datacenters` | All ESXi hosts: ID, name, connection state, power state, and placement. |
| `get_host` | `tools/vcenter_inventory.py` | `host`*, `vcenter_name` | Full ESXi host detail: name, connection state, maintenance state, and placement. |

### Networks

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_networks` | `tools/vcenter_inventory.py` | `vcenter_name`, `networks`, `names`, `datacenters` | All networks and distributed port groups: ID, name, type, and placement. |
| `get_network` | `tools/vcenter_inventory.py` | `network`*, `vcenter_name` | Full network detail: name, type, and datacenter reference. |

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
| `get_vm_power` | `tools/vcenter_inventory.py` | `vm`*, `vcenter_name` | Current VM power state. |

### Guest Customization

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_guest_customization_specs` | `tools/vcenter_inventory.py` | `vcenter_name` | All guest customization specifications available in vCenter. |
| `get_guest_customization_spec` | `tools/vcenter_inventory.py` | `name`*, `vcenter_name` | Full guest customization specification by name. |

### Topology

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_topology_nodes` | `tools/vcenter_inventory.py` | `vcenter_name` | All vCenter topology nodes visible to the appliance. |
| `get_topology_replication_status` | `tools/vcenter_inventory.py` | `vcenter_name` | Replication status for the vCenter topology domain. |

---

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
| `list_vm_cdroms` | `tools/vm_details.py` | `vm`*, `vcenter_name` | CD-ROM devices attached to a VM. |
| `get_vm_cdrom` | `tools/vm_details.py` | `vm`*, `cdrom`*, `vcenter_name` | Full detail for a specific CD-ROM device. |
| `list_vm_floppies` | `tools/vm_details.py` | `vm`*, `vcenter_name` | Floppy devices attached to a VM. |
| `get_vm_floppy` | `tools/vm_details.py` | `vm`*, `floppy`*, `vcenter_name` | Full detail for a specific floppy device. |
| `list_vm_scsi_adapters` | `tools/vm_details.py` | `vm`*, `vcenter_name` | SCSI adapters attached to a VM. |
| `get_vm_scsi_adapter` | `tools/vm_details.py` | `vm`*, `adapter`*, `vcenter_name` | Full detail for a specific SCSI adapter. |
| `list_vm_sata_adapters` | `tools/vm_details.py` | `vm`*, `vcenter_name` | SATA adapters attached to a VM. |
| `get_vm_sata_adapter` | `tools/vm_details.py` | `vm`*, `adapter`*, `vcenter_name` | Full detail for a specific SATA adapter. |
| `list_vm_nvme_adapters` | `tools/vm_details.py` | `vm`*, `vcenter_name` | NVMe adapters attached to a VM. |
| `get_vm_nvme_adapter` | `tools/vm_details.py` | `vm`*, `adapter`*, `vcenter_name` | Full detail for a specific NVMe adapter. |

---

## Tagging tools — REST API

### Categories

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_tag_categories` | `tools/tagging.py` | `vcenter_name` | All tag category identifiers registered in vCenter. |
| `get_tag_category` | `tools/tagging.py` | `category_id`*, `vcenter_name` | Full tag category detail: name, description, cardinality, associable types. |
| `list_used_tag_categories` | `tools/tagging.py` | `used_by_entity`*, `vcenter_name` | Category identifiers currently used by a given subscriber entity. |

### Tags

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_tags` | `tools/tagging.py` | `vcenter_name` | All tag identifiers registered in vCenter. |
| `get_tag` | `tools/tagging.py` | `tag_id`*, `vcenter_name` | Full tag detail: name, description, and category association. |
| `list_attached_tags` | `tools/tagging.py` | `object_type`*, `object_id`*, `vcenter_name` | Tags attached to a given vCenter inventory object. |
| `list_attached_objects` | `tools/tagging.py` | `tag_id`*, `vcenter_name` | Inventory objects currently attached to a given tag. |

---

## Appliance tools — REST API

### System

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `get_appliance_version` | `tools/appliance.py` | `vcenter_name` | Appliance version, build, product, and release information. |
| `get_appliance_time` | `tools/appliance.py` | `vcenter_name` | Current appliance time and synchronization settings. |
| `get_appliance_timezone` | `tools/appliance.py` | `vcenter_name` | Appliance timezone configuration. |
| `get_appliance_ntp` | `tools/appliance.py` | `vcenter_name` | Appliance NTP configuration. |
| `get_appliance_update` | `tools/appliance.py` | `vcenter_name` | Appliance update configuration and current update source state. |
| `get_appliance_update_pending` | `tools/appliance.py` | `vcenter_name` | Pending update information currently visible to the appliance. |

### Services

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_appliance_services` | `tools/appliance.py` | `vcenter_name` | All appliance services: name, startup type, and current state. |
| `get_appliance_service` | `tools/appliance.py` | `service`*, `vcenter_name` | Full detail for a specific appliance service. |

### Health

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `get_appliance_health` | `tools/appliance.py` | `vcenter_name` | Overall appliance health status. |
| `get_appliance_health_cpu` | `tools/appliance.py` | `vcenter_name` | Appliance CPU or load health status. |
| `get_appliance_health_memory` | `tools/appliance.py` | `vcenter_name` | Appliance memory health status. |
| `get_appliance_health_storage` | `tools/appliance.py` | `vcenter_name` | Appliance storage health status. |
| `get_appliance_health_swap` | `tools/appliance.py` | `vcenter_name` | Appliance swap health status. |

### Networking

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_appliance_network_interfaces` | `tools/appliance.py` | `vcenter_name` | All appliance network interfaces: name, MAC, addressing, and state. |
| `get_appliance_network_interface` | `tools/appliance.py` | `interface`*, `vcenter_name` | Full detail for a specific appliance network interface. |

### Local Accounts

| Tool | Module | Parameters | Description |
|---|---|---|---|
| `list_appliance_local_accounts` | `tools/appliance.py` | `vcenter_name` | All appliance local accounts visible through the API. |
| `get_appliance_local_account` | `tools/appliance.py` | `username`*, `vcenter_name` | Full detail for a specific appliance local account. |

---

`*` = required parameter
