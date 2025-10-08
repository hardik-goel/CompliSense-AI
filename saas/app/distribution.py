# [file name]: saas/app/distribution.py
"""
Agent distribution endpoints for CompliSense-AI
Handles agent download and management
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import datetime
from auth import get_current_user
from projects import projects_db, scans_db
from agent_generator import agent_generator

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/download/{scan_id}")
async def download_agent(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Download a customized agent for a specific scan"""
    scan = scans_db.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan configuration not found")

    if scan["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to download this agent")

    project = projects_db.get(scan["project_id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Generate customized agent
        zip_path = agent_generator.create_custom_agent(scan, current_user)

        # Update scan status
        scan["last_downloaded"] = datetime.datetime.utcnow().isoformat()
        scan["status"] = "downloaded"

        # Return the ZIP file
        return FileResponse(
            path=zip_path,
            filename=f"complisense_agent_{scan_id}.zip",
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename=complisense_agent_{scan_id}.zip"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate agent: {str(e)}")


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

    return {"status": "results_received"}