# Security Policy

CompliSense is a compliance-readiness product; the security of the product itself is part
of the promise. This file states our posture and how to report issues.

## Reporting a vulnerability

Please report suspected security issues privately. Do **not** open a public issue for a
vulnerability.

- Email: **security@complisense.ai** *(update to the maintained address before launch)*
- Include: a description, reproduction steps, affected component/version, and impact.
- We aim to acknowledge within a few business days and to keep you updated on remediation.

Please act in good faith: do not access, modify, or exfiltrate other users' data, and give
us reasonable time to remediate before any disclosure.

## Posture (current state)

- **Authentication:** JWT-based per-user auth on the SaaS API. Privileged endpoints are
  guarded by an admin token.
  - ⚠️ **Known hardening item:** the admin token must not fall back to a weak default in
    any deployed environment (`ADMIN_API_TOKEN` must be set to a strong secret). Tracked in
    `docs/BUILD_PLAN_AND_AUDIT.md` (finding H7) and addressed in Foundation step 0.5.
- **Data handling:** see [`docs/DATA_HANDLING.md`](docs/DATA_HANDLING.md). The local agent
  runs offline; raw artefacts are not uploaded; only findings/metadata are stored.
- **Secrets:** must be supplied via environment variables, never committed. Do not log
  tokens or secrets.
- **Transport:** all hosted endpoints must be served over HTTPS.

## Scope

This product is provided without warranty (see the product Terms). Security reports about
the hosted service, the local agent, and the rulepack tooling are all in scope.
