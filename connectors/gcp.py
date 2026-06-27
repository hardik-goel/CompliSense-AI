"""Google Cloud read-only discovery connector (Phase 3.1).

Mirrors the AWS connector against GCP, emitting the SAME normalized signal keys
(storage_encryption, public_access_blocked, has_data_stores, …) so one mapper
(connectors/mapping.py) serves every provider.

Access: a read-only OAuth2 bearer token (e.g. from a service account granted
``roles/viewer`` or the narrower read roles in ``least_privilege_policy``) plus the
project id. Transport is an injectable ``http_get`` (default: bearer ``requests`` over
the GCP JSON APIs), so tests need neither SDK nor network.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional

from connectors.base import (
    Connector, ConnectorError, DiscoveredSignal, bearer_http_get, utc_now_iso,
)

# Indian GCP regions — bucket location outside these hints at a cross-border transfer.
INDIA_LOCATIONS = {"asia-south1", "asia-south2"}
HttpGet = Callable[..., Dict[str, Any]]


class GCPConnector(Connector):
    provider = "gcp"

    def __init__(
        self,
        project_id: str,
        access_token: Optional[str] = None,
        region: str = "asia-south1",
        http_get: Optional[HttpGet] = None,
        now: Optional[dt.datetime] = None,
    ):
        if not project_id:
            raise ConnectorError("GCPConnector requires a project_id")
        self.project_id = project_id
        self.region = region
        self._get = http_get or bearer_http_get(access_token or "")
        self._now_iso = utc_now_iso(now)

    def _signal(self, key: str, value: Any, confidence: str, evidence: str) -> DiscoveredSignal:
        return DiscoveredSignal(key=key, value=value, source=self.provider,
                                confidence=confidence, evidence=evidence, observed_at=self._now_iso)

    def _degraded(self, key: str, exc: Exception) -> DiscoveredSignal:
        return self._signal(key, None, "low", f"could not read (permission or API error): {type(exc).__name__}")

    def discover(self) -> List[DiscoveredSignal]:
        signals: List[DiscoveredSignal] = []
        signals.extend(self._probe_storage())
        signals.extend(self._probe_logging())
        signals.append(self._signal("primary_region", self.region, "high",
                                     f"discovery region {self.region}"
                                     + ("" if self.region in INDIA_LOCATIONS else " (outside India — review cross-border)")))
        return signals

    def _probe_storage(self) -> List[DiscoveredSignal]:
        try:
            data = self._get("https://storage.googleapis.com/storage/v1/b",
                             params={"project": self.project_id})
            buckets = data.get("items", []) or []
            out = [self._signal("has_data_stores", bool(buckets), "high", f"{len(buckets)} GCS bucket(s)")]
            if not buckets:
                return out
            # GCS encrypts at rest by default; flag CMEK separately as key-management evidence.
            cmek = any(b.get("encryption", {}).get("defaultKmsKeyName") for b in buckets)
            block_all = all(
                (b.get("iamConfiguration", {}).get("publicAccessPrevention") == "enforced") for b in buckets)
            lifecycle_any = any((b.get("lifecycle", {}).get("rule")) for b in buckets)
            non_india = any((b.get("location", "").lower() not in INDIA_LOCATIONS) for b in buckets)
            out.append(self._signal("storage_encryption", True, "high", "GCS encrypts all objects at rest by default"))
            out.append(self._signal("public_access_blocked", block_all, "high",
                                    "public access prevention enforced on all buckets" if block_all
                                    else "one or more buckets without enforced public-access prevention"))
            out.append(self._signal("retention_lifecycle_present", lifecycle_any, "medium",
                                    "object lifecycle rules present" if lifecycle_any else "no lifecycle rules found"))
            if cmek:
                out.append(self._signal("encryption_keys_present", True, "medium", "customer-managed KMS keys on buckets"))
            if non_india:
                out.append(self._signal("data_outside_india", True, "low",
                                        "GCS data found outside Indian regions — review cross-border transfer"))
            return out
        except Exception as exc:
            return [self._degraded("has_data_stores", exc)]

    def _probe_logging(self) -> List[DiscoveredSignal]:
        try:
            data = self._get(f"https://logging.googleapis.com/v2/projects/{self.project_id}/sinks")
            sinks = data.get("sinks", []) or []
            return [self._signal("audit_logging_enabled", bool(sinks), "medium",
                                 f"{len(sinks)} logging sink(s) configured")]
        except Exception as exc:
            return [self._degraded("audit_logging_enabled", exc)]

    def least_privilege_policy(self) -> Dict[str, Any]:
        return {
            "type": "gcp_iam_role",
            "recommended_role": "roles/viewer",
            "minimal_permissions": [
                "storage.buckets.list", "storage.buckets.get",
                "logging.sinks.list",
            ],
            "note": "Read-only. Grant on the project to a discovery service account.",
        }
