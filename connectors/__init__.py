"""Tier-1 connectors: read-only discovery of a customer's live stack (Phase 3).

Phase 0/1 relied on self-declared manifest answers. Tier-1 connectors corroborate
those answers against the customer's real environment — read-only, least-privilege,
and always "suggested, user confirms". A connector never mutates the customer account
and never asserts compliance; it emits evidence-backed signals that map to manifest
answer *suggestions* a human accepts or rejects.

Guardrails (inherited from the product, do not relax):
  - Read-only by default; least-privilege IAM.
  - Suggested, not applied — discovery feeds suggestions, the user confirms.
  - No credential storage; only signals + suggestions are persisted (consent-gated).
  - Readiness framing, full audit trail.
"""

from connectors.base import Connector, ConnectorError, DiscoveredSignal

__all__ = ["Connector", "ConnectorError", "DiscoveredSignal"]
