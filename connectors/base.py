"""Connector framework: the signal model + the abstract connector contract (Phase 3.1).

Kept dependency-free and pure so it imports without any cloud SDK and is trivially
testable. Concrete connectors (e.g. ``connectors/aws.py``) implement ``discover`` and
``least_privilege_policy``.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


class ConnectorError(Exception):
    """Raised when a connector cannot establish access or run discovery."""


@dataclass
class DiscoveredSignal:
    """One read-only observation about the customer's environment.

    Deliberately content-free: a signal records *whether* a control is present and a
    short human-readable evidence note — never raw API payloads, resource ARNs, or any
    customer data. This keeps discovery history small and consistent with the
    "we do not store your source artefacts / personal data" stance (DATA_HANDLING.md).
    """

    key: str
    value: Any
    source: str
    confidence: str = "medium"  # high | medium | low
    evidence: str = ""
    observed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class Suggestion:
    """A proposed manifest answer derived from one or more signals. Never auto-applied.

    ``action`` distinguishes a confident corroboration ("confirm") from something that
    merely warrants human review ("review"). The user accepts or rejects; the manifest
    is only updated on explicit confirmation (handled in the API/UI layer, Phase 3.2/3.3).
    """

    manifest_field: str
    suggested_value: Any
    confidence: str  # high | medium | low
    rationale: str
    action: str = "confirm"  # confirm | review
    evidence_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def utc_now_iso(now: Optional[dt.datetime] = None) -> str:
    """ISO timestamp helper. Injectable ``now`` keeps callers/tests deterministic."""
    return (now or dt.datetime.utcnow()).isoformat()


def bearer_http_get(token: str, extra_headers: Optional[Dict[str, str]] = None):
    """Build a read-only ``http_get(url, params=None) -> dict`` using a bearer token.

    Used as the DEFAULT transport for the REST-based connectors (GCP/Azure/GitHub) so
    they make real, authenticated GET calls in production. Tests inject their own
    ``http_get`` instead, so neither the SDK nor the network is touched under test.
    ``requests`` is imported lazily — importing a connector never requires it.
    """

    def _get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import requests  # lazy: optional at import time
        except ImportError as exc:  # pragma: no cover
            raise ConnectorError("requests is required for live discovery") from exc
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code >= 400:
            raise ConnectorError(f"GET {url} -> HTTP {resp.status_code}")
        return resp.json() if resp.content else {}

    return _get


class Connector(ABC):
    """Abstract read-only connector.

    Implementations must be read-only and least-privilege. ``least_privilege_policy``
    returns the exact permission document a customer grants — published so they can audit
    that we ask for nothing beyond read access.
    """

    #: short stable identifier, e.g. "aws"
    provider: str = "base"

    @abstractmethod
    def discover(self) -> List[DiscoveredSignal]:
        """Run read-only discovery and return normalized signals."""

    @abstractmethod
    def least_privilege_policy(self) -> Dict[str, Any]:
        """Return the least-privilege permission document this connector requires."""
