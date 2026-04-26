from __future__ import annotations

import datetime as dt
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent.db.mongo import list_audit_logs
from saas.app.auth import get_current_user, get_current_user_optional, router as auth_router
from saas.app.config import settings
from saas.app.database import ensure_indexes, ping_database, serialize_document
from saas.app.distribution import router as distribution_router
from saas.app.plans import PLANS
from saas.app.projects import (
    projects_collection,
    router as projects_router,
    scans_collection,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

saas_dir = Path(__file__).parent.parent
templates_dir = saas_dir / "templates"
static_dir = saas_dir / "static"
templates_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    description="Central dashboard for EU AI Act compliance management",
    version=settings.app_version,
)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(distribution_router)


@app.on_event("startup")
async def startup_event():
    try:
        ping_database()
        ensure_indexes()
    except Exception:
        logger.exception("MongoDB startup initialization failed")
        if settings.is_production:
            raise
    logger.info("Application startup complete")


@app.middleware("http")
async def attach_user_context(request: Request, call_next):
    request.state.current_user = await get_current_user_optional(request, None, request.cookies.get("access_token"))
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Unhandled application error for path=%s", request.url.path)
        raise


def _get_user_from_request(request: Request):
    return getattr(request.state, "current_user", None)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = _get_user_from_request(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    user = _get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("user_dashboard.html", {"request": request, "user": user})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    user = _get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("reports.html", {"request": request, "user": user})


@app.get("/scan/{scan_id}", response_class=HTMLResponse)
async def scan_output_page(scan_id: str, request: Request):
    user = _get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/")
    scan = scans_collection().find_one({"id": scan_id, "user_id": user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    project = projects_collection().find_one({"id": scan.get("project_id")})
    return templates.TemplateResponse(
        "scan_output.html",
        {"request": request, "user": user, "scan": serialize_document(scan), "project": serialize_document(project or {})},
    )


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}


@app.get("/render_health")
async def render_health():
    return await health_check()


@app.get("/api/stats")
async def get_dashboard_stats(request: Request):
    user = await get_current_user(request)
    project_count = projects_collection().count_documents({"user_id": user["id"]})
    user_scans = list(scans_collection().find({"user_id": user["id"]}))

    free_scans_used = 0
    free_scans_limit = 0
    if user.get("tier", "free") == "free":
        now = dt.datetime.utcnow()
        free_scans_used = len(
            [
                scan
                for scan in user_scans
                if scan.get("created_at")
                and scan["created_at"].year == now.year
                and scan["created_at"].month == now.month
            ]
        )
        free_scans_limit = 10

    return {
        "total_projects": project_count,
        "total_scans": len(user_scans),
        "active_scans": len([scan for scan in user_scans if scan.get("status") in {"running", "downloaded"}]),
        "completed_scans": len([scan for scan in user_scans if scan.get("status") == "completed"]),
        "user_tier": user.get("tier", "free"),
        "free_scans_used": free_scans_used,
        "free_scans_limit": free_scans_limit,
    }


@app.get("/api/scans")
async def get_user_scans(request: Request):
    user = await get_current_user(request)
    scans = list(scans_collection().find({"user_id": user["id"]}).sort("created_at", -1))
    return [serialize_document(scan) for scan in scans]


@app.get("/api/audit")
async def get_audit_logs(request: Request):
    user = await get_current_user(request)
    try:
        return list_audit_logs(user_id=user["id"], limit=200)
    except Exception:
        logger.exception("Falling back from audit log fetch to derived scan history for user_id=%s", user["id"])
        scans = list(scans_collection().find({"user_id": user["id"]}).sort("created_at", -1).limit(100))
        derived = []
        for scan in scans:
            clean_scan = serialize_document(scan)
            derived.append(
                {
                    "audit_id": clean_scan["id"],
                    "timestamp": clean_scan.get("last_completed") or clean_scan.get("created_at"),
                    "user_id": clean_scan.get("user_id"),
                    "project_id": clean_scan.get("project_id"),
                    "scan_id": clean_scan.get("id"),
                    "rulepack_version": clean_scan.get("rulepack_version"),
                    "status": clean_scan.get("status", "unknown"),
                    "source": "scan_fallback",
                    "metadata": {
                        "results_count": clean_scan.get("results_count", 0),
                        "summary": clean_scan.get("results_summary", {}),
                    },
                }
            )
        return derived


@app.get("/api/plans")
async def get_plans():
    order = ["free", "standard", "premium", "premium_plus"]
    return [PLANS[key] for key in order if key in PLANS]


@app.get("/api/reports/{scan_id}/html")
async def get_scan_report_html(scan_id: str, request: Request):
    user = await get_current_user(request)
    scan = scans_collection().find_one({"id": scan_id, "user_id": user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    project = projects_collection().find_one({"id": scan.get("project_id")})
    project_name = project.get("name", "Unknown") if project else "Unknown"
    summary = scan.get("results_summary", {}) or {}
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    total = scan.get("results_count", passed + failed) or (passed + failed)
    timestamp = scan.get("last_completed") or scan.get("created_at")
    timestamp_display = timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Compliance Report - {scan.get("scan_name", scan_id)}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:1rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px;text-align:left}} th{{background:#f5f5f5}}</style></head>
<body>
<h1>CompliSense-AI Compliance Report</h1>
<h2>{scan.get("scan_name", scan_id)}</h2>
<p><strong>Project:</strong> {project_name} | <strong>Status:</strong> {scan.get("status", "-")} | <strong>Date:</strong> {timestamp_display}</p>
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
    user = await get_current_user(request)
    scan = scans_collection().find_one({"id": scan_id, "user_id": user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    fmt = format.lower()
    project = projects_collection().find_one({"id": scan.get("project_id")})
    project_name = project.get("name", "Unknown") if project else "Unknown"
    summary = scan.get("results_summary", {}) or {}
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    total = scan.get("results_count", passed + failed) or (passed + failed)
    timestamp = scan.get("last_completed") or scan.get("created_at")
    timestamp_display = timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp
    filename = (scan.get("scan_name") or scan_id).replace(" ", "_")

    if fmt == "html":
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Compliance Report - {scan.get("scan_name", scan_id)}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:1rem}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}}</style></head>
<body><h1>CompliSense-AI Report</h1><h2>{scan.get("scan_name", scan_id)}</h2>
<p>Project: {project_name} | Status: {scan.get("status", "-")} | {timestamp_display}</p>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total</td><td>{total}</td></tr><tr><td>Passed</td><td>{passed}</td></tr><tr><td>Failed</td><td>{failed}</td></tr>
</table></body></html>"""
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}_report.html"'},
        )

    if fmt in {"pdf", "docx"}:
        return JSONResponse(
            {
                "detail": (
                    f"PDF and DOCX reports are generated by the local agent. "
                    f"Run the agent to produce {fmt.upper()} in the output directory."
                )
            },
            status_code=501,
        )

    raise HTTPException(status_code=400, detail="Format must be html, pdf, or docx")
