# [file name]: saas/app/main.py (Updated)
"""
SaaS Web Dashboard - Main FastAPI application
Now with authentication integrated
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import Optional

from auth import router as auth_router, get_current_user

# Create saas directory structure
saas_dir = Path(__file__).parent.parent
templates_dir = saas_dir / "templates"
static_dir = saas_dir / "static"

templates_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="CompliSense-AI SaaS Dashboard",
    description="Central dashboard for EU AI Act compliance management",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

# In-memory storage (replace with database in production)
users_db = {}
projects_db = {}
scans_db = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CompliSense-AI SaaS"}


@app.get("/api/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics (protected)"""
    user_projects = [p for p in projects_db.values() if p.get("user_id") == current_user["id"]]
    user_scans = [s for s in scans_db.values() if s.get("user_id") == current_user["id"]]

    return {
        "total_users": len(users_db),
        "total_projects": len(user_projects),
        "total_scans": len(user_scans),
        "active_scans": len([s for s in user_scans if s.get("status") == "running"]),
        "user_tier": current_user.get("tier", "free")
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    """User-specific dashboard"""
    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "user": current_user
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)