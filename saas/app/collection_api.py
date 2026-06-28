"""Declare collection sources on a project (Tier-1.5 / 6.5).

Stores only NON-SECRET source config (bucket, prefix, repo, path, …). Credentials are supplied
locally when the downloaded agent runs the collectors — they never reach the backend. This config
is embedded into the agent bundle so the agent knows what to collect.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from agent.db.mongo import insert_audit_log
from compliance.collection_config import CollectionConfigError, validate_source
from saas.app.auth import get_current_user
from saas.app.database import get_collection
from saas.app.teams import get_project_with_role

router = APIRouter(prefix="/projects", tags=["collection"])


def _projects():
    return get_collection("projects")


def _sources(project: dict[str, Any]) -> list[dict[str, Any]]:
    return project.get("collection_sources") or []


@router.get("/{project_id}/collection/sources")
async def list_sources(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    project, _ = get_project_with_role(project_id, current_user, "view")
    return {"project_id": project_id, "sources": _sources(project)}


@router.post("/{project_id}/collection/sources")
async def add_source(project_id: str, body: dict[str, Any],
                     current_user: dict[str, Any] = Depends(get_current_user)):
    project, _ = get_project_with_role(project_id, current_user, "edit_project")
    try:
        norm = validate_source(body)
    except CollectionConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    norm["id"] = uuid.uuid4().hex[:12]
    sources = _sources(project) + [norm]
    _projects().update_one({"id": project_id}, {"$set": {"collection_sources": sources}})
    _audit(current_user, project_id, "collection_source_add", {"type": norm["type"]})
    return {"project_id": project_id, "source": norm}


@router.delete("/{project_id}/collection/sources/{source_id}")
async def remove_source(project_id: str, source_id: str,
                        current_user: dict[str, Any] = Depends(get_current_user)):
    project, _ = get_project_with_role(project_id, current_user, "edit_project")
    sources = _sources(project)
    kept = [s for s in sources if s.get("id") != source_id]
    if len(kept) == len(sources):
        raise HTTPException(status_code=404, detail="source not found")
    _projects().update_one({"id": project_id}, {"$set": {"collection_sources": kept}})
    _audit(current_user, project_id, "collection_source_remove", {"source_id": source_id})
    return {"project_id": project_id, "removed": source_id}


@router.get("/{project_id}/collection/config.json")
async def collection_config(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """The non-secret config the agent uses to drive collection."""
    project, _ = get_project_with_role(project_id, current_user, "view")
    return {
        "project_id": project_id,
        "sources": [{"type": s["type"], "label": s.get("label"), "config": s.get("config", {})}
                    for s in _sources(project)],
        "note": "Credentials are supplied locally when the agent runs; they are not stored here.",
    }


def _audit(user: dict[str, Any], project_id: str, source: str, meta: dict[str, Any]) -> None:
    try:
        insert_audit_log({"user_id": user["id"], "project_id": project_id, "source": source,
                          "status": "ok", "timestamp": dt.datetime.utcnow(), "metadata": meta})
    except Exception:
        pass
