"""CLI entry point for vcenter-mcp."""

from __future__ import annotations

import getpass
import json
import os
import subprocess
import sys

import yaml

from vcenter_mcp.credentials import store_vcenter_credentials

MIN_PYTHON = (3, 10)


def _ok(message: str) -> None:
    print(f"  [OK]  {message}")


def _warn(message: str) -> None:
    print(f"  [!]   {message}")


def _fail(message: str) -> None:
    print(f"\n  [ERR] {message}")
    raise SystemExit(1)


def _inventory_path() -> str:
    return os.path.join(os.getcwd(), "inventory.yaml")


def _load_inventory() -> dict:
    path = _inventory_path()
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _write_inventory(data: dict) -> None:
    with open(_inventory_path(), "w", encoding="utf-8") as handle:
        yaml.dump(data, handle, default_flow_style=False, sort_keys=False)


def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        _fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.")
    _ok(f"Python {sys.version.split()[0]}")


def _install_dependencies() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "mcp[cli]>=1.6.0",
            "requests>=2.31.0",
            "pyyaml>=6.0.0",
            "keyring>=24.0.0",
            "keyrings.alt>=5.0.0",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _fail(result.stderr.strip() or "Dependency installation failed.")
    _ok("Dependencies verified")


def _configure_inventory() -> None:
    data = _load_inventory()
    vcenters = list(data.get("vcenters", []))
    print("\n  Register vCenter Server Appliance endpoints. Leave the name blank to finish.\n")
    while True:
        name = input("    vCenter name [blank to finish]: ").strip()
        if not name:
            break
        if any(entry["name"].lower() == name.lower() for entry in vcenters):
            _warn(f"'{name}' already exists in inventory.yaml")
            continue
        host = input(f"    Host/IP for '{name}': ").strip()
        if not host:
            _warn("Host is required. Skipping entry.")
            continue
        port_raw = input("    HTTPS port [443]: ").strip() or "443"
        verify_ssl = input("    Verify SSL certificate? (yes/no) [no]: ").strip().lower() == "yes"
        vcenters.append(
            {"name": name, "host": host, "port": int(port_raw), "verify_ssl": verify_ssl}
        )
        _ok(f"Added {name} ({host}:{port_raw})")

    if vcenters:
        data["vcenters"] = vcenters
        _write_inventory(data)
        _ok(f"inventory.yaml updated with {len(vcenters)} vCenter entry(s)")


def _configure_credentials() -> None:
    data = _load_inventory()
    vcenters = data.get("vcenters", [])
    if not vcenters:
        _warn("No vCenters found in inventory.yaml, skipping credential setup.")
        return

    print("\n  Store credentials securely in the OS keyring.\n")
    default_username = input("    Default username [Enter to skip]: ").strip()
    if default_username:
        default_password = getpass.getpass("    Default password: ")
        default_verify_ssl = input("    Default verify SSL? (yes/no) [no]: ").strip().lower() == "yes"
        store_vcenter_credentials("default", default_username, default_password, default_verify_ssl)
        _ok("Stored default vCenter credentials")

    for entry in vcenters:
        override = input(f"    Override credentials for '{entry['name']}'? (yes/no) [no]: ").strip().lower()
        if override != "yes":
            continue
        username = input("      Username: ").strip()
        if not username:
            _warn("      Username is required to store an override.")
            continue
        password = getpass.getpass("      Password: ")
        verify_ssl = input("      Verify SSL? (yes/no) [no]: ").strip().lower() == "yes"
        store_vcenter_credentials(entry["name"], username, password, verify_ssl)
        _ok(f"Stored credentials for {entry['name']}")


def _write_mcp_json() -> None:
    vscode_dir = os.path.join(os.getcwd(), ".vscode")
    mcp_path = os.path.join(vscode_dir, "mcp.json")
    servers = {}
    if os.path.exists(mcp_path):
        try:
            with open(mcp_path, encoding="utf-8") as handle:
                servers = json.load(handle).get("servers", {})
        except Exception:
            servers = {}

    servers["vcenter-mcp"] = {
        "type": "stdio",
        "command": "vcenter-mcp",
        "env": {"VCENTER_MCP_INVENTORY": "${workspaceFolder}/inventory.yaml"},
    }
    os.makedirs(vscode_dir, exist_ok=True)
    with open(mcp_path, "w", encoding="utf-8") as handle:
        json.dump({"servers": servers}, handle, indent=2)
    _ok(".vscode/mcp.json written")


def configure() -> None:
    print("\nvcenter-mcp setup\n" + "-" * 32)
    _check_python()
    _install_dependencies()
    _configure_inventory()
    _configure_credentials()
    _write_mcp_json()


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "configure":
        configure()
        return

    if args and args[0] in {"-h", "--help"}:
        print("Usage: vcenter-mcp [configure]")
        return

    import vcenter_mcp.tools.appliance  # noqa: F401
    import vcenter_mcp.tools.inventory  # noqa: F401
    import vcenter_mcp.tools.tagging  # noqa: F401
    import vcenter_mcp.tools.vcenter_inventory  # noqa: F401
    import vcenter_mcp.tools.vm_details  # noqa: F401

    from vcenter_mcp.app import mcp

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
