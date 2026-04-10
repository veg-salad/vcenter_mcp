"""Inventory loading and shared helpers."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote

import yaml

from vcenter_mcp.credentials import get_vcenter_credentials


def _find_inventory() -> str | None:
    env_path = os.environ.get("VCENTER_MCP_INVENTORY", "")
    if env_path and os.path.exists(env_path):
        return env_path

    cwd_path = os.path.join(os.getcwd(), "inventory.yaml")
    if os.path.exists(cwd_path):
        return cwd_path

    home_path = os.path.join(os.path.expanduser("~"), ".vcenter_mcp", "inventory.yaml")
    if os.path.exists(home_path):
        return home_path

    repo_rel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "inventory.yaml")
    repo_abs = os.path.normpath(repo_rel)
    if os.path.exists(repo_abs):
        return repo_abs
    return None


def _load_vcenters() -> list[dict[str, Any]]:
    path = _find_inventory()
    if not path:
        return []
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("vcenters", [])


VCENTERS = _load_vcenters()


def resolve_vcenter(vcenter_name: str | None = None) -> dict[str, Any]:
    """Resolve inventory and credential information for a vCenter entry."""
    names = [entry["name"] for entry in VCENTERS]
    if not VCENTERS:
        raise ValueError(
            "inventory.yaml has no vcenters defined. Run 'vcenter-mcp configure' to add one."
        )

    if not vcenter_name:
        if len(VCENTERS) == 1:
            entry = VCENTERS[0]
        else:
            raise ValueError(f"Multiple vCenters configured. Specify vcenter_name from: {names}")
    else:
        entry = next(
            (candidate for candidate in VCENTERS if candidate["name"].lower() == vcenter_name.lower()),
            None,
        )
        if entry is None:
            raise ValueError(f"vCenter '{vcenter_name}' not found. Available: {names}")

    host = (entry.get("fqdn") or "").strip() or (entry.get("ip_address") or "").strip()
    if not host:
        raise ValueError(
            f"vCenter '{entry['name']}' must define either 'fqdn' or 'ip_address' in inventory.yaml."
        )

    return {
        "host": host,
        "verify_ssl": bool(entry.get("verify_ssl", False)),
        **get_vcenter_credentials(entry["name"]),
    }


def json_response(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [part.strip() for part in value.split(",")]
    return [item for item in items if item] or None


def path_id(value: str) -> str:
    return quote(str(value), safe="")
