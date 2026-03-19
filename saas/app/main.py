# [file name]: saas/app/main.py (Fixed with Cookie Support)
"""
Fixed SaaS Web Dashboard with Cookie Authentication
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `agent` and other top-level packages import correctly
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException, Request, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import Optional
import jwt

from auth import router as auth_router, get_current_user, SECRET_KEY, ALGORITHM, users_db
from projects import router as projects_router, projects_db, scans_db
from distribution import router as distribution_router
from plans import PLANS  # Preload so /api/plans returns instantly

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

    # Compute free-tier usage if applicable
    tier = user.get("tier", "free")
    free_scans_used = 0
    free_scans_limit = 0
    if tier == "free":
        import datetime as _dt
        now = _dt.datetime.utcnow()
        year_month = (now.year, now.month)
        scans_this_month = [
            s for s in user_scans
            if s.get("created_at")
            and (_dt.datetime.fromisoformat(s["created_at"]).year,
                 _dt.datetime.fromisoformat(s["created_at"]).month) == year_month
        ]
        free_scans_used = len(scans_this_month)
        free_scans_limit = 10

    return {
        "total_users": len(users_db),
        "total_projects": len(user_projects),
        "total_scans": len(user_scans),
        "active_scans": len([s for s in user_scans if s.get("status") in ["running", "downloaded"]]),
        "completed_scans": len([s for s in user_scans if s.get("status") == "completed"]),
        "user_tier": tier,
        "free_scans_used": free_scans_used,
        "free_scans_limit": free_scans_limit,
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


@app.get("/api/audit")
async def get_audit_logs(request: Request):
    """Get audit logs for current user"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return {"error": "Not authenticated"}

    try:
        from agent.db.mongo import list_audit_logs  # type: ignore
        logs = list_audit_logs(user_id=user["id"], limit=200)
    except Exception:
        # Fallback: derive audit-like entries from scans for the user
        user_scans = [s for s in scans_db.values() if s.get("user_id") == user["id"]]
        import datetime as _dt
        logs = []
        for s in sorted(user_scans, key=lambda x: x.get("last_completed") or x.get("created_at") or "", reverse=True)[:100]:
            ts = s.get("last_completed") or s.get("created_at") or _dt.datetime.utcnow().isoformat()
            logs.append({
                "audit_id": s.get("id"),
                "timestamp": ts,
                "user_id": s.get("user_id"),
                "project_id": s.get("project_id"),
                "scan_id": s.get("id"),
                "rulepack_version": s.get("rulepack_version"),
                "status": s.get("status", "unknown"),
                "source": "agent_results",
                "metadata": {
                    "results_count": s.get("results_count", 0),
                    "summary": s.get("results_summary", {}),
                },
            })
    return logs


@app.get("/api/plans")
async def get_plans(request: Request):
    """Get subscription plans (public endpoint) - PLANS preloaded at startup for fast response"""
    order = ["free", "standard", "premium", "premium_plus"]
    return [PLANS[k] for k in order if k in PLANS]


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About us page"""
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/scan/{scan_id}", response_class=HTMLResponse)
async def scan_output_page(scan_id: str, request: Request):
    """Scan output view - requires auth"""
    user = get_user_from_cookie(request.cookies.get("access_token"))
    if not user:
        try:
            user = await get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/")
    scan = scans_db.get(scan_id)
    if not scan or scan.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Scan not found")
    project = projects_db.get(scan.get("project_id", ""))
    return templates.TemplateResponse(
        "scan_output.html",
        {"request": request, "user": user, "scan": scan, "project": project or {}}
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page - requires auth, redirects to login if not authenticated"""
    user = get_user_from_cookie(request.cookies.get("access_token"))
    if not user:
        try:
            user = await get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/")
    return templates.TemplateResponse("reports.html", {"request": request, "user": user})


@app.get("/api/reports/{scan_id}/html")
async def get_scan_report_html(scan_id: str, request: Request):
    """Generate HTML report for a scan (for View)"""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    scan = scans_db.get(scan_id)
    if not scan or scan.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Scan not found")
    project = projects_db.get(scan.get("project_id", ""))
    proj_name = project.get("name", "Unknown") if project else "Unknown"
    summary = scan.get("results_summary", {}) or {}
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    total = scan.get("results_count", passed + failed) or (passed + failed) or 0
    ts = scan.get("last_completed") or scan.get("created_at") or ""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Compliance Report - {scan.get("scan_name", scan_id)}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:1rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px;text-align:left}} th{{background:#f5f5f5}}</style></head>
<body>
<h1>CompliSense-AI Compliance Report</h1>
<h2>{scan.get("scan_name", scan_id)}</h2>
<p><strong>Project:</strong> {proj_name} | <strong>Status:</strong> {scan.get("status", "-")} | <strong>Date:</strong> {ts}</p>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total checks</td><td>{total}</td></tr>
<tr><td>Passed</td><td>{passed}</td></tr>
<tr><td>Failed</td><td>{failed}</td></tr>
<tr><td>Rulepack</td><td>{scan.get("rulepack_version", "-")}</td></tr>
</table>
<p><em>Report generated by CompliSense-AI. For full details run the agent locally.</em></p>
</body></html>"""
    return HTMLResponse(content=html)


@app.get("/api/reports/{scan_id}/download")
async def download_scan_report(scan_id: str, request: Request, format: str = "html"):
    """Download report as HTML, PDF, or DOCX. HTML is generated; PDF/DOCX require agent run."""
    try:
        user = await get_current_user(request)
    except HTTPException:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    scan = scans_db.get(scan_id)
    if not scan or scan.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Scan not found")
    fmt = (format or "html").lower()
    project = projects_db.get(scan.get("project_id", ""))
    proj_name = project.get("name", "Unknown") if project else "Unknown"
    summary = scan.get("results_summary", {}) or {}
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    total = scan.get("results_count", passed + failed) or (passed + failed) or 0
    ts = scan.get("last_completed") or scan.get("created_at") or ""
    name = (scan.get("scan_name") or scan_id).replace(" ", "_")
    if fmt == "html":
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Compliance Report - {scan.get("scan_name", scan_id)}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:1rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}}</style></head>
<body><h1>CompliSense-AI Report</h1><h2>{scan.get("scan_name", scan_id)}</h2>
<p>Project: {proj_name} | Status: {scan.get("status", "-")} | {ts}</p>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total</td><td>{total}</td></tr><tr><td>Passed</td><td>{passed}</td></tr><tr><td>Failed</td><td>{failed}</td></tr>
</table></body></html>"""
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{name}_report.html"'}
        )
    if fmt in ("pdf", "docx"):
        return JSONResponse(
            {"detail": f"PDF and DOCX reports are generated by the local agent. Run the agent to produce {fmt.upper()} in the output directory."},
            status_code=501
        )
    raise HTTPException(status_code=400, detail="Format must be html, pdf, or docx")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
