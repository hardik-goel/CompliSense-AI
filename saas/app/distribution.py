# [file name]: saas/app/distribution.py
"""
Agent distribution endpoints for CompliSense-AI
Handles agent download and management
"""

import asyncio
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Optional
import datetime
from auth import get_current_user
from projects import projects_db, scans_db
from agent_generator import agent_generator
from agent.db.mongo import insert_audit_log  # type: ignore

router = APIRouter(prefix="/agent", tags=["agent"])

# Short-lived tokens for download (scan_id -> (user_id, expiry_ts))
_download_tokens: Dict[str, tuple] = {}
_TOKEN_TTL_SEC = 120


def _get_scan_and_check(scan_id: str, current_user: dict):
    scan = scans_db.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan configuration not found")
    if scan["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to download this agent")
    project = projects_db.get(scan["project_id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return scan, project


@router.post("/download/{scan_id}/prepare")
async def prepare_agent_download(scan_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Prepare agent zip and return a one-time download URL.
    Client should set window.location.href = download_url so the browser
    performs a normal GET and shows native download progress (avoids fetch/blob "stuck").
    """
    _get_scan_and_check(scan_id, current_user)
    try:
        zip_path = await asyncio.to_thread(
            agent_generator.create_custom_agent,
            scans_db[scan_id],
            current_user,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    scan = scans_db[scan_id]
    scan["last_downloaded"] = datetime.datetime.utcnow().isoformat()
    scan["status"] = "downloaded"
    token = secrets.token_urlsafe(32)
    _download_tokens[token] = (current_user["id"], time.time() + _TOKEN_TTL_SEC)
    base = str(request.base_url).rstrip("/")
    download_url = f"{base}/agent/download/{scan_id}?token={token}"
    return JSONResponse({"download_url": download_url})


@router.get("/download/{scan_id}")
async def download_agent(
    scan_id: str,
    request: Request,
    token: Optional[str] = None,
):
    """
    Stream the agent zip. Accepts ?token= from prepare (no auth header needed).
    Using token + direct navigation lets the browser show download progress.
    """
    if token:
        if token not in _download_tokens:
            raise HTTPException(status_code=403, detail="Invalid or expired download link")
        user_id, expiry = _download_tokens[token]
        if time.time() > expiry:
            del _download_tokens[token]
            raise HTTPException(status_code=403, detail="Download link expired")
        scan = scans_db.get(scan_id)
        if not scan or scan.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        del _download_tokens[token]
    else:
        try:
            current_user = await get_current_user(request)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Use the Download button to get a download link")
        _get_scan_and_check(scan_id, current_user)

    zip_path = agent_generator.temp_dir / f"complisense_agent_{scan_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Agent not found; run Prepare first")

    def iter_file():
        with open(zip_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=complisense_agent_{scan_id}.zip"
        },
    )


@router.post("/heartbeat")
async def receive_agent_heartbeat(heartbeat_data: Dict[str, Any]):
    """Receive heartbeat from running agents"""
    scan_id = heartbeat_data.get("scan_id")
    status = heartbeat_data.get("status")

    if scan_id in scans_db:
        scan = scans_db[scan_id]
        scan["status"] = status

        if status == "running" and not scan.get("last_run"):
            scan["last_run"] = datetime.datetime.utcnow().isoformat()

    return {"status": "acknowledged"}


@router.post("/results")
async def receive_scan_results(results_data: Dict[str, Any]):
    """Receive scan results from agents"""
    scan_id = results_data.get("scan_id")

    if scan_id in scans_db:
        scan = scans_db[scan_id]
        scan["status"] = "completed"
        scan["last_completed"] = datetime.datetime.utcnow().isoformat()
        scan["results_summary"] = results_data.get("summary", {})
        scan["results_count"] = results_data.get("results_count", 0)

        # Write minimal audit log entry (metadata only)
        try:
            insert_audit_log(
                {
                    "scan_id": scan_id,
                    "user_id": scan.get("user_id"),
                    "project_id": scan.get("project_id"),
                    "rulepack_version": scan.get("rulepack_version"),
                    "status": "completed",
                    "source": "agent_results",
                    "timestamp": datetime.datetime.utcnow(),
                    "metadata": {
                        "results_count": scan.get("results_count", 0),
                        "summary": scan.get("results_summary", {}),
                    },
                }
            )
        except Exception:
            # Audit logging is best-effort; never break main flow
            pass

    return {"status": "results_received"}