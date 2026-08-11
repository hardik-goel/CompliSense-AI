"""Scheduled sweeps that turn artefact freshness into something a client is told about.

An endpoint only fires when someone thinks to call it. These sweeps are what make
"we monitor the law" a benefit the client receives rather than a backlog we keep.
"""

import datetime as dt

import saas.app.freshness_api as F
from compliance.provenance import build_provenance

NOW = dt.datetime(2026, 8, 11, 6, 0, 0)


class _Col:
    def __init__(self, docs=None): self.docs = list(docs or [])
    def insert_one(self, d): self.docs.append(d)
    def find(self, q=None):
        q = q or {}
        return [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)


def _pack(rules, version="2.1.0"):
    return {"pack_id": "dpdp_india_extended_v2", "pack_version": version, "rules": rules}


RULE = {"id": "DPDP-SEC16-TRANSFER-001", "clause": "Section 16",
        "act_citation": "DPDP Act 2023, s.16", "enforcement_date": "2027-05-13",
        "status": "phased_not_yet_in_force"}


def _patch(monkeypatch, *, pack, stamped_against, changes=None):
    alerts = []
    prov = _Col([{"project_id": "p1", "artefact_id": "record_of_processing",
                  "generated_at": "2026-08-01T00:00:00Z",
                  "provenance": build_provenance(stamped_against, [RULE["id"]])}])
    projects = _Col([{"id": "p1", "user_id": "u1", "name": "Acme"}])
    monkeypatch.setattr(F, "provenance_collection", lambda: prov)
    monkeypatch.setattr(F, "projects_collection", lambda: projects)
    monkeypatch.setattr(F, "changes_collection", lambda: _Col(changes or []))
    monkeypatch.setattr(F, "load_pack", lambda pid: pack)
    monkeypatch.setattr(F, "create_alert",
                        lambda **kw: (alerts.append(kw), kw)[1])
    return alerts


# --- staleness sweep ------------------------------------------------------------------------

def test_a_moved_rule_raises_a_stale_artefact_alert(monkeypatch):
    base = _pack([RULE])
    moved = _pack([{**RULE, "enforcement_date": "2029-01-01"}], version="2.2.0")
    alerts = _patch(monkeypatch, pack=moved, stamped_against=base)
    created = F.evaluate_artefact_freshness(now=NOW)
    assert len(created) == 1
    alert = alerts[0]
    assert alert["alert_type"] == "artefact_stale"
    assert "Record of Processing" in alert["message"]
    assert alert["detail"]["artefact_id"] == "record_of_processing"
    assert any(r["kind"] == "rule_changed" for r in alert["detail"]["reasons"])


def test_an_unchanged_pack_raises_nothing(monkeypatch):
    base = _pack([RULE])
    _patch(monkeypatch, pack=base, stamped_against=base)
    assert F.evaluate_artefact_freshness(now=NOW) == []


def test_a_pack_bump_that_leaves_the_artefact_alone_does_not_alert(monkeypatch):
    base = _pack([RULE])
    bumped = _pack([RULE, {"id": "DPDP-SEC5-NOTICE-001"}], version="2.2.0")
    _patch(monkeypatch, pack=bumped, stamped_against=base)
    assert F.evaluate_artefact_freshness(now=NOW) == []


def test_the_stale_alert_is_deduped_per_project_artefact_and_day(monkeypatch):
    base = _pack([RULE])
    moved = _pack([{**RULE, "status": "in_force"}], version="2.2.0")
    alerts = _patch(monkeypatch, pack=moved, stamped_against=base)
    F.evaluate_artefact_freshness(now=NOW)
    assert alerts[0]["dedupe_key"] == "artefact_stale:p1:record_of_processing:2026-08-11"


def test_the_stale_alert_tells_the_client_what_to_do(monkeypatch):
    base = _pack([RULE])
    moved = _pack([{**RULE, "status": "in_force"}], version="2.2.0")
    alerts = _patch(monkeypatch, pack=moved, stamped_against=base)
    F.evaluate_artefact_freshness(now=NOW)
    assert "re-generate" in alerts[0]["message"].lower()
    assert alerts[0]["user_id"] == "u1"


# --- regwatch exposure sweep ------------------------------------------------------------------

def _proposal(rule_ids, status="pending"):
    return {"change_id": "c1", "status": status, "url": "https://meity.gov.in/x",
            "detected_at": "2026-08-10T00:00:00Z",
            "proposal": {"affected_rule_ids": rule_ids,
                         "source": {"label": "MeitY", "url": "https://meity.gov.in/x"}}}


def test_a_pending_change_touching_a_held_document_raises_an_exposure_alert(monkeypatch):
    base = _pack([RULE])
    alerts = _patch(monkeypatch, pack=base, stamped_against=base,
                    changes=[_proposal([RULE["id"]])])
    created = F.evaluate_regwatch_exposure(now=NOW)
    assert len(created) == 1
    assert alerts[0]["alert_type"] == "regwatch_exposure"
    assert alerts[0]["detail"]["change_id"] == "c1"
    assert "record_of_processing" in alerts[0]["detail"]["artefact_ids"]


def test_a_pending_change_touching_nothing_held_raises_no_alert(monkeypatch):
    base = _pack([RULE])
    _patch(monkeypatch, pack=base, stamped_against=base,
           changes=[_proposal(["EUAI-ART9-RISK-MGMT-001"])])
    assert F.evaluate_regwatch_exposure(now=NOW) == []


def test_an_already_reviewed_change_raises_no_alert(monkeypatch):
    base = _pack([RULE])
    _patch(monkeypatch, pack=base, stamped_against=base,
           changes=[_proposal([RULE["id"]], status="approved")])
    assert F.evaluate_regwatch_exposure(now=NOW) == []


def test_the_exposure_alert_says_no_rule_has_changed_yet(monkeypatch):
    base = _pack([RULE])
    alerts = _patch(monkeypatch, pack=base, stamped_against=base,
                    changes=[_proposal([RULE["id"]])])
    F.evaluate_regwatch_exposure(now=NOW)
    msg = alerts[0]["message"].lower()
    assert "not yet" in msg or "no rule has changed" in msg
    assert alerts[0]["severity"] == "low"


def test_the_exposure_alert_is_deduped_per_project_and_change(monkeypatch):
    base = _pack([RULE])
    alerts = _patch(monkeypatch, pack=base, stamped_against=base,
                    changes=[_proposal([RULE["id"]])])
    F.evaluate_regwatch_exposure(now=NOW)
    assert alerts[0]["dedupe_key"] == "regwatch_exposure:p1:c1"


# --- the cron entrypoint runs both -------------------------------------------------------------

def test_the_monitoring_cron_runs_the_freshness_sweeps(monkeypatch):
    import saas.app.monitoring_cron as C
    calls = []
    monkeypatch.setattr(C, "evaluate_overdue_scans", lambda: calls.append("overdue") or [])
    monkeypatch.setattr(C, "evaluate_artefact_freshness", lambda: calls.append("stale") or [])
    monkeypatch.setattr(C, "evaluate_regwatch_exposure", lambda: calls.append("exposure") or [])
    assert C.main() == 0
    assert calls == ["overdue", "stale", "exposure"]
