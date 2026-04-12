"""HTTP client helpers for read-only vCenter and appliance access."""

from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Any

import requests
import urllib3

from vcenter_mcp.security import enforce_request_policy, get_active_request_timeout

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_TIMEOUT_SECONDS = 30
_HTTPS_PORT = 443
_SESSION_CACHE: dict[tuple[str, int, str], str] = {}
_LOCK = threading.Lock()


class VCenterClientError(RuntimeError):
    """Raised when the vCenter API returns an unexpected error."""


def _base_url(host: str) -> str:
    return f"https://{host}:{_HTTPS_PORT}"


def _auth_headers(session_token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "vmware-api-session-id": session_token,
    }


def create_session(*, host: str, username: str, password: str, verify_ssl: bool) -> str:
    """Authenticate to vCenter and return a session token."""
    cache_key = (host, _HTTPS_PORT, username)
    with _LOCK:
        cached = _SESSION_CACHE.get(cache_key)
    if cached:
        return cached

    try:
        response = requests.post(
            f"{_base_url(host)}/api/session",
            auth=(username, password),
            headers={"Accept": "application/json"},
            verify=verify_ssl,
            timeout=get_active_request_timeout(_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        raise VCenterClientError(
            f"SSL error while connecting to {host}:{_HTTPS_PORT}. Enable verification only with trusted certificates."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise VCenterClientError(f"Cannot connect to {host}:{_HTTPS_PORT}. Verify the vCenter host is reachable.") from exc
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise VCenterClientError(f"Session creation failed with HTTP {status}.") from exc

    token = response.json()
    with _LOCK:
        _SESSION_CACHE[cache_key] = token
    return token


def vcenter_request(
    method: str,
    path: str,
    *,
    params: Mapping[str, Any] | None = None,
    json_body: Any = None,
    host: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> Any:
    """Issue a read-only request against the vCenter API."""
    enforce_request_policy(method, path, params)

    token = create_session(
        host=host,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
    )

    request_params = {key: value for key, value in (params or {}).items() if value is not None}
    request_kwargs = {
        "method": method,
        "url": f"{_base_url(host)}{path}",
        "headers": _auth_headers(token),
        "params": request_params,
        "json": json_body,
        "verify": verify_ssl,
        "timeout": get_active_request_timeout(_TIMEOUT_SECONDS),
    }

    try:
        response = requests.request(**request_kwargs)
        if response.status_code == 401:
            with _LOCK:
                _SESSION_CACHE.pop((host, _HTTPS_PORT, username), None)
            request_kwargs["headers"] = _auth_headers(
                create_session(
                    host=host,
                    username=username,
                    password=password,
                    verify_ssl=verify_ssl,
                )
            )
            response = requests.request(**request_kwargs)
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        raise VCenterClientError(f"SSL error while calling {path} on {host}:{_HTTPS_PORT}.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise VCenterClientError(f"Connection error while calling {path} on {host}:{_HTTPS_PORT}.") from exc
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise VCenterClientError(f"HTTP {status} from vCenter API for {path}.") from exc

    if response.status_code == 204 or not response.text:
        return {"status": response.status_code}
    return response.json()


def vcenter_get(path: str, *, params: Mapping[str, Any] | None = None, **connection: Any) -> Any:
    return vcenter_request("GET", path, params=params, **connection)


def vcenter_post_readonly(
    path: str,
    *,
    json_body: Any = None,
    params: Mapping[str, Any] | None = None,
    **connection: Any,
) -> Any:
    raise VCenterClientError(
        "POST operations are disabled by security policy. "
        "Use a reviewed, explicit tool implementation for any future exception."
    )
