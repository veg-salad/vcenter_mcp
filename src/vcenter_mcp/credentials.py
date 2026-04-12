"""OS keyring credential helpers for vcenter-mcp."""

from __future__ import annotations

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
    """Return username and password from OS keyring for a vCenter."""
    name = (vcenter_name or "").strip()
    username = _get(f"vcenter.{name}.username") or _get("vcenter.default.username") or ""
    password = _get(f"vcenter.{name}.password") or _get("vcenter.default.password") or ""

    username = username.strip()
    if not username or not password:
        raise EnvironmentError(
            f"No vCenter credentials found for '{name}'. Run 'vcenter-mcp configure' first."
        )
    if any(ord(ch) < 32 for ch in username):
        raise EnvironmentError(f"Stored username for '{name}' contains invalid control characters.")

    return {
        "username": username,
        "password": password,
    }


def store_vcenter_credentials(
    vcenter_name: str,
    username: str,
    password: str,
) -> None:
    name = vcenter_name or "default"
    cleaned_username = (username or "").strip()
    if not cleaned_username or not password:
        raise ValueError("Username and password are required for keyring storage.")
    if any(ord(ch) < 32 for ch in cleaned_username):
        raise ValueError("Username cannot contain control characters.")

    _set(f"vcenter.{name}.username", cleaned_username)
    _set(f"vcenter.{name}.password", password)
