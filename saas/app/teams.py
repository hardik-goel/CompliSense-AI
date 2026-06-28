"""Teams & multi-team roles (Phase 8).

Adds an optional team layer on top of the existing single-owner projects: a project keeps
its `user_id` owner, and may also be attached to a team whose members get role-gated access
(viewer / member / admin / owner). Existing owner-only flows are unchanged; team access is
additive and governs the new role-gated endpoints (evidence export, etc.).
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from saas.app.auth import get_current_user, users_collection
from saas.app.database import get_collection, serialize_document
from saas.app.projects import projects_collection
from saas.app.rbac import ROLES, can, role_at_least

router = APIRouter(tags=["teams"])


def teams_collection():
    return get_collection("teams")


def team_members_collection():
    return get_collection("team_members")


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class MemberInvite(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    role: str = "member"


class RoleUpdate(BaseModel):
    role: str


class AttachTeam(BaseModel):
    team_id: str


def _team_role(team_id: str, user_id: str) -> str | None:
    member = team_members_collection().find_one({"team_id": team_id, "user_id": user_id})
    return member.get("role") if member else None


def require_team_action(team_id: str, user: dict[str, Any], action: str) -> str:
    """Return the user's role in the team after asserting they may perform ``action``."""
    if not teams_collection().find_one({"id": team_id}):
        raise HTTPException(status_code=404, detail="Team not found")
    role = _team_role(team_id, user["id"])
    if role is None:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    if not can(role, action):
        raise HTTPException(status_code=403, detail=f"Role '{role}' may not {action}")
    return role


def resolve_project_role(project: dict[str, Any], user_id: str) -> str | None:
    """The user's effective role on a project: owner if they own it, else their team role."""
    if project.get("user_id") == user_id:
        return "owner"
    team_id = project.get("team_id")
    if team_id:
        return _team_role(team_id, user_id)
    return None


def get_project_with_role(project_id: str, user: dict[str, Any], action: str) -> tuple[dict[str, Any], str]:
    """Load a project and assert the user's effective role permits ``action`` (owner or team)."""
    project = projects_collection().find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = resolve_project_role(project, user["id"])
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")  # don't leak existence
    if not can(role, action):
        raise HTTPException(status_code=403, detail=f"Role '{role}' may not {action}")
    return project, role


# ── team endpoints ───────────────────────────────────────────────────────────

@router.post("/teams")
async def create_team(body: TeamCreate, current_user: dict[str, Any] = Depends(get_current_user)):
    now = dt.datetime.utcnow()
    team = {"id": f"team_{uuid.uuid4().hex[:8]}", "name": body.name.strip(),
            "owner_id": current_user["id"], "created_at": now}
    teams_collection().insert_one(team)
    team_members_collection().insert_one({
        "team_id": team["id"], "user_id": current_user["id"], "email": current_user.get("email"),
        "role": "owner", "created_at": now})
    return serialize_document(team)


@router.get("/teams")
async def list_teams(current_user: dict[str, Any] = Depends(get_current_user)):
    memberships = list(team_members_collection().find({"user_id": current_user["id"]}))
    out = []
    for m in memberships:
        team = teams_collection().find_one({"id": m["team_id"]})
        if team:
            clean = serialize_document(team)
            clean["my_role"] = m.get("role")
            clean["member_count"] = team_members_collection().count_documents({"team_id": team["id"]})
            out.append(clean)
    return {"count": len(out), "teams": out}


@router.get("/teams/{team_id}/members")
async def list_members(team_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    require_team_action(team_id, current_user, "view")
    members = list(team_members_collection().find({"team_id": team_id}))
    return {"team_id": team_id, "members": [serialize_document(m) for m in members]}


@router.post("/teams/{team_id}/members")
async def invite_member(team_id: str, body: MemberInvite, current_user: dict[str, Any] = Depends(get_current_user)):
    require_team_action(team_id, current_user, "manage_members")
    role = body.role.strip().lower()
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {list(ROLES)}")
    email = body.email.strip().lower()
    invited = users_collection().find_one({"email": email})
    user_id = invited["id"] if invited else None  # pending until they register
    existing = team_members_collection().find_one({"team_id": team_id, "email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Already a member or invited")
    member = {"team_id": team_id, "user_id": user_id, "email": email, "role": role,
              "status": "active" if user_id else "pending", "created_at": dt.datetime.utcnow()}
    team_members_collection().insert_one(member)
    return serialize_document(member)


@router.put("/teams/{team_id}/members/{member_user_id}")
async def update_member_role(team_id: str, member_user_id: str, body: RoleUpdate,
                             current_user: dict[str, Any] = Depends(get_current_user)):
    require_team_action(team_id, current_user, "manage_members")
    role = body.role.strip().lower()
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {list(ROLES)}")
    result = team_members_collection().update_one(
        {"team_id": team_id, "user_id": member_user_id}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"team_id": team_id, "user_id": member_user_id, "role": role}


@router.delete("/teams/{team_id}/members/{member_user_id}")
async def remove_member(team_id: str, member_user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    require_team_action(team_id, current_user, "manage_members")
    team = teams_collection().find_one({"id": team_id})
    if team and team.get("owner_id") == member_user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the team owner")
    team_members_collection().delete_one({"team_id": team_id, "user_id": member_user_id})
    return {"removed": member_user_id}


@router.post("/projects/{project_id}/team")
async def attach_project_to_team(project_id: str, body: AttachTeam,
                                 current_user: dict[str, Any] = Depends(get_current_user)):
    """Attach a project to a team. Only the project owner may do this."""
    project = projects_collection().find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # The actor must be at least an admin of the target team.
    require_team_action(body.team_id, current_user, "manage_members")
    projects_collection().update_one({"id": project_id}, {"$set": {"team_id": body.team_id}})
    return {"project_id": project_id, "team_id": body.team_id}
