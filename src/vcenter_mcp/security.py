"""Centralized security policy, runtime limits, and validated configuration."""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Any


@dataclass(frozen=True)
class ToolSecurityPolicy:
    """Per-tool security controls."""

    request_timeout_seconds: float
    concurrency_limit: int
    rate_limit_per_minute: int


@dataclass(frozen=True)
class SecurityConfig:
    """Validated security configuration loaded once at startup."""

    default_tool_policy: ToolSecurityPolicy
    per_tool_policy: dict[str, ToolSecurityPolicy]


_ENDPOINT_PARAM_POLICY: dict[str, set[str]] = {
    "/api/appliance/system/time": set(),
    "/api/appliance/system/version": set(),
    "/api/vcenter/cluster": {"clusters", "datacenters"},
    "/api/vcenter/cluster/{id}": set(),
    "/api/vcenter/datacenter": {"datacenters", "folders"},
    "/api/vcenter/datacenter/{id}": set(),
    "/api/vcenter/datastore": {"datastores", "names", "folders", "datacenters"},
    "/api/vcenter/datastore/{id}": set(),
    "/api/vcenter/folder": {"folders", "names", "type", "datacenters"},
    "/api/vcenter/network": {"networks", "names", "datacenters"},
    "/api/vcenter/resource-pool": {"resource_pools", "names", "hosts", "clusters"},
    "/api/vcenter/resource-pool/{id}": set(),
    "/api/vcenter/vm": {"vms", "names", "power_states", "hosts", "clusters", "folders", "datacenters"},
    "/api/vcenter/vm/{id}": set(),
    "/api/vcenter/vm/{id}/guest/identity": set(),
    "/api/vcenter/vm/{id}/guest/local-filesystem": set(),
    "/api/vcenter/vm/{id}/guest/networking/interfaces": set(),
    "/api/vcenter/vm/{id}/hardware": set(),
    "/api/vcenter/vm/{id}/hardware/boot": set(),
    "/api/vcenter/vm/{id}/hardware/cpu": set(),
    "/api/vcenter/vm/{id}/hardware/disk": set(),
    "/api/vcenter/vm/{id}/hardware/disk/{id}": set(),
    "/api/vcenter/vm/{id}/hardware/ethernet": set(),
    "/api/vcenter/vm/{id}/hardware/ethernet/{id}": set(),
    "/api/vcenter/vm/{id}/hardware/memory": set(),
}

_CURRENT_TOOL: ContextVar[str | None] = ContextVar("current_tool", default=None)


class _ToolLimiter:
    def __init__(self, policy: ToolSecurityPolicy) -> None:
        self._policy = policy
        self._semaphore = threading.BoundedSemaphore(policy.concurrency_limit)
        self._rate_lock = threading.Lock()
        self._timestamps: deque[float] = deque()

    def enforce_rate_limit(self, tool_name: str) -> None:
        now = time.monotonic()
        window_seconds = 60.0
        with self._rate_lock:
            while self._timestamps and now - self._timestamps[0] >= window_seconds:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._policy.rate_limit_per_minute:
                raise RuntimeError(
                    f"Rate limit exceeded for tool '{tool_name}'. "
                    f"Try again after a short pause."
                )
            self._timestamps.append(now)

    @contextmanager
    def acquire_slot(self, tool_name: str):
        acquired = self._semaphore.acquire(timeout=self._policy.request_timeout_seconds)
        if not acquired:
            raise RuntimeError(
                f"Concurrency limit reached for tool '{tool_name}'. "
                "Try again once active requests complete."
            )
        try:
            yield
        finally:
            self._semaphore.release()


_LIMITERS: dict[str, _ToolLimiter] = {}
_LIMITERS_LOCK = threading.Lock()


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _build_policy(raw: Mapping[str, Any], base: ToolSecurityPolicy) -> ToolSecurityPolicy:
    timeout = float(raw.get("request_timeout_seconds", base.request_timeout_seconds))
    concurrency = int(raw.get("concurrency_limit", base.concurrency_limit))
    rate = int(raw.get("rate_limit_per_minute", base.rate_limit_per_minute))

    if timeout <= 0 or timeout > 300:
        raise ValueError("request_timeout_seconds must be > 0 and <= 300.")
    if concurrency < 1 or concurrency > 100:
        raise ValueError("concurrency_limit must be between 1 and 100.")
    if rate < 1 or rate > 10000:
        raise ValueError("rate_limit_per_minute must be between 1 and 10000.")

    return ToolSecurityPolicy(
        request_timeout_seconds=timeout,
        concurrency_limit=concurrency,
        rate_limit_per_minute=rate,
    )


@lru_cache(maxsize=1)
def get_security_config() -> SecurityConfig:
    """Load and validate security configuration once per process."""
    default_policy = ToolSecurityPolicy(
        request_timeout_seconds=float(
            _env_int("VCENTER_MCP_REQUEST_TIMEOUT_SECONDS", 30, minimum=1, maximum=300)
        ),
        concurrency_limit=_env_int("VCENTER_MCP_TOOL_CONCURRENCY_LIMIT", 4, minimum=1, maximum=100),
        rate_limit_per_minute=_env_int("VCENTER_MCP_RATE_LIMIT_PER_MINUTE", 120, minimum=1, maximum=10000),
    )

    overrides_raw = os.environ.get("VCENTER_MCP_TOOL_POLICY_OVERRIDES", "").strip()
    per_tool: dict[str, ToolSecurityPolicy] = {}
    if overrides_raw:
        try:
            parsed = json.loads(overrides_raw)
        except json.JSONDecodeError as exc:
            raise ValueError("VCENTER_MCP_TOOL_POLICY_OVERRIDES must be valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("VCENTER_MCP_TOOL_POLICY_OVERRIDES must be a JSON object.")
        for tool_name, override in parsed.items():
            if not isinstance(tool_name, str) or not tool_name.strip():
                raise ValueError("Tool names in VCENTER_MCP_TOOL_POLICY_OVERRIDES must be non-empty strings.")
            if not isinstance(override, dict):
                raise ValueError(
                    f"Override for tool '{tool_name}' must be a JSON object with policy fields."
                )
            per_tool[tool_name] = _build_policy(override, default_policy)

    return SecurityConfig(default_tool_policy=default_policy, per_tool_policy=per_tool)


def get_tool_policy(tool_name: str) -> ToolSecurityPolicy:
    config = get_security_config()
    return config.per_tool_policy.get(tool_name, config.default_tool_policy)


def _get_limiter(tool_name: str) -> _ToolLimiter:
    with _LIMITERS_LOCK:
        limiter = _LIMITERS.get(tool_name)
        expected_policy = get_tool_policy(tool_name)
        if limiter is None or limiter._policy != expected_policy:  # noqa: SLF001 - intentional internal check
            limiter = _ToolLimiter(expected_policy)
            _LIMITERS[tool_name] = limiter
        return limiter


def guard_tool(tool_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Apply per-tool concurrency and rate limits, and set execution context."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter = _get_limiter(tool_name)
            limiter.enforce_rate_limit(tool_name)
            token = _CURRENT_TOOL.set(tool_name)
            try:
                with limiter.acquire_slot(tool_name):
                    return func(*args, **kwargs)
            finally:
                _CURRENT_TOOL.reset(token)

        return wrapper

    return decorator


def get_active_tool_name() -> str | None:
    return _CURRENT_TOOL.get()


def get_active_request_timeout(default_timeout: float) -> float:
    tool_name = get_active_tool_name()
    if not tool_name:
        return default_timeout
    return min(default_timeout, get_tool_policy(tool_name).request_timeout_seconds)


def _normalize_path(path: str) -> str:
    if not path or not path.startswith("/"):
        raise ValueError("Request path must be an absolute API path beginning with '/'.")
    if "?" in path or "#" in path:
        raise ValueError("Request path must not include query strings or fragments.")
    normalized = path.rstrip("/")
    return normalized or "/"


def _match_template(path: str) -> str | None:
    path_segments = path.strip("/").split("/")
    for template in _ENDPOINT_PARAM_POLICY:
        template_segments = template.strip("/").split("/")
        if len(path_segments) != len(template_segments):
            continue
        matches = True
        for left, right in zip(path_segments, template_segments):
            if right == "{id}":
                if left == "":
                    matches = False
                    break
                continue
            if left != right:
                matches = False
                break
        if matches:
            return template
    return None


def enforce_request_policy(method: str, path: str, params: Mapping[str, Any] | None) -> None:
    """Enforce allowed method, endpoint templates, and query parameter keys."""
    if method != "GET":
        raise ValueError("Security policy allows only GET operations.")

    normalized_path = _normalize_path(path)
    template = _match_template(normalized_path)
    if template is None:
        raise ValueError(f"Endpoint '{normalized_path}' is not allowed by security policy.")

    allowed_params = _ENDPOINT_PARAM_POLICY[template]
    provided_params = set((params or {}).keys())
    unknown = provided_params - allowed_params
    if unknown:
        unknown_joined = ", ".join(sorted(unknown))
        raise ValueError(
            f"Endpoint '{normalized_path}' does not allow query parameter(s): {unknown_joined}."
        )
