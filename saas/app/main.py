# [file name]: saas/app/main.py (Fixed with Cookie Support)
"""
Fixed SaaS Web Dashboard with Cookie Authentication
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import Optional
import jwt

from auth import router as auth_router, get_current_user, SECRET_KEY, ALGORITHM
from projects import router as projects_router, projects_db, scans_db
from distribution import router as distribution_router

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
app.include_router(projects_router)
app.include_router(distribution_router)

# Import shared databases
from auth import users_db


def get_user_from_cookie(access_token: Optional[str] = Cookie(None)):
    """Get user from cookie token"""
    if not access_token:
        return None

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return next((u for u in users_db.values() if u["id"] == user_id), None)
    except:
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    user = get_user_from_cookie(request.cookies.get("access_token"))
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    """User-specific dashboard - fixed to handle both cookie and header auth"""
    # Try to get user from cookie first
    user = get_user_from_cookie(request.cookies.get("access_token"))

    if not user:
        # If no cookie, check if this is an API call with header
        try:
            # This will raise HTTPException if no valid token
            user = await get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "user": user
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CompliSense-AI SaaS"}


@app.get("/api/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics - fixed authentication"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return {"error": "Not authenticated"}

    user_projects = [p for p in projects_db.values() if p.get("user_id") == user["id"]]
    user_scans = [s for s in scans_db.values() if s.get("user_id") == user["id"]]

    return {
        "total_users": len(users_db),
        "total_projects": len(user_projects),
        "total_scans": len(user_scans),
        "active_scans": len([s for s in user_scans if s.get("status") in ["running", "downloaded"]]),
        "completed_scans": len([s for s in user_scans if s.get("status") == "completed"]),
        "user_tier": user.get("tier", "free")
    }


# Add missing API endpoints with fixed auth
@app.get("/api/scans")
async def get_user_scans(request: Request):
    """Get all scans for current user - fixed auth"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return {"error": "Not authenticated"}

    user_scans = [s for s in scans_db.values() if s.get("user_id") == user["id"]]
    return user_scans


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
