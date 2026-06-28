"""Gap assignment & sign-off workflow (Phase 8 governance)."""

import asyncio

import pytest

import saas.app.gaps_api as G


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self): self.docs = []
    def find(self, q): return [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u, upsert=False):
        d = self.find_one(q)
        if d is None:
            d = dict(q); d.update(u.get("$setOnInsert", {})); self.docs.append(d)
        d.update(u.get("$set", {}))


ADMIN = {"id": "u1", "email": "admin@x.com"}
MEMBER = {"id": "u2", "email": "m@x.com"}
PROJECT = {"id": "p1", "user_id": "owner", "team_id": "t1"}


def _patch(monkeypatch, actor_role="admin", assignee_role="member"):
    gaps = _Col()
    monkeypatch.setattr(G, "gap_states_collection", lambda: gaps)
    monkeypatch.setattr(G, "get_project_with_role",
                        lambda pid, user, action: (PROJECT, actor_role) if _ok(actor_role, action)
                        else _raise403(actor_role, action))
    monkeypatch.setattr(G, "resolve_project_role", lambda project, uid: assignee_role if uid == "u2" else None)
    monkeypatch.setattr(G, "insert_audit_log", lambda *a, **k: None)
    return gaps


def _ok(role, action):
    from saas.app.rbac import can
    return can(role, action)


def _raise403(role, action):
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail=f"{role} may not {action}")


def test_assign_then_signoff_flow(monkeypatch):
    gaps = _patch(monkeypatch)
    a = _run(G.assign_gap("p1", "DPDP-SEC5-NOTICE-001", G.AssignRequest(assignee_user_id="u2"), current_user=ADMIN))
    assert a["status"] == "assigned" and a["assignee_user_id"] == "u2"
    s = _run(G.sign_off_gap("p1", "DPDP-SEC5-NOTICE-001", G.SignoffRequest(note="done"), current_user=ADMIN))
    assert s["status"] == "signed_off" and s["signed_off_by"] == "u1"
    doc = gaps.find_one({"project_id": "p1", "rule_id": "DPDP-SEC5-NOTICE-001"})
    assert doc["status"] == "signed_off" and doc["assignee_user_id"] == "u2" and doc["signoff_note"] == "done"


def test_assign_rejects_non_member_assignee(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, assignee_role="member")
    with pytest.raises(HTTPException) as e:
        _run(G.assign_gap("p1", "R1", G.AssignRequest(assignee_user_id="stranger"), current_user=ADMIN))
    assert e.value.status_code == 400  # resolve_project_role -> None for non-u2


def test_member_cannot_sign_off(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, actor_role="member")  # member fails sign_off_gap (admin-only)
    with pytest.raises(HTTPException) as e:
        _run(G.sign_off_gap("p1", "R1", G.SignoffRequest(), current_user=MEMBER))
    assert e.value.status_code == 403


def test_list_gap_states(monkeypatch):
    gaps = _patch(monkeypatch, actor_role="viewer")
    gaps.docs.append({"project_id": "p1", "rule_id": "R1", "status": "assigned"})
    out = _run(G.list_gap_states("p1", current_user=ADMIN))
    assert out["count"] == 1
