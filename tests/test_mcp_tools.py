"""CompliSense MCP tool registry (Phase 6.1) — pure, no `mcp` SDK needed."""

import pytest

from mcp_server.tools import call_tool, list_tools


def test_list_tools_descriptors_well_formed():
    tools = list_tools()
    names = {t["name"] for t in tools}
    assert {"list_rulepacks", "list_rules", "get_questionnaire", "score_readiness",
            "infer_pii", "infer_data_flows", "list_connectors", "connector_policy"} <= names
    for t in tools:
        assert t["description"] and t["inputSchema"]["type"] == "object"


def test_list_rulepacks():
    out = call_tool("list_rulepacks")
    assert any(p["pack_id"] == "dpdp_india_core_v1" for p in out["rulepacks"])


def test_list_rules_with_citations():
    out = call_tool("list_rules", {"pack_id": "dpdp_india_core_v1"})
    assert out["count"] > 0
    r = out["rules"][0]
    assert "rule_id" in r and "framing" in r and "act_citation" in r


def test_list_rules_unknown_pack_raises():
    with pytest.raises(ValueError):
        call_tool("list_rules", {"pack_id": "nope"})


def test_get_questionnaire():
    out = call_tool("get_questionnaire")
    assert len(out["questions"]) > 5


def test_score_readiness():
    out = call_tool("score_readiness", {"answers": {"entity_type": "startup", "has_privacy_notice": True}})
    assert "readiness_score" in out and "disclaimer" in out


def test_score_readiness_scores_eu_pack():
    out = call_tool("score_readiness", {"answers": {"has_ai_system": True}, "pack_id": "euai_core_v1"})
    assert out["jurisdiction"] == "EU_AI_ACT" and "readiness_score" in out


def test_score_readiness_rejects_unknown_pack():
    with pytest.raises(ValueError):
        call_tool("score_readiness", {"answers": {}, "pack_id": "uk_core_v1"})


def test_infer_pii_names_only():
    out = call_tool("infer_pii", {"field_names": ["user_email", "aadhaar"]})
    cats = {f["category"] for f in out["findings"]}
    assert {"email", "government_id"} <= cats
    assert out["suggestion"]["manifest_field"] == "pii_categories"
    assert "never values" in out["note"].lower()


def test_infer_data_flows():
    out = call_tool("infer_data_flows", {"sources": [
        {"name": "db", "field_names": ["email", "latitude"], "provider": "gcp", "region": "us-east1"}]})
    assert out["has_cross_border"] is True


def test_infer_data_flows_requires_sources():
    with pytest.raises(ValueError):
        call_tool("infer_data_flows", {"sources": []})


def test_list_connectors_and_policy():
    cons = call_tool("list_connectors")
    assert set(cons["providers"]) == {"aws", "gcp", "azure", "github"}
    pol = call_tool("connector_policy", {"provider": "aws"})
    assert "least_privilege_policy" in pol


def test_connector_policy_unknown_provider():
    with pytest.raises(ValueError):
        call_tool("connector_policy", {"provider": "oracle"})


def test_unknown_tool_raises_keyerror():
    with pytest.raises(KeyError):
        call_tool("does_not_exist")


def test_server_module_imports_without_mcp_sdk():
    # The transport must import even though `mcp` is not installed (lazy import in main()).
    import mcp_server.server as srv
    assert srv.SERVER_NAME == "complisense"
