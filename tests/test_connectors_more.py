"""GCP / Azure / GitHub connectors + registry + cross-provider mapping (Phase 3.1).

All three use an injectable ``http_get``, so tests run with no token, no SDK, no network.
A single fake router maps URL substrings to canned JSON (or an Exception to simulate a
permission/API failure).
"""

import pytest

from connectors.azure import AzureConnector
from connectors.gcp import GCPConnector
from connectors.github import GitHubConnector
from connectors.base import Connector, ConnectorError, DiscoveredSignal
from connectors.mapping import signals_to_suggestions
from connectors.registry import available_providers, get_connector, CONNECTOR_REQUIREMENTS


def fake_http(routes):
    """routes: list of (url_substring, response-or-Exception). First match wins."""
    def _get(url, params=None):
        for needle, resp in routes:
            if needle in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        raise AssertionError(f"unrouted URL: {url}")
    return _get


def _by_key(signals):
    return {s.key: s for s in signals}


# ── GitHub ─────────────────────────────────────────────────────────────────────

def test_github_discovers_org_controls():
    http = fake_http([
        ("/orgs/acme/audit-log", []),
        ("/orgs/acme/dependabot/alerts", []),
        ("/orgs/acme", {"two_factor_requirement_enabled": True}),
    ])
    sig = _by_key(GitHubConnector("acme", http_get=http).discover())
    assert sig["mfa_enabled"].value is True
    assert sig["audit_logging_enabled"].value is True
    assert sig["threat_detection_enabled"].value is True


def test_github_requires_org():
    with pytest.raises(ConnectorError):
        GitHubConnector("")


def test_github_permission_failure_degrades():
    http = fake_http([
        ("/orgs/acme/audit-log", PermissionError("403")),
        ("/orgs/acme/dependabot/alerts", []),
        ("/orgs/acme", {"two_factor_requirement_enabled": False}),
    ])
    sig = _by_key(GitHubConnector("acme", http_get=http).discover())
    assert sig["audit_logging_enabled"].value is None
    assert sig["mfa_enabled"].value is False


def test_github_policy_is_read_only():
    pol = GitHubConnector("acme", http_get=fake_http([])).least_privilege_policy()
    assert all("Read" in v for v in pol["organization_permissions"].values())


# ── GCP ────────────────────────────────────────────────────────────────────────

def test_gcp_discovers_storage_and_logging():
    http = fake_http([
        ("storage.googleapis.com", {"items": [{
            "location": "ASIA-SOUTH1",
            "iamConfiguration": {"publicAccessPrevention": "enforced"},
            "lifecycle": {"rule": [{"action": {}}]},
            "encryption": {"defaultKmsKeyName": "projects/p/locations/l/keyRings/r/cryptoKeys/k"},
        }]}),
        ("logging.googleapis.com", {"sinks": [{"name": "s1"}]}),
    ])
    sig = _by_key(GCPConnector("proj", region="asia-south1", http_get=http).discover())
    assert sig["has_data_stores"].value is True
    assert sig["storage_encryption"].value is True
    assert sig["public_access_blocked"].value is True
    assert sig["encryption_keys_present"].value is True
    assert sig["audit_logging_enabled"].value is True
    assert "data_outside_india" not in sig  # asia-south1


def test_gcp_flags_cross_border_region():
    http = fake_http([
        ("storage.googleapis.com", {"items": [{"location": "US", "iamConfiguration": {}}]}),
        ("logging.googleapis.com", {"sinks": []}),
    ])
    sig = _by_key(GCPConnector("proj", region="us-central1", http_get=http).discover())
    assert sig["data_outside_india"].value is True
    sug = {s.manifest_field: s for s in signals_to_suggestions(sig.values())}
    assert sug["cross_border_transfer"].action == "review"


# ── Azure ──────────────────────────────────────────────────────────────────────

def test_azure_discovers_storage_keyvault_defender():
    http = fake_http([
        ("Microsoft.Storage/storageAccounts", {"value": [{
            "location": "Central India", "properties": {"allowBlobPublicAccess": False}}]}),
        ("Microsoft.KeyVault/vaults", {"value": [{"name": "kv1"}]}),
        ("Microsoft.Security/pricings", {"value": [{"properties": {"pricingTier": "Standard"}}]}),
    ])
    sig = _by_key(AzureConnector("sub-1", http_get=http).discover())
    assert sig["has_data_stores"].value is True
    assert sig["storage_encryption"].value is True
    assert sig["public_access_blocked"].value is True
    assert sig["encryption_keys_present"].value is True
    assert sig["threat_detection_enabled"].value is True
    assert "data_outside_india" not in sig  # Central India


def test_azure_public_blob_not_blocked_and_cross_border():
    http = fake_http([
        ("Microsoft.Storage/storageAccounts", {"value": [{
            "location": "East US", "properties": {"allowBlobPublicAccess": True}}]}),
        ("Microsoft.KeyVault/vaults", {"value": []}),
        ("Microsoft.Security/pricings", {"value": []}),
    ])
    sig = _by_key(AzureConnector("sub-1", http_get=http).discover())
    assert sig["public_access_blocked"].value is False
    assert sig["data_outside_india"].value is True


# ── Mapping works across providers ─────────────────────────────────────────────

def test_mapping_security_suggestion_from_azure_signals():
    # encryption + logging + access(mfa or PAB). Add audit logging + mfa to complete it.
    sigs = [
        DiscoveredSignal("storage_encryption", True, "azure"),
        DiscoveredSignal("audit_logging_enabled", True, "azure"),
        DiscoveredSignal("public_access_blocked", True, "azure"),
    ]
    sug = {s.manifest_field: s for s in signals_to_suggestions(sigs)}
    sec = sug["has_security_safeguards"]
    assert sec.suggested_value is True and sec.action == "confirm"


# ── Registry ───────────────────────────────────────────────────────────────────

def test_registry_lists_all_four_providers():
    assert set(available_providers()) == {"aws", "gcp", "azure", "github"}
    assert set(CONNECTOR_REQUIREMENTS) == {"aws", "gcp", "azure", "github"}


def test_registry_instantiates_and_rejects_unknown():
    conn = get_connector("github", org="acme", http_get=fake_http([]))
    assert isinstance(conn, Connector) and conn.provider == "github"
    with pytest.raises(ConnectorError):
        get_connector("oracle", foo=1)
