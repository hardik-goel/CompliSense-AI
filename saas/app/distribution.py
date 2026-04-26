from __future__ import annotations

import asyncio
import datetime as dt
import logging
import secrets
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from saas.app.auth import get_current_user, get_current_user_optional
from saas.app.config import settings
from saas.app.database import get_collection, serialize_document
from saas.app.projects import get_project_for_user

try:
    from saas.app.agent_generator import agent_generator
except Exception:
    agent_generator = None

router = APIRouter(tags=["agent"])
logger = logging.getLogger(__name__)

_download_tokens: dict[str, tuple[str, float]] = {}
_TOKEN_TTL_SEC = 120


class UploadScanRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=120)
    scan_summary: dict[str, Any]
    findings_json: dict[str, Any]
    timestamp: dt.datetime
    scan_id: str | None = None
    scan_name: str | None = Field(default=None, max_length=120)
    rulepack_version: str = Field(default="euai_core_v1", max_length=120)


def projects_collection():
    return get_collection("projects")


def scans_collection():
    return get_collection("scans")


def _get_scan(scan_id: str) -> dict[str, Any]:
    scan = scans_collection().find_one({"id": scan_id})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan configuration not found")
    return scan


def _get_project(project_id: str) -> dict[str, Any] | None:
    return projects_collection().find_one({"id": project_id})


def _count_findings(findings_json: dict[str, Any]) -> int:
    results = findings_json.get("results")
    if isinstance(results, list):
        return len(results)
    findings = findings_json.get("findings")
    if isinstance(findings, list):
        return len(findings)
    return 0


async def _get_upload_actor(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_admin_api_token: str | None = Header(default=None, alias="X-Admin-Api-Token"),
):
    provided_token = x_api_key or x_admin_api_token
    if provided_token and secrets.compare_digest(provided_token, settings.admin_api_token):
        return {"auth_type": "admin_api_token"}

    user = await get_current_user_optional(request, None, request.cookies.get("access_token"))
    if user:
        return {"auth_type": "jwt", "user": user}

    logger.warning("Rejected scan upload due to missing or invalid credentials")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


def _get_scan_and_check(scan_id: str, current_user: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    scan = _get_scan(scan_id)
    if scan["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to download this agent")
    project = get_project_for_user(scan["project_id"], current_user["id"])
    return scan, project


@router.post("/agent/download/{scan_id}/prepare")
async def prepare_agent_download(scan_id: str, request: Request, current_user: dict[str, Any] = Depends(get_current_user)):
    _get_scan_and_check(scan_id, current_user)
    if agent_generator is None:
        raise HTTPException(status_code=500, detail="Agent generator is unavailable")

    try:
        scan_doc = serialize_document(_get_scan(scan_id))
        zip_path = await asyncio.to_thread(
            agent_generator.create_custom_agent,
            scan_doc,
            current_user,
            str(request.base_url).rstrip("/"),
        )
    except Exception as exc:
        logger.exception("Failed to prepare agent download for scan_id=%s", scan_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    scans_collection().update_one(
        {"id": scan_id},
        {"$set": {"last_downloaded": dt.datetime.utcnow(), "updated_at": dt.datetime.utcnow(), "status": "downloaded"}},
    )
    token = secrets.token_urlsafe(32)
    _download_tokens[token] = (current_user["id"], time.time() + _TOKEN_TTL_SEC)
    base = str(request.base_url).rstrip("/")
    download_url = f"{base}/agent/download/{scan_id}?token={token}"

    return JSONResponse({"download_url": download_url, "zip_path": str(zip_path)})


@router.get("/agent/download/{scan_id}")
async def download_agent(scan_id: str, request: Request, token: str | None = None):
    if token:
        if token not in _download_tokens:
            raise HTTPException(status_code=403, detail="Invalid or expired download link")
        user_id, expiry = _download_tokens[token]
        if time.time() > expiry:
            del _download_tokens[token]
            raise HTTPException(status_code=403, detail="Download link expired")
        scan = _get_scan(scan_id)
        if scan.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        del _download_tokens[token]
    else:
        current_user = await get_current_user(request)
        _get_scan_and_check(scan_id, current_user)

    if agent_generator is None:
        raise HTTPException(status_code=500, detail="Agent generator is unavailable")

    zip_path = agent_generator.temp_dir / f"complisense_agent_{scan_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Agent not found; run Prepare first")

    def iter_file():
        with open(zip_path, "rb") as file_handle:
            while chunk := file_handle.read(65536):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=complisense_agent_{scan_id}.zip"},
    )


@router.post("/agent/heartbeat")
async def receive_agent_heartbeat(heartbeat_data: dict[str, Any]):
    scan_id = heartbeat_data.get("scan_id")
    status_value = heartbeat_data.get("status")
    if not scan_id:
        raise HTTPException(status_code=400, detail="scan_id is required")

    scan = scans_collection().find_one({"id": scan_id})
    if scan:
        update_fields: dict[str, Any] = {"status": status_value, "updated_at": dt.datetime.utcnow()}
        if status_value == "running" and not scan.get("last_run"):
            update_fields["last_run"] = dt.datetime.utcnow()
        scans_collection().update_one({"id": scan_id}, {"$set": update_fields})

    return {"status": "acknowledged"}


@router.post("/agent/results")
async def receive_scan_results(results_data: dict[str, Any]):
    scan_id = results_data.get("scan_id")
    if not scan_id:
        raise HTTPException(status_code=400, detail="scan_id is required")

    scan = scans_collection().find_one({"id": scan_id})
    if scan:
        summary = results_data.get("summary", {}) or {}
        findings_json = results_data if isinstance(results_data, dict) else {}
        update_fields = {
            "status": "completed",
            "updated_at": dt.datetime.utcnow(),
            "last_completed": dt.datetime.utcnow(),
            "results_summary": summary,
            "findings_json": findings_json,
            "results_count": results_data.get("results_count", _count_findings(findings_json)),
        }
        scans_collection().update_one({"id": scan_id}, {"$set": update_fields})

        try:
            insert_audit_log(
                {
                    "scan_id": scan_id,
                    "user_id": scan.get("user_id"),
                    "project_id": scan.get("project_id"),
                    "rulepack_version": scan.get("rulepack_version"),
                    "status": "completed",
                    "source": "agent_results",
                    "timestamp": dt.datetime.utcnow(),
                    "metadata": {
                        "results_count": update_fields["results_count"],
                        "summary": summary,
                    },
                }
            )
        except Exception:
            logger.exception("Audit log write failed for scan_id=%s", scan_id)

    return {"status": "results_received"}


@router.post("/api/v1/upload-scan")
async def upload_scan(payload: UploadScanRequest, actor: dict[str, Any] = Depends(_get_upload_actor)):
    project = _get_project(payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if actor["auth_type"] == "jwt":
        user = actor["user"]
        get_project_for_user(payload.project_id, user["id"])
        user_id = user["id"]
    else:
        user_id = project["user_id"]

    now = dt.datetime.utcnow()
    scan_id = payload.scan_id or f"scan_{uuid.uuid4().hex[:8]}"
    existing_scan = scans_collection().find_one({"id": scan_id})

    findings_count = _count_findings(payload.findings_json)
    scan_doc = {
        "id": scan_id,
        "project_id": payload.project_id,
        "scan_name": payload.scan_name or f"Upload {payload.timestamp.isoformat()}",
        "rulepack_version": payload.rulepack_version,
        "custom_checks": [],
        "output_format": ["json"],
        "notify_on_completion": False,
        "user_id": user_id,
        "created_at": existing_scan.get("created_at", now) if existing_scan else now,
        "updated_at": now,
        "status": "completed",
        "last_run": payload.timestamp,
        "last_completed": payload.timestamp,
        "results_summary": payload.scan_summary,
        "findings_json": payload.findings_json,
        "results_count": findings_count,
    }

    scans_collection().update_one({"id": scan_id}, {"$set": scan_doc}, upsert=True)
    logger.info("Stored uploaded scan scan_id=%s project_id=%s auth_type=%s", scan_id, payload.project_id, actor["auth_type"])

    try:
        insert_audit_log(
            {
                "user_id": user_id,
                "project_id": payload.project_id,
                "scan_id": scan_id,
                "rulepack_version": payload.rulepack_version,
                "status": "completed",
                "source": "api_v1_upload_scan",
                "timestamp": payload.timestamp,
                "metadata": {"results_count": findings_count, "summary": payload.scan_summary},
            }
        )
    except Exception:
        logger.exception("Audit log write failed for uploaded scan scan_id=%s", scan_id)

    return {"success": True, "scan_id": scan_id, "project_id": payload.project_id, "stored_at": now.isoformat()}
