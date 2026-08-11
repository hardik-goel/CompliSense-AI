"""ROPA + DFD API — register, markdown artefact and diagram from project facts."""

import asyncio

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
           "consent_mechanism": "explicit_optin", "retention_defined": True,
           "grievance_email": "dpo@example.com"}


def _patch(monkeypatch, project=None, inferences=None):
    projects, pii, prov = _Col(), _Col(), _Col()
    proj = project or {"id": "p1", "user_id": "u1", "manifest_answers": ANSWERS}
    projects.insert_one(proj)
    for doc in inferences or []:
        pii.insert_one(doc)
    monkeypatch.setattr(R, "projects_collection", lambda: projects)
    monkeypatch.setattr(R, "pii_collection", lambda: pii)
    monkeypatch.setattr(R, "provenance_collection", lambda: prov)
    monkeypatch.setattr(R, "get_project_with_role", lambda pid, u, perm: (proj, "owner"))
    monkeypatch.setattr(R, "insert_audit_log", lambda *a, **k: None)
    return projects, pii, proj


def _flow_doc():
    from compliance.dataflow import DataSource, infer_data_flows
    report = infer_data_flows([
        DataSource(name="users_db", field_names=["email"], provider="aws", region="ap-south-1"),
        DataSource(name="analytics", field_names=["email"], provider="gcp", region="us-central1"),
    ])
    return {"inference_id": "pii_1", "project_id": "p1", "created_at": 1, "report": report}


# --- register ------------------------------------------------------------------------

def test_get_ropa_builds_a_register_from_manifest_answers(monkeypatch):
    _patch(monkeypatch)
    body = _run(R.get_ropa("p1", current_user=USER))
    assert body["project_id"] == "p1"
    assert [r["store"] for r in body["ropa"]["rows"]] == ["aws"]
    assert body["ropa"]["controller"]["grievance_contact"] == "dpo@example.com"


def test_get_ropa_uses_the_latest_stored_data_flow_inference(monkeypatch):
    _patch(monkeypatch, inferences=[_flow_doc()])
    body = _run(R.get_ropa("p1", current_user=USER))
    assert {r["store"] for r in body["ropa"]["rows"]} == {"users_db", "analytics"}
    assert body["ropa"]["has_cross_border"] is True


def test_register_is_stamped_with_a_generation_timestamp(monkeypatch):
    _patch(monkeypatch)
    assert _run(R.get_ropa("p1", current_user=USER))["ropa"]["generated_at"]


# --- declared activities ---------------------------------------------------------------

def test_saving_activities_persists_them_on_the_project(monkeypatch):
    projects, _, _ = _patch(monkeypatch)
    _run(R.save_activities("p1", R.ActivitiesRequest(activities=[R.ActivityIn(
        activity_id="signup", purpose="Account creation", categories=["email"],
        data_principals=["customers"], stores=["users_db"], retention="24 months",
        legal_basis="consent", processors=["AWS"])]), current_user=USER))
    saved = projects.find_one({"id": "p1"})["processing_activities"]
    assert saved[0]["purpose"] == "Account creation"


def test_declared_activities_take_priority_and_can_complete_the_register(monkeypatch):
    project = {"id": "p1", "user_id": "u1", "manifest_answers": ANSWERS,
               "processing_activities": [{
                   "activity_id": "signup", "purpose": "Account creation", "categories": ["email"],
                   "data_principals": ["customers"], "stores": ["users_db"],
                   "retention": "24 months", "legal_basis": "consent", "processors": ["AWS"]}]}
    _patch(monkeypatch, project=project)
    ropa = _run(R.get_ropa("p1", current_user=USER))["ropa"]
    assert ropa["completeness"]["percent"] == 100
    assert ropa["unknowns"] == []
    assert ropa["rows"][0]["purpose"] == "Account creation"


def test_incomplete_register_reports_what_is_still_missing(monkeypatch):
    _patch(monkeypatch)
    body = _run(R.get_ropa("p1", current_user=USER))
    assert body["ropa"]["completeness"]["percent"] < 100
    assert any(u["column"] == "purpose" for u in body["ropa"]["unknowns"])


# --- artefact renders -------------------------------------------------------------------

def test_markdown_export_returns_the_ropa_document(monkeypatch):
    _patch(monkeypatch)
    resp = _run(R.get_ropa_markdown("p1", current_user=USER))
    assert resp.media_type == "text/markdown"
    text = resp.body.decode()
    assert "# Record of Processing Activities" in text
    assert "REQUIRES LEGAL REVIEW" in text.upper()


def test_dfd_export_returns_a_self_contained_svg(monkeypatch):
    _patch(monkeypatch, inferences=[_flow_doc()])
    resp = _run(R.get_dfd_svg("p1", current_user=USER))
    assert resp.media_type == "image/svg+xml"
    svg = resp.body.decode()
    assert svg.startswith("<svg") and "users_db" in svg and "<script" not in svg


def test_dfd_marks_the_india_boundary_when_a_store_sits_abroad(monkeypatch):
    _patch(monkeypatch, inferences=[_flow_doc()])
    assert "Outside India" in _run(R.get_dfd_svg("p1", current_user=USER)).body.decode()


# --- guardrails --------------------------------------------------------------------------

def test_every_read_goes_through_project_rbac(monkeypatch):
    seen = []
    _patch(monkeypatch)
    monkeypatch.setattr(R, "get_project_with_role",
                        lambda pid, u, perm: (seen.append(perm), ({"id": pid, "manifest_answers": ANSWERS}, "owner"))[1])
    _run(R.get_ropa("p1", current_user=USER))
    _run(R.get_ropa_markdown("p1", current_user=USER))
    _run(R.get_dfd_svg("p1", current_user=USER))
    assert seen == ["view", "view", "view"]


def test_saving_activities_requires_edit_permission(monkeypatch):
    seen = []
    projects, _, proj = _patch(monkeypatch)
    monkeypatch.setattr(R, "get_project_with_role",
                        lambda pid, u, perm: (seen.append(perm), (proj, "owner"))[1])
    _run(R.save_activities("p1", R.ActivitiesRequest(activities=[]), current_user=USER))
    assert seen == ["edit_project"]
