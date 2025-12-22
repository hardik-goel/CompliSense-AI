# saas/app/main.py
"""
CompliSense-AI SaaS Dashboard (Scan-aware, Event-driven)
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from threading import Thread
from pathlib import Path
from typing import Optional
import jwt

from auth import router as auth_router, get_current_user, SECRET_KEY, ALGORITHM
from projects import router as projects_router, projects_db, scans_db
from distribution import router as distribution_router
from saas.app.scan_manager import scan_manager

# -------------------------
# App setup
# -------------------------

saas_dir = Path(__file__).parent.parent
templates_dir = saas_dir / "templates"
static_dir = saas_dir / "static"

templates = Jinja2Templates(directory=templates_dir)

app = FastAPI(
    title="CompliSense-AI SaaS Dashboard",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(distribution_router)

from auth import users_db


# -------------------------
# Auth helper
# -------------------------

def get_user_from_cookie(access_token: Optional[str] = Cookie(None)):
    if not access_token:
        return None
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = payload.get("sub")
        return next((u for u in users_db.values() if u["id"] == uid), None)
    except Exception:
        return None


# -------------------------
# UI Routes
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_user_from_cookie(request.cookies.get("access_token"))
    if user:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    user = get_user_from_cookie(request.cookies.get("access_token"))
    if not user:
        try:
            user = await get_current_user(request)
        except HTTPException:
            return RedirectResponse("/")
    return templates.TemplateResponse(
        "user_dashboard.html",
        {"request": request, "user": user}
    )


# -------------------------
# Scan APIs (NEW)
# -------------------------

class StartScanRequest(BaseModel):
    project_id: str


@app.post("/api/scan/start")
async def start_scan(payload: StartScanRequest, request: Request):
    user = await get_current_user(request)

    scan_id = scan_manager.create_scan(
        project_id=payload.project_id,
        user_id=user["id"]
    )

    thread = Thread(
        target=scan_manager.run_scan,
        args=(scan_id,),
        daemon=True
    )
    thread.start()

    return JSONResponse({"scan_id": scan_id})


@app.get("/api/scan/{scan_id}/status")
async def scan_status(scan_id: str, request: Request):
    await get_current_user(request)
    state = scan_manager.get_state(scan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Scan not found")
    return state


@app.post("/api/scan/{scan_id}/cancel")
async def cancel_scan(scan_id: str, request: Request):
    await get_current_user(request)
    scan_manager.cancel(scan_id)
    return {"status": "cancelled"}


# -------------------------
# Health
# -------------------------

@app.get("/api/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
