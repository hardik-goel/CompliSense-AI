"""Artefact freshness API — is the document the client is holding still current?"""

import asyncio

import saas.app.freshness_api as F
import saas.app.ropa_api as R


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self): self.docs = []
    def insert_one(self, d): self.docs.append(d)
    def find(self, q=None):
        class C(list):
            def sort(self, *a, **k): return self
        q = q or {}
        return C([d for d in self.docs if all(d.get(k) == v for k, v in q.items())])
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u, upsert=False):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(u.get("$set", {})); return
        if upsert:
            self.docs.append({**q, **u.get("$set", {})})


USER = {"id": "u1"}
ANSWERS = {"entity_type": "startup", "sector": "saas", "offers_in_india": True,
           "pii_categories": ["email"], "storage_locations": ["aws"],
           "consent_mechanism": "explicit_optin", "retention_defined": True}
PROJECT = {"id": "p1", "user_id": "u1", "manifest_answers": ANSWERS}


def _patch(monkeypatch):
    prov, projects, pii = _Col(), _Col(), _Col()
    projects.insert_one(PROJECT)
    for mod in (F, R):
        monkeypatch.setattr(mod, "get_project_with_role", lambda pid, u, perm: (PROJECT, "owner"),
                            raising=False)
        monkeypatch.setattr(mod, "insert_audit_log", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(F, "provenance_collection", lambda: prov)
    monkeypatch.setattr(R, "projects_collection", lambda: projects)
    monkeypatch.setattr(R, "pii_collection", lambda: pii)
    return prov


# --- stamping on generation ---------------------------------------------------------------

def test_the_register_carries_a_provenance_stamp(monkeypatch):
    _patch(monkeypatch)
    prov = _run(R.get_ropa("p1", current_user=USER))["ropa"]["provenance"]
    assert prov["pack_id"] and prov["pack_version"]
    assert "DPDP-SEC16-TRANSFER-001" in prov["rules"]


def test_the_stamp_records_the_domains_the_register_covers(monkeypatch):
    _patch(monkeypatch)
    prov = _run(R.get_ropa("p1", current_user=USER))["ropa"]["provenance"]
    assert 4 in prov["domains"]


def test_exporting_the_register_records_its_stamp_for_later_freshness_checks(monkeypatch):
    prov = _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    doc = prov.find_one({"project_id": "p1", "artefact_id": "record_of_processing"})
    assert doc and doc["provenance"]["rules"]
    assert doc["generated_at"]


def test_exporting_the_diagram_records_its_own_stamp(monkeypatch):
    prov = _patch(monkeypatch)
    _run(R.get_dfd_svg("p1", current_user=USER))
    assert prov.find_one({"project_id": "p1", "artefact_id": "data_flow_diagram"})


# --- freshness ------------------------------------------------------------------------------

def test_a_just_exported_artefact_is_fresh(monkeypatch):
    _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    body = _run(F.get_freshness("p1", current_user=USER))
    entry = next(a for a in body["artefacts"] if a["artefact_id"] == "record_of_processing")
    assert entry["status"] == "fresh" and entry["reasons"] == []
    assert body["summary"]["stale"] == 0


def test_a_moved_enforcement_date_turns_the_exported_artefact_stale(monkeypatch):
    prov = _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    # The law moves: the pack now carries a different enforcement date for a cited rule.
    real = F.load_pack

    def _moved(pack_id):
        pack = dict(real(pack_id))
        pack["rules"] = [
            {**r, "enforcement_date": "2029-01-01"} if r["id"] == "DPDP-SEC16-TRANSFER-001" else r
            for r in pack["rules"]
        ]
        return pack

    monkeypatch.setattr(F, "load_pack", _moved)
    body = _run(F.get_freshness("p1", current_user=USER))
    entry = next(a for a in body["artefacts"] if a["artefact_id"] == "record_of_processing")
    assert entry["status"] == "stale"
    reason = next(r for r in entry["reasons"] if r["kind"] == "rule_changed")
    assert reason["rule_id"] == "DPDP-SEC16-TRANSFER-001"
    assert reason["fields"] == ["enforcement_date"]
    assert body["summary"]["stale"] == 1
    assert prov.find_one({"project_id": "p1", "artefact_id": "record_of_processing"})


def test_freshness_reports_nothing_when_nothing_was_ever_exported(monkeypatch):
    _patch(monkeypatch)
    body = _run(F.get_freshness("p1", current_user=USER))
    assert body["artefacts"] == [] and body["summary"]["stale"] == 0


def test_freshness_tells_the_client_what_to_do_about_a_stale_artefact(monkeypatch):
    _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    real = F.load_pack
    monkeypatch.setattr(F, "load_pack", lambda pid: {
        **real(pid), "rules": [r for r in real(pid)["rules"] if r["id"] != "DPDP-SEC16-TRANSFER-001"]})
    entry = _run(F.get_freshness("p1", current_user=USER))["artefacts"][0]
    assert entry["status"] == "stale"
    assert all(r["action"] for r in entry["reasons"])
    assert entry["regenerate"]


# --- the regwatch join ------------------------------------------------------------------------

def test_a_regulatory_change_names_the_artefacts_it_invalidates(monkeypatch):
    _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    body = _run(F.get_change_impact("p1", rule_ids="DPDP-SEC16-TRANSFER-001", current_user=USER))
    assert [h["artefact_id"] for h in body["impacted"]] == ["record_of_processing"]
    assert body["impacted"][0]["via"] == "dependency"


def test_a_change_touching_nothing_the_client_holds_impacts_nothing(monkeypatch):
    _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    body = _run(F.get_change_impact("p1", rule_ids="EUAI-ART9-RISK-MGMT-001", current_user=USER))
    assert body["impacted"] == []


def test_change_impact_accepts_several_rule_ids(monkeypatch):
    _patch(monkeypatch)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    _run(R.get_dfd_svg("p1", current_user=USER))
    body = _run(F.get_change_impact(
        "p1", rule_ids="DPDP-SEC16-TRANSFER-001,DPDP-SEC5-NOTICE-001", current_user=USER))
    assert {h["artefact_id"] for h in body["impacted"]} == {
        "record_of_processing", "data_flow_diagram"}


def test_change_impact_requires_at_least_one_rule_id(monkeypatch):
    import pytest
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(F.get_change_impact("p1", rule_ids="", current_user=USER))
    assert e.value.status_code == 400


# --- early warning: pending regwatch proposals, before any rulepack edit ------------------

def _proposal(change_id, rule_ids, url="https://meity.gov.in/x", status="pending"):
    return {"change_id": change_id, "url": url, "status": status,
            "detected_at": "2026-08-01T00:00:00Z",
            "proposal": {"affected_rule_ids": rule_ids,
                         "source": {"label": "MeitY", "url": url},
                         "proposed_action": "date_change"}}


def test_pending_regwatch_proposals_warn_about_the_documents_they_may_affect(monkeypatch):
    _patch(monkeypatch)
    changes = _Col()
    changes.insert_one(_proposal("c1", ["DPDP-SEC16-TRANSFER-001"]))
    monkeypatch.setattr(F, "changes_collection", lambda: changes)
    _run(R.get_ropa_markdown("p1", current_user=USER))

    body = _run(F.get_regwatch_impact("p1", current_user=USER))
    assert body["pending_changes"] == 1
    warning = body["warnings"][0]
    assert warning["change_id"] == "c1"
    assert [i["artefact_id"] for i in warning["impacted"]] == ["record_of_processing"]


def test_a_reviewed_proposal_is_not_an_open_warning(monkeypatch):
    _patch(monkeypatch)
    changes = _Col()
    changes.insert_one(_proposal("c1", ["DPDP-SEC16-TRANSFER-001"], status="approved"))
    monkeypatch.setattr(F, "changes_collection", lambda: changes)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    assert _run(F.get_regwatch_impact("p1", current_user=USER))["warnings"] == []


def test_a_proposal_touching_nothing_this_client_holds_raises_no_warning(monkeypatch):
    _patch(monkeypatch)
    changes = _Col()
    changes.insert_one(_proposal("c1", ["EUAI-ART9-RISK-MGMT-001"]))
    monkeypatch.setattr(F, "changes_collection", lambda: changes)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    assert _run(F.get_regwatch_impact("p1", current_user=USER))["warnings"] == []


def test_the_warning_says_plainly_that_no_rule_has_been_changed_yet(monkeypatch):
    _patch(monkeypatch)
    changes = _Col()
    changes.insert_one(_proposal("c1", ["DPDP-SEC16-TRANSFER-001"]))
    monkeypatch.setattr(F, "changes_collection", lambda: changes)
    _run(R.get_ropa_markdown("p1", current_user=USER))
    body = _run(F.get_regwatch_impact("p1", current_user=USER))
    note = body["note"].lower()
    assert "no rule has been changed" in note and "nothing has been applied" in note


# --- the pack follows the rules the artefact cites, not a hardcoded constant --------------

def test_pack_is_chosen_by_the_rules_the_artefact_actually_cites():
    dpdp = F.pack_for_rules(["DPDP-SEC16-TRANSFER-001", "DPDP-SEC5-NOTICE-001"])
    eu = F.pack_for_rules(["EUAI-ART9-RISK-MGMT-001"])
    assert dpdp["pack_id"].startswith("dpdp_india")
    assert eu["pack_id"].startswith("euai")


def test_pack_selection_prefers_the_pack_covering_the_most_cited_rules():
    # SEC5 lives in both core and extended; SEC16 only in extended.
    pack = F.pack_for_rules(["DPDP-SEC5-NOTICE-001", "DPDP-SEC16-TRANSFER-001"])
    ids = {r["id"] for r in pack["rules"]}
    assert {"DPDP-SEC5-NOTICE-001", "DPDP-SEC16-TRANSFER-001"} <= ids


def test_unknown_rules_do_not_silently_pick_an_arbitrary_pack():
    assert F.pack_for_rules(["DPDP-NOPE-001"]) is None


def test_no_rules_selects_no_pack():
    assert F.pack_for_rules([]) is None


def test_the_ropa_stamp_names_the_pack_that_actually_holds_its_rules(monkeypatch):
    _patch(monkeypatch)
    prov = _run(R.get_ropa("p1", current_user=USER))["ropa"]["provenance"]
    assert prov["pack_id"] == "dpdp_india_extended_v2"
    assert prov["missing_rule_ids"] == []
