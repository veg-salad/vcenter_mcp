# vcenter-mcp

`vcenter-mcp` is a read-only Model Context Protocol server for Broadcom VCF and VMware vCenter Server Appliance environments.

It is designed for safe community use:

- Read-only tool coverage for common vCenter and appliance REST resources
- Keyring-backed credential storage
- Inventory-based multi-vCenter selection
- Session-based authentication with bounded timeouts
- No mutation tools and no passthrough arbitrary write methods

## Current tool coverage

- Inventory and connection discovery
- Core vCenter inventory: clusters, datacenters, datastores, folders, hosts, networks, resource pools, VMs
- VM guest and hardware inspection
- Guest customization specifications
- Tagging inventory and associations
- vCenter appliance version, health, networking, services, system time, update, and local accounts visibility

## Quick start

```powershell
python -m pip install -e .
vcenter-mcp configure
vcenter-mcp
```

## Inventory

Create `inventory.yaml` in the workspace or set `VCENTER_MCP_INVENTORY`:

```yaml
vcenters:
  - name: lab
    host: vcsa.lab.local
    port: 443
    verify_ssl: false
```

## Credentials

The setup wizard stores credentials in the OS keyring under the `vcenter-mcp` service.

Supported fallback environment variables:

- `VCENTER_USERNAME`
- `VCENTER_PASSWORD`
- `VCENTER_VERIFY_SSL`

## Publishing

When you are ready to publish:

```powershell
python -m build
python -m twine upload dist/*
```
