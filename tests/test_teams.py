"""Teams & roles API (Phase 8)."""

import asyncio

import pytest

import saas.app.teams as T


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self): self.docs = []
    def insert_one(self, d): self.docs.append(d)
    def find(self, q): return [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def count_documents(self, q): return len(self.find(q))
    def update_one(self, q, u):
        m = self.find_one(q)
        if m: m.update(u.get("$set", {})); return type("R", (), {"matched_count": 1})()
        return type("R", (), {"matched_count": 0})()
    def delete_one(self, q):
        m = self.find_one(q)
        if m: self.docs.remove(m)


def _patch(monkeypatch):
    teams, members, projects, users = _Col(), _Col(), _Col(), _Col()
    monkeypatch.setattr(T, "teams_collection", lambda: teams)
    monkeypatch.setattr(T, "team_members_collection", lambda: members)
    monkeypatch.setattr(T, "projects_collection", lambda: projects)
    monkeypatch.setattr(T, "users_collection", lambda: users)
    return teams, members, projects, users


OWNER = {"id": "u1", "email": "owner@x.com"}
OTHER = {"id": "u2", "email": "bob@x.com"}


def test_create_team_makes_creator_owner(monkeypatch):
    _, members, _, _ = _patch(monkeypatch)
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    assert team["name"] == "Acme"
    assert members.find_one({"team_id": team["id"], "user_id": "u1"})["role"] == "owner"


def test_invite_and_list_members(monkeypatch):
    _, members, _, users = _patch(monkeypatch)
    users.insert_one({"id": "u2", "email": "bob@x.com"})
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    _run(T.invite_member(team["id"], T.MemberInvite(email="bob@x.com", role="member"), current_user=OWNER))
    listed = _run(T.list_members(team["id"], current_user=OWNER))
    assert len(listed["members"]) == 2
    bob = members.find_one({"team_id": team["id"], "user_id": "u2"})
    assert bob["role"] == "member" and bob["status"] == "active"


def test_invite_pending_when_user_unknown(monkeypatch):
    _, members, _, _ = _patch(monkeypatch)
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    m = _run(T.invite_member(team["id"], T.MemberInvite(email="new@x.com", role="viewer"), current_user=OWNER))
    assert m["status"] == "pending" and m["user_id"] is None


def test_member_cannot_manage_members(monkeypatch):
    from fastapi import HTTPException
    _, members, _, users = _patch(monkeypatch)
    users.insert_one({"id": "u2", "email": "bob@x.com"})
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    _run(T.invite_member(team["id"], T.MemberInvite(email="bob@x.com", role="member"), current_user=OWNER))
    with pytest.raises(HTTPException) as e:
        _run(T.invite_member(team["id"], T.MemberInvite(email="x@x.com", role="member"), current_user=OTHER))
    assert e.value.status_code == 403


def test_update_and_remove_role(monkeypatch):
    _, members, _, users = _patch(monkeypatch)
    users.insert_one({"id": "u2", "email": "bob@x.com"})
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    _run(T.invite_member(team["id"], T.MemberInvite(email="bob@x.com", role="viewer"), current_user=OWNER))
    _run(T.update_member_role(team["id"], "u2", T.RoleUpdate(role="admin"), current_user=OWNER))
    assert members.find_one({"team_id": team["id"], "user_id": "u2"})["role"] == "admin"
    _run(T.remove_member(team["id"], "u2", current_user=OWNER))
    assert members.find_one({"team_id": team["id"], "user_id": "u2"}) is None


def test_cannot_remove_owner(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    with pytest.raises(HTTPException) as e:
        _run(T.remove_member(team["id"], "u1", current_user=OWNER))
    assert e.value.status_code == 400


def test_resolve_project_role_and_access(monkeypatch):
    from fastapi import HTTPException
    teams, members, projects, users = _patch(monkeypatch)
    users.insert_one({"id": "u2", "email": "bob@x.com"})
    team = _run(T.create_team(T.TeamCreate(name="Acme"), current_user=OWNER))
    _run(T.invite_member(team["id"], T.MemberInvite(email="bob@x.com", role="viewer"), current_user=OWNER))
    projects.insert_one({"id": "p1", "user_id": "u1", "team_id": team["id"], "name": "P1"})
    # owner
    assert T.resolve_project_role(projects.find_one({"id": "p1"}), "u1") == "owner"
    # team viewer
    assert T.resolve_project_role(projects.find_one({"id": "p1"}), "u2") == "viewer"
    # viewer can export_evidence
    proj, role = T.get_project_with_role("p1", OTHER, "export_evidence")
    assert role == "viewer"
    # viewer cannot delete
    with pytest.raises(HTTPException) as e:
        T.get_project_with_role("p1", OTHER, "delete_project")
    assert e.value.status_code == 403
    # non-member: 404 (no leak)
    with pytest.raises(HTTPException) as e:
        T.get_project_with_role("p1", {"id": "u9"}, "view")
    assert e.value.status_code == 404
