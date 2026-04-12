# vcenter-mcp Security Posture

This document summarizes the current security controls, intended operating model, and known boundaries.

## Security goals

- Keep vCenter interactions read-only and tightly scoped to documented tool behavior.
- Prevent accidental API surface expansion by future tool changes.
- Reduce abuse risk from excessive parallel calls and high request rates.
- Keep credentials in OS-managed secure storage only.

## Implemented controls

### 1. Central policy engine for API access

The client layer enforces a centralized policy that validates:

- Allowed HTTP methods: `GET` only.
- Allowed API path templates.
- Allowed query parameter keys for each endpoint template.

Any request outside policy is rejected before network I/O.

Why this matters:
- Even if a future tool is implemented incorrectly, unauthorized endpoints and extra parameters are blocked centrally.

### 2. Generic POST is disabled

The generic read-only POST helper is intentionally disabled.

Why this matters:
- Prevents broadening into action-style endpoints through generic helpers.
- Future POST use must be consciously reviewed and implemented as an explicit exception.

### 3. Sanitized upstream error propagation

The client no longer returns raw HTTP response bodies from vCenter in raised errors.

Why this matters:
- Reduces leakage of internal infrastructure details into tool output or conversational context.

### 4. Keyring-only credential ingestion

Credential lookup now uses OS keyring only.

- Removed environment variable credential fallback.
- Added basic credential validation for stored values.

Why this matters:
- Removes a broad injection/exposure surface from process environment variables.

### 5. Per-tool concurrency caps

Each tool is wrapped with a security guard that enforces a maximum number of concurrent executions.

Why this matters:
- Limits accidental overload and reduces abuse potential.

### 6. Per-tool rate limiting

Each tool has a token-window rate limit (requests per minute).

Why this matters:
- Prevents rapid-fire enumeration and limits abuse from tight prompt loops.

### 7. Validated config loaded once at startup

A validated security config object is loaded once during startup.

Supported environment controls:

- `VCENTER_MCP_REQUEST_TIMEOUT_SECONDS`
- `VCENTER_MCP_TOOL_CONCURRENCY_LIMIT`
- `VCENTER_MCP_RATE_LIMIT_PER_MINUTE`
- `VCENTER_MCP_TOOL_POLICY_OVERRIDES` (JSON object keyed by tool name)

Why this matters:
- Misconfiguration fails fast at process start.
- Runtime behavior is deterministic and centralized.

## TLS rationale and caution

`verify_ssl` remains configurable per vCenter inventory entry because many enterprise deployments use private CA or self-signed certs.

- `verify_ssl: true` gives strongest MITM protection and identity verification.
- `verify_ssl: false` improves compatibility in environments that are not PKI-ready.

Security caution:
- Using `verify_ssl: false` reduces transport authenticity guarantees and should be treated as risk acceptance.
- Prefer moving to trusted internal CA whenever feasible.

This project intentionally preserves this choice for operator convenience and real-world compatibility.

## Keyring access boundary disclaimer

The MCP server process must read credentials from keyring to authenticate to vCenter. Within that process, credentials exist in memory during request execution.

Important boundary:
- Preventing all possible host-level credential access is outside application scope.
- Any principal that can execute arbitrary local commands as the same user may still be able to access local secrets.

Operational recommendation:
- Run the MCP server under a least-privilege user context on a trusted workstation or jump host.

## Remaining cautions

- vSphere Web Services operations may take longer than REST calls depending on environment size and vCenter performance.
- Rate limits and concurrency limits reduce risk but are not a full anti-abuse system.
- This project does not currently include built-in SIEM/audit logging in this hardening step.

## Production usage guidance

- Use a read-only vCenter service account with least privilege RBAC.
- Scope network access so the MCP host can only reach approved vCenter endpoints.
- Set conservative tool limits for large shared environments.
- Periodically review inventory entries and remove stale vCenter targets.

## Disclaimer

This project is community-maintained and is not an official Broadcom or VMware product. Operators are responsible for validating security controls against their own policy and compliance requirements.
