from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
AGENT_ZIP = BASE_DIR / "dist" / "CompliSenseAgent-macos.zip"


@router.get("/download/agent", tags=["Downloads"])
def download_agent():
    if not AGENT_ZIP.exists() or not AGENT_ZIP.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Agent binary not found at {AGENT_ZIP}"
        )

    return FileResponse(
        path=AGENT_ZIP,
        filename="CompliSenseAgent-macos.zip",
        media_type="application/zip"
    )
