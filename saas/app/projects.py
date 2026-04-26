from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    model_type: str = Field(min_length=1, max_length=120)
    compliance_standard: str = Field(default="EU_AI_ACT", min_length=1, max_length=120)
    industry: str | None = Field(default=None, max_length=120)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    model_type: str | None = Field(default=None, min_length=1, max_length=120)
    industry: str | None = Field(default=None, max_length=120)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    model_type: str
    compliance_standard: str
    industry: str | None = None
    user_id: str
    created_at: str
    updated_at: str
    scan_count: int = 0


class ScanConfiguration(BaseModel):
    project_id: str
    scan_name: str = Field(min_length=1, max_length=120)
    rulepack_version: str = Field(default="euai_core_v1", min_length=1, max_length=120)
    custom_checks: list[str] | None = None
    output_format: list[str] = Field(default_factory=lambda: ["pdf", "json"])
    notify_on_completion: bool = True


def projects_collection():
    return get_collection("projects")


def scans_collection():
    return get_collection("scans")


def _serialize_project(project: dict[str, Any]) -> dict[str, Any]:
    return serialize_document(project)


def _serialize_scan(scan: dict[str, Any]) -> dict[str, Any]:
    return serialize_document(scan)


def get_project_for_user(project_id: str, user_id: str) -> dict[str, Any]:
    project = projects_collection().find_one({"id": project_id, "user_id": user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, current_user: dict[str, Any] = Depends(get_current_user)):
    now = dt.datetime.utcnow()
    project = {
        "id": f"proj_{uuid.uuid4().hex[:8]}",
        "name": project_data.name.strip(),
        "description": project_data.description,
        "model_type": project_data.model_type.strip(),
        "compliance_standard": project_data.compliance_standard.strip(),
        "industry": project_data.industry,
        "user_id": current_user["id"],
        "created_at": now,
        "updated_at": now,
    }
    projects_collection().insert_one(project)
    clean_project = _serialize_project(project)
    clean_project["scan_count"] = 0
    return ProjectResponse(**clean_project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(current_user: dict[str, Any] = Depends(get_current_user)):
    project_docs = list(projects_collection().find({"user_id": current_user["id"]}).sort("created_at", -1))
    responses: list[ProjectResponse] = []
    for project in project_docs:
        clean_project = _serialize_project(project)
        clean_project["scan_count"] = scans_collection().count_documents({"project_id": clean_project["id"]})
        responses.append(ProjectResponse(**clean_project))
    return responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    project = get_project_for_user(project_id, current_user["id"])
    clean_project = _serialize_project(project)
    clean_project["scan_count"] = scans_collection().count_documents({"project_id": project_id})
    return ProjectResponse(**clean_project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    project = get_project_for_user(project_id, current_user["id"])
    update_data = project_data.model_dump(exclude_unset=True)
    if not update_data:
        clean_project = _serialize_project(project)
        clean_project["scan_count"] = scans_collection().count_documents({"project_id": project_id})
        return ProjectResponse(**clean_project)

    update_data["updated_at"] = dt.datetime.utcnow()
    projects_collection().update_one({"id": project_id}, {"$set": update_data})
    updated = projects_collection().find_one({"id": project_id})
    clean_project = _serialize_project(updated)
    clean_project["scan_count"] = scans_collection().count_documents({"project_id": project_id})
    return ProjectResponse(**clean_project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    projects_collection().delete_one({"id": project_id})
    scans_collection().delete_many({"project_id": project_id})
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/scans")
async def create_scan_configuration(
    project_id: str,
    scan_config: ScanConfiguration,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    get_project_for_user(project_id, current_user["id"])

    if current_user.get("tier", "free") == "free":
        start_of_month = dt.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        scan_count = scans_collection().count_documents(
            {"user_id": current_user["id"], "created_at": {"$gte": start_of_month}}
        )
        if scan_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier limit reached: 10 scans per month. Upgrade plan to run more scans.",
            )

    now = dt.datetime.utcnow()
    scan = {
        "id": f"scan_{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "scan_name": scan_config.scan_name.strip(),
        "rulepack_version": scan_config.rulepack_version.strip(),
        "custom_checks": scan_config.custom_checks or [],
        "output_format": scan_config.output_format,
        "notify_on_completion": scan_config.notify_on_completion,
        "user_id": current_user["id"],
        "created_at": now,
        "updated_at": now,
        "status": "configured",
        "last_downloaded": None,
        "last_run": None,
        "last_completed": None,
        "results_summary": {},
        "findings_json": None,
        "results_count": 0,
    }
    scans_collection().insert_one(scan)

    return {
        "scan_id": scan["id"],
        "message": "Scan configuration created successfully",
        "download_url": f"/agent/download/{scan['id']}",
    }


@router.get("/{project_id}/scans")
async def list_project_scans(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    scans = list(scans_collection().find({"project_id": project_id}).sort("created_at", -1))
    return [_serialize_scan(scan) for scan in scans]
