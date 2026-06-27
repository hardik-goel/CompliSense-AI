"""GitHub read-only discovery connector (Phase 3.1).

GitHub posture corroborates *organisational security* controls (org-wide 2FA, audit-log
access, vulnerability alerting) rather than data storage/location. Access is a read-only
fine-grained PAT or GitHub App token; we only ever GET.

Transport is an injectable ``http_get(url, params=None) -> dict`` (default: bearer-token
``requests`` over the GitHub REST API), so tests run with no token and no network.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional

from connectors.base import (
    Connector, ConnectorError, DiscoveredSignal, bearer_http_get, utc_now_iso,
)

API = "https://api.github.com"
HttpGet = Callable[..., Dict[str, Any]]


class GitHubConnector(Connector):
    provider = "github"

    def __init__(
        self,
        org: str,
        token: Optional[str] = None,
        http_get: Optional[HttpGet] = None,
        now: Optional[dt.datetime] = None,
    ):
        if not org:
            raise ConnectorError("GitHubConnector requires an organisation login")
        self.org = org
        self._get = http_get or bearer_http_get(
            token or "", extra_headers={"X-GitHub-Api-Version": "2022-11-28"}
        )
        self._now_iso = utc_now_iso(now)

    def _signal(self, key: str, value: Any, confidence: str, evidence: str) -> DiscoveredSignal:
        return DiscoveredSignal(key=key, value=value, source=self.provider,
                                confidence=confidence, evidence=evidence, observed_at=self._now_iso)

    def _degraded(self, key: str, exc: Exception) -> DiscoveredSignal:
        return self._signal(key, None, "low", f"could not read (permission or API error): {type(exc).__name__}")

    def discover(self) -> List[DiscoveredSignal]:
        signals: List[DiscoveredSignal] = []
        signals.extend(self._probe_org())
        signals.extend(self._probe_audit_log())
        signals.extend(self._probe_dependabot())
        return signals

    def _probe_org(self) -> List[DiscoveredSignal]:
        try:
            org = self._get(f"{API}/orgs/{self.org}")
            two_factor = bool(org.get("two_factor_requirement_enabled"))
            return [self._signal("mfa_enabled", two_factor,
                                 "high" if "two_factor_requirement_enabled" in org else "low",
                                 "org enforces 2FA for all members" if two_factor else "org does not require 2FA")]
        except Exception as exc:
            return [self._degraded("mfa_enabled", exc)]

    def _probe_audit_log(self) -> List[DiscoveredSignal]:
        try:
            # 200 (even empty list) means the org audit log is accessible/enabled.
            self._get(f"{API}/orgs/{self.org}/audit-log", params={"per_page": 1})
            return [self._signal("audit_logging_enabled", True, "high", "organisation audit log accessible")]
        except Exception as exc:
            return [self._degraded("audit_logging_enabled", exc)]

    def _probe_dependabot(self) -> List[DiscoveredSignal]:
        try:
            alerts = self._get(f"{API}/orgs/{self.org}/dependabot/alerts", params={"per_page": 1})
            enabled = isinstance(alerts, list)
            return [self._signal("threat_detection_enabled", enabled, "medium",
                                 "Dependabot vulnerability alerts enabled org-wide" if enabled
                                 else "Dependabot alerts not accessible")]
        except Exception as exc:
            return [self._degraded("threat_detection_enabled", exc)]

    def least_privilege_policy(self) -> Dict[str, Any]:
        # GitHub authorises via token scopes / fine-grained permissions, not IAM JSON.
        return {
            "type": "github_fine_grained_token",
            "organization_permissions": {
                "Administration": "Read-only",
                "Audit log": "Read-only",
                "Dependabot alerts": "Read-only",
            },
            "classic_scopes_equivalent": ["read:org", "read:audit_log"],
            "note": "Read-only only — no write/admin-write scopes required.",
        }
