# [file name]: saas/app/projects.py
"""
Project management system for CompliSense-AI
Handles project creation, configuration, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
import uuid
from auth import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

# In-memory storage (replace with database in production)
projects_db = {}
scans_db = {}


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str  # e.g., "LLM", "Computer Vision", "Speech Recognition"
    compliance_standard: str = "EU_AI_ACT"  # Default to EU AI Act
    industry: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    industry: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    model_type: str
    compliance_standard: str
    industry: Optional[str]
    user_id: str
    created_at: str
    updated_at: str
    scan_count: int = 0


class ScanConfiguration(BaseModel):
    project_id: str
    scan_name: str
    rulepack_version: str = "euai_core_v1"
    custom_checks: Optional[List[str]] = None
    output_format: List[str] = ["pdf", "json"]  # pdf, json, html
    notify_on_completion: bool = True


@router.post("/", response_model=ProjectResponse)
async def create_project(
        project_data: ProjectCreate,
        current_user: dict = Depends(get_current_user)
):
    """Create a new compliance project"""
    project_id = f"proj_{uuid.uuid4().hex[:8]}"

    project = {
        "id": project_id,
        "name": project_data.name,
        "description": project_data.description,
        "model_type": project_data.model_type,
        "compliance_standard": project_data.compliance_standard,
        "industry": project_data.industry,
        "user_id": current_user["id"],
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "scan_count": 0
    }

    projects_db[project_id] = project

    return ProjectResponse(**project)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    """List all projects for the current user"""
    user_projects = [p for p in projects_db.values() if p["user_id"] == current_user["id"]]

    # Add scan counts
    for project in user_projects:
        project_scans = [s for s in scans_db.values() if s.get("project_id") == project["id"]]
        project["scan_count"] = len(project_scans)

    return user_projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific project"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")

    # Add scan count
    project_scans = [s for s in scans_db.values() if s.get("project_id") == project_id]
    project["scan_count"] = len(project_scans)

    return ProjectResponse(**project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: str,
        project_data: ProjectUpdate,
        current_user: dict = Depends(get_current_user)
):
    """Update a project"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")

    # Update provided fields
    update_data = project_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        project[key] = value

    project["updated_at"] = datetime.datetime.utcnow().isoformat()

    return ProjectResponse(**project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project and its associated scans"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")

    # Delete project
    del projects_db[project_id]

    # Delete associated scans
    scan_ids_to_delete = [
        scan_id for scan_id, scan in scans_db.items()
        if scan.get("project_id") == project_id
    ]
    for scan_id in scan_ids_to_delete:
        del scans_db[scan_id]

    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/scans")
async def create_scan_configuration(
        project_id: str,
        scan_config: ScanConfiguration,
        current_user: dict = Depends(get_current_user)
):
    """Create a scan configuration for a project"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to configure scans for this project")

    # Enforce free-tier limits: 10 scans/month across all projects
    if current_user.get("tier", "free") == "free":
        now = datetime.datetime.utcnow()
        year_month = (now.year, now.month)
        user_scans_this_month = [
            s for s in scans_db.values()
            if s.get("user_id") == current_user["id"]
            and s.get("created_at")
            and (datetime.datetime.fromisoformat(s["created_at"]).year,
                 datetime.datetime.fromisoformat(s["created_at"]).month) == year_month
        ]
        if len(user_scans_this_month) >= 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier limit reached: 10 scans per month. Upgrade plan to run more scans."
            )

    scan_id = f"scan_{uuid.uuid4().hex[:8]}"

    scan = {
        "id": scan_id,
        "project_id": project_id,
        "scan_name": scan_config.scan_name,
        "rulepack_version": scan_config.rulepack_version,
        "custom_checks": scan_config.custom_checks or [],
        "output_format": scan_config.output_format,
        "notify_on_completion": scan_config.notify_on_completion,
        "user_id": current_user["id"],
        "created_at": datetime.datetime.utcnow().isoformat(),
        "status": "configured",  # configured, downloaded, running, completed, failed
        "last_downloaded": None,
        "last_run": None
    }

    scans_db[scan_id] = scan

    return {
        "scan_id": scan_id,
        "message": "Scan configuration created successfully",
        "download_url": f"/agent/download/{scan_id}"
    }


@router.get("/{project_id}/scans")
async def list_project_scans(project_id: str, current_user: dict = Depends(get_current_user)):
    """List all scans for a project"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project's scans")

    project_scans = [s for s in scans_db.values() if s.get("project_id") == project_id]
    return project_scans