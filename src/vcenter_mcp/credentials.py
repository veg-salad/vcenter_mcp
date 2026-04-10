"""OS keyring credential helpers for vcenter-mcp."""

from __future__ import annotations

import os

try:
    import keyring
except ImportError as exc:
    raise ImportError("Install keyring to use vcenter-mcp credential storage.") from exc

SERVICE_NAME = "vcenter-mcp"


def _get(key: str) -> str | None:
    try:
        return keyring.get_password(SERVICE_NAME, key) or None
    except Exception:
        return None


def _set(key: str, value: str) -> None:
    keyring.set_password(SERVICE_NAME, key, value)


def get_vcenter_credentials(vcenter_name: str) -> dict[str, object]:
    """Return username, password, and verify_ssl settings for a vCenter."""
    name = (vcenter_name or "").strip()
    username = (
        _get(f"vcenter.{name}.username")
        or _get("vcenter.default.username")
        or os.environ.get("VCENTER_USERNAME", "")
    )
    password = (
        _get(f"vcenter.{name}.password")
        or _get("vcenter.default.password")
        or os.environ.get("VCENTER_PASSWORD", "")
    )
    verify_ssl_raw = (
        _get(f"vcenter.{name}.verify_ssl")
        or _get("vcenter.default.verify_ssl")
        or os.environ.get("VCENTER_VERIFY_SSL", "false")
    )
    if not username:
        raise EnvironmentError(
            f"No vCenter credentials found for '{name}'. Run 'vcenter-mcp configure' first."
        )
    return {
        "username": username,
        "password": password,
        "verify_ssl": verify_ssl_raw.lower() == "true",
    }


def store_vcenter_credentials(
    vcenter_name: str,
    username: str,
    password: str,
    verify_ssl: bool = False,
) -> None:
    name = vcenter_name or "default"
    _set(f"vcenter.{name}.username", username)
    _set(f"vcenter.{name}.password", password)
    _set(f"vcenter.{name}.verify_ssl", "true" if verify_ssl else "false")
