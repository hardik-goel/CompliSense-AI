"""Gap assignment & sign-off workflow (Phase 8 governance layer).

On top of the Phase-8 RBAC + teams layer: assign a specific readiness gap (rule) to a team
member, and let an admin/owner sign it off (attestation). Every action is audit-logged, so
there is a record of who assigned and who approved what.

State is one ``gap_states`` doc per (project_id, rule_id), upserted as it moves
open -> assigned -> signed_off.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.teams import get_project_with_role, resolve_project_role

router = APIRouter(prefix="/projects", tags=["gaps"])


def gap_states_collection():
    return get_collection("gap_states")


class AssignRequest(BaseModel):
    assignee_user_id: str = Field(min_length=1, max_length=120)
    note: str = Field(default="", max_length=2000)


class SignoffRequest(BaseModel):
    note: str = Field(default="", max_length=2000)


def _audit(user_id: str, project_id: str, source: str, status: str, meta: dict[str, Any]) -> None:
    try:
        insert_audit_log({"user_id": user_id, "project_id": project_id, "source": source,
                          "status": status, "timestamp": dt.datetime.utcnow(), "metadata": meta})
    except Exception:
        pass


@router.get("/{project_id}/gaps")
async def list_gap_states(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_with_role(project_id, current_user, "view")
    docs = list(gap_states_collection().find({"project_id": project_id}))
    return {"project_id": project_id, "count": len(docs), "gaps": [serialize_document(d) for d in docs]}


@router.post("/{project_id}/gaps/{rule_id}/assign")
async def assign_gap(project_id: str, rule_id: str, body: AssignRequest,
                     current_user: dict[str, Any] = Depends(get_current_user)):
    project, _role = get_project_with_role(project_id, current_user, "assign_gap")
    # The assignee must themselves have access to the project (owner or team member).
    if resolve_project_role(project, body.assignee_user_id) is None:
        raise HTTPException(status_code=400, detail="Assignee is not a member of this project's team")
    now = dt.datetime.utcnow()
    gap_states_collection().update_one(
        {"project_id": project_id, "rule_id": rule_id},
        {"$set": {"project_id": project_id, "rule_id": rule_id, "status": "assigned",
                  "assignee_user_id": body.assignee_user_id, "assigned_by": current_user["id"],
                  "assigned_at": now, "note": body.note, "updated_at": now},
         "$setOnInsert": {"signed_off_by": None, "signed_off_at": None}},
        upsert=True)
    _audit(current_user["id"], project_id, "gap_assign", "assigned",
           {"rule_id": rule_id, "assignee_user_id": body.assignee_user_id})
    return {"project_id": project_id, "rule_id": rule_id, "status": "assigned",
            "assignee_user_id": body.assignee_user_id}


@router.post("/{project_id}/gaps/{rule_id}/signoff")
async def sign_off_gap(project_id: str, rule_id: str, body: SignoffRequest,
                       current_user: dict[str, Any] = Depends(get_current_user)):
    """Attest that a gap has been addressed. Admin/owner only; recorded + audited.

    Readiness framing: a sign-off is an internal attestation that the readiness item has been
    handled — it is not a determination of legal compliance.
    """
    get_project_with_role(project_id, current_user, "sign_off_gap")
    now = dt.datetime.utcnow()
    gap_states_collection().update_one(
        {"project_id": project_id, "rule_id": rule_id},
        {"$set": {"project_id": project_id, "rule_id": rule_id, "status": "signed_off",
                  "signed_off_by": current_user["id"], "signed_off_by_email": current_user.get("email"),
                  "signed_off_at": now, "signoff_note": body.note, "updated_at": now}},
        upsert=True)
    _audit(current_user["id"], project_id, "gap_signoff", "signed_off",
           {"rule_id": rule_id, "note": body.note})
    return {"project_id": project_id, "rule_id": rule_id, "status": "signed_off",
            "signed_off_by": current_user["id"]}
