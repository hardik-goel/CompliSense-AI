"""Microsoft Azure read-only discovery connector (Phase 3.1).

Mirrors the AWS/GCP connectors against Azure Resource Manager, emitting the same
normalized signal keys so connectors/mapping.py serves every provider.

Access: a read-only OAuth2 bearer token for the ARM audience (a service principal /
managed identity granted the built-in **Reader** role) plus the subscription id.
Transport is an injectable ``http_get`` (default: bearer ``requests`` over ARM), so tests
need neither SDK nor network.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Dict, List, Optional

from connectors.base import (
    Connector, ConnectorError, DiscoveredSignal, bearer_http_get, utc_now_iso,
)

ARM = "https://management.azure.com"
# Indian Azure regions (lower-cased, space-stripped) for the cross-border heuristic.
INDIA_LOCATIONS = {"centralindia", "southindia", "westindia", "jioindiacentral", "jioindiawest"}
HttpGet = Callable[..., Dict[str, Any]]


class AzureConnector(Connector):
    provider = "azure"

    def __init__(
        self,
        subscription_id: str,
        access_token: Optional[str] = None,
        http_get: Optional[HttpGet] = None,
        now: Optional[dt.datetime] = None,
    ):
        if not subscription_id:
            raise ConnectorError("AzureConnector requires a subscription_id")
        self.subscription_id = subscription_id
        self._get = http_get or bearer_http_get(access_token or "")
        self._now_iso = utc_now_iso(now)

    def _arm(self, path: str) -> str:
        return f"{ARM}/subscriptions/{self.subscription_id}{path}"

    def _signal(self, key: str, value: Any, confidence: str, evidence: str) -> DiscoveredSignal:
        return DiscoveredSignal(key=key, value=value, source=self.provider,
                                confidence=confidence, evidence=evidence, observed_at=self._now_iso)

    def _degraded(self, key: str, exc: Exception) -> DiscoveredSignal:
        return self._signal(key, None, "low", f"could not read (permission or API error): {type(exc).__name__}")

    def discover(self) -> List[DiscoveredSignal]:
        signals: List[DiscoveredSignal] = []
        signals.extend(self._probe_storage())
        signals.extend(self._probe_keyvault())
        signals.extend(self._probe_defender())
        return signals

    def _probe_storage(self) -> List[DiscoveredSignal]:
        try:
            data = self._get(self._arm("/providers/Microsoft.Storage/storageAccounts"),
                             params={"api-version": "2023-01-01"})
            accounts = data.get("value", []) or []
            out = [self._signal("has_data_stores", bool(accounts), "high", f"{len(accounts)} storage account(s)")]
            if not accounts:
                return out
            block_all = all(
                (a.get("properties", {}).get("allowBlobPublicAccess") is False) for a in accounts)
            non_india = any(
                (str(a.get("location", "")).replace(" ", "").lower() not in INDIA_LOCATIONS) for a in accounts)
            # Azure Storage is encrypted at rest by default (SSE).
            out.append(self._signal("storage_encryption", True, "high", "Azure Storage SSE encrypts data at rest by default"))
            out.append(self._signal("public_access_blocked", block_all, "high",
                                    "blob public access disabled on all accounts" if block_all
                                    else "one or more accounts allow blob public access"))
            if non_india:
                out.append(self._signal("data_outside_india", True, "low",
                                        "storage found outside Indian regions — review cross-border transfer"))
            return out
        except Exception as exc:
            return [self._degraded("has_data_stores", exc)]

    def _probe_keyvault(self) -> List[DiscoveredSignal]:
        try:
            data = self._get(self._arm("/providers/Microsoft.KeyVault/vaults"),
                             params={"api-version": "2022-07-01"})
            vaults = data.get("value", []) or []
            return [self._signal("encryption_keys_present", bool(vaults), "medium",
                                 f"{len(vaults)} Key Vault(s)")]
        except Exception as exc:
            return [self._degraded("encryption_keys_present", exc)]

    def _probe_defender(self) -> List[DiscoveredSignal]:
        try:
            data = self._get(self._arm("/providers/Microsoft.Security/pricings"),
                             params={"api-version": "2023-01-01"})
            pricings = data.get("value", []) or []
            standard = any((p.get("properties", {}).get("pricingTier") == "Standard") for p in pricings)
            return [self._signal("threat_detection_enabled", standard, "medium",
                                 "Microsoft Defender for Cloud (Standard) enabled" if standard
                                 else "Defender for Cloud on Free tier / not enabled")]
        except Exception as exc:
            return [self._degraded("threat_detection_enabled", exc)]

    def least_privilege_policy(self) -> Dict[str, Any]:
        return {
            "type": "azure_rbac_role",
            "recommended_role": "Reader",
            "scope": f"/subscriptions/{self.subscription_id}",
            "note": "Built-in Reader is read-only across the subscription; no write/action permissions.",
        }
