"""Artefact generator API (Tier-1.5)."""

import asyncio

import pytest

import saas.app.artefacts_api as A


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1", "email": "owner@x.com"}
# privacy_notice (DPDP-SEC5-NOTICE-001) is a gap when has_privacy_notice is False.
PROJECT = {"id": "p1", "user_id": "u1",
           "discovered_manifest": {"has_privacy_notice": False, "has_security_safeguards": True}}


class _Col:
    def __init__(self): self.docs = []
    def find(self, q): return [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u, upsert=False):
        d = self.find_one(q)
        if d is None:
            d = dict(q); self.docs.append(d)
        d.update(u.get("$set", {}))


class _FakeCopilot:
    def draft(self, rule, facts, artifact_type):
        return {"mode": "draft", "grounded": True,
                "answer": f"DRAFT — REQUIRES LEGAL REVIEW\n\n{artifact_type} for {rule['rule_id']}",
                "disclaimer": "not legal advice", "model": "claude-opus-4-8"}


def _patch(monkeypatch, role="owner", copilot=None):
    import saas.app.freshness_api as F
    import saas.app.ropa_api as R
    col = _Col()
    monkeypatch.setattr(A, "artefacts_collection", lambda: col)
    # Draft/approve/export all record provenance now; without this they hit real Mongo.
    monkeypatch.setattr(F, "provenance_collection", lambda: _Col())
    monkeypatch.setattr(A, "get_project_with_role", lambda pid, user, action: (PROJECT, role))
    monkeypatch.setattr(A, "get_copilot", lambda: copilot or _FakeCopilot())
    monkeypatch.setattr(A, "insert_audit_log", lambda *a, **k: None)
    monkeypatch.setattr(R, "pii_collection", lambda: _Col())
    return col


def test_needed_lists_artefacts_and_sources(monkeypatch):
    _patch(monkeypatch)
    body = _run(A.list_needed("p1", current_user=USER))
    ids = {a["artefact_id"] for a in body["artefacts"]}
    assert "privacy_notice" in ids
    assert body["we_can_connect_to"] == ["AWS", "GCP", "Azure", "GitHub"]
    assert "sources_legend" in body


def test_draft_requires_consent(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=False, current_user=USER))
    assert e.value.status_code == 400


def test_draft_then_approve_then_export(monkeypatch):
    col = _patch(monkeypatch)
    d = _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    assert d["status"] == "drafted" and "REQUIRES LEGAL REVIEW" in d["content"]
    assert col.find_one({"project_id": "p1", "art_id": "privacy_notice"})["status"] == "drafted"
    # cannot export before approval
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        _run(A.export_approved("p1", current_user=USER))
    assert e.value.status_code == 404
    # approve -> export works
    ap = _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    assert ap["status"] == "approved"
    resp = _run(A.export_approved("p1", current_user=USER))
    assert resp.media_type == "application/zip" and "attachment" in resp.headers["content-disposition"]


def test_draft_unknown_artefact_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "nope", consent_to_send=True, current_user=USER))
    assert e.value.status_code == 404


def test_draft_copilot_failure_502(monkeypatch):
    from fastapi import HTTPException
    class Boom:
        def draft(self, *a): raise RuntimeError("no api key")
    _patch(monkeypatch, copilot=Boom())
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    assert e.value.status_code == 502


def test_approve_requires_a_draft(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    assert e.value.status_code == 404  # nothing drafted yet


def _zip(resp):
    """StreamingResponse -> ZipFile (the export streams, so there is no .body)."""
    import io, zipfile

    async def _drain():
        return b"".join([c async for c in resp.body_iterator])

    return zipfile.ZipFile(io.BytesIO(_run(_drain())))


def test_export_bundles_the_deterministic_ropa_and_dfd(monkeypatch):
    _patch(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    names = set(_zip(_run(A.export_approved("p1", current_user=USER))).namelist())
    assert {"record_of_processing.md", "data_flow_diagram.svg"} <= names


def test_bundled_ropa_is_the_real_register_not_a_stub(monkeypatch):
    _patch(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    z = _zip(_run(A.export_approved("p1", current_user=USER)))
    ropa = z.read("record_of_processing.md").decode()
    assert "# Record of Processing Activities" in ropa
    assert "REQUIRES LEGAL REVIEW" in ropa.upper()
    assert z.read("data_flow_diagram.svg").decode().startswith("<svg")


def test_readme_tells_the_client_the_ropa_is_generated_not_ai_drafted(monkeypatch):
    _patch(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    z = _zip(_run(A.export_approved("p1", current_user=USER)))
    readme = z.read("READ_ME_FIRST.txt").decode()
    assert "record_of_processing.md" in readme and "not AI-drafted" in readme


def test_needed_also_advertises_the_generated_ropa_and_dfd(monkeypatch):
    _patch(monkeypatch)
    body = _run(A.list_needed("p1", current_user=USER))
    generated = {g["artefact_id"]: g for g in body["generated"]}
    assert "record_of_processing" in generated and "data_flow_diagram" in generated
    # Generated artefacts are facts, not drafts — no approval step, no LLM.
    assert all(g["ai_drafted"] is False for g in body["generated"])
    assert generated["record_of_processing"]["endpoint"].endswith("/ropa.md")


# --- provenance: every path a client can download from must leave a stamp -----------------

def _prov_col(monkeypatch):
    """Re-patch the provenance store with a handle the test can assert against."""
    import saas.app.freshness_api as F
    col = _Col()
    monkeypatch.setattr(F, "provenance_collection", lambda: col)
    return col


def test_downloading_the_zip_records_stamps_for_the_generated_artefacts(monkeypatch):
    # Regression: the zip is the primary download path and it recorded nothing, so the
    # freshness report could not speak about the documents the client actually held.
    _patch(monkeypatch)
    prov = _prov_col(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    _run(A.export_approved("p1", current_user=USER))
    stamped = {d["artefact_id"] for d in prov.docs}
    assert {"record_of_processing", "data_flow_diagram"} <= stamped


def test_an_ai_drafted_artefact_is_stamped_with_the_rule_it_rests_on(monkeypatch):
    col = _patch(monkeypatch)
    _prov_col(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    stamp = col.find_one({"project_id": "p1", "art_id": "privacy_notice"})["provenance"]
    assert "DPDP-SEC5-NOTICE-001" in stamp["rules"]
    assert stamp["pack_id"].startswith("dpdp_india")


def test_approving_an_ai_draft_records_its_stamp_for_freshness(monkeypatch):
    _patch(monkeypatch)
    prov = _prov_col(monkeypatch)
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    assert prov.docs == []          # not yet relied upon
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    assert prov.find_one({"project_id": "p1", "artefact_id": "privacy_notice"})


def test_an_eu_artefact_is_stamped_against_the_eu_pack(monkeypatch):
    col = _patch(monkeypatch)
    _prov_col(monkeypatch)
    _run(A.draft_artefact("p1", "risk_management", consent_to_send=True,
                          pack_id="euai_extended_v2", current_user=USER))
    stamp = col.find_one({"project_id": "p1", "art_id": "risk_management"})["provenance"]
    assert stamp["pack_id"].startswith("euai")


def test_the_zip_stamp_survives_a_provenance_store_failure(monkeypatch):
    """A stamping failure must never block the client's download."""
    import saas.app.freshness_api as F
    _patch(monkeypatch)

    class _Boom:
        def update_one(self, *a, **k): raise RuntimeError("mongo down")
    monkeypatch.setattr(F, "provenance_collection", lambda: _Boom())
    _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    names = set(_zip(_run(A.export_approved("p1", current_user=USER))).namelist())
    assert "record_of_processing.md" in names
