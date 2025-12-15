# server/saas_api.py
from fastapi import FastAPI, Header, HTTPException, Request
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from agent.rules.loader import load_rulepack
from agent.db.mongo import insert_report, get_mongo_client
from typing import Dict, Any
import os, json, pathlib, jwt, logging
from pydantic import BaseModel
from datetime import datetime, timedelta
from server.downloads import router as downloads_router


app = FastAPI(title="CompliSense SaaS API (dev-friendly)")

logger = logging.getLogger("saas_api")
logging.basicConfig(level=logging.INFO)

# Simple install codes map (dev/demo only)
INSTALL_CODES = {"one-time-install-123": "client-001"}


# Helper: read allowed static token(s) from env at runtime
def get_allowed_static_tokens():
    """
    Returns a set of allowed static tokens read from env var ADMIN_API_TOKEN.
    Can be a single token or comma-separated list.
    """
    raw = os.getenv("ADMIN_API_TOKEN", None)
    if not raw:
        return set()
    # allow comma separated tokens
    toks = {t.strip() for t in raw.split(",") if t.strip()}
    return toks

# Simple /auth/issue endpoint for dev: issues HS256 tokens based on a one-time install code
class IssueReq(BaseModel):
    install_code: str

DEV_AUTH_SECRET = os.getenv("DEV_AUTH_SECRET", None)  # optional; if set we'll issue HS256 tokens

@app.get("/")
def root():
    return {"status": "CompliSense SaaS API running", "version": "0.1.0"}

@app.get("/", response_class=HTMLResponse)
def ui():
    return pathlib.Path("server/static/app.html").read_text()

@app.post("/auth/issue")
def issue(req: IssueReq):
    """
    Dev-only token issuer: return a short-lived HS256 JWT when a valid install code is supplied.
    """
    client = INSTALL_CODES.get(req.install_code)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid install code")
    now = datetime.utcnow()
    payload = {
        "sub": client,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=60)).timestamp()),
        "scope": "upload:summary",
        "iss": "http://127.0.0.1:8080"
    }
    # If DEV_AUTH_SECRET not set, fallback to returning a dummy token (not recommended)
    if not DEV_AUTH_SECRET:
        # return a simple token-like string to help devs (not signed)
        return {"access_token": f"dev-plain-{client}-{int(now.timestamp())}", "token_type": "bearer", "expires_in": 3600}
    token = jwt.encode(payload, DEV_AUTH_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}

@app.get("/rulepacks/latest")
def rulepack_latest():
    rp = load_rulepack(pathlib.Path(__file__).parent.parent / "rulepacks" / "euai_core_v1.yaml")
    return rp

# Main results endpoint: accepts either a static token (ADMIN_API_TOKEN) or a HS256 JWT signed by DEV_AUTH_SECRET
@app.post("/results")
async def results_endpoint(request: Request, authorization: str = Header(...)):
    """
    Accepts run summary from agent. Authorization: Bearer <token>
    This endpoint supports:
      - Static tokens set in ADMIN_API_TOKEN (comma-separated)
      - HS256 JWTs signed with DEV_AUTH_SECRET (dev flow)
    """
    # Basic header sanity
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]

    # 1) Check static tokens (reads env at runtime)
    allowed = get_allowed_static_tokens()
    if allowed:
        logger.info("Allowed static tokens present: %s", list(allowed))
    if token in allowed:
        # token accepted via static token list
        payload = {"auth_method": "static", "sub": None}
        logger.info("Accepted via static token")
    else:
        # 2) Try validating as HS256 JWT if DEV_AUTH_SECRET is set
        dev_secret = os.getenv("DEV_AUTH_SECRET", None)
        payload = None
        if dev_secret:
            try:
                payload = jwt.decode(token, dev_secret, algorithms=["HS256"], options={"require": ["exp", "iat", "iss"]})
                logger.info("Accepted via DEV_AUTH_SECRET JWT; sub=%s", payload.get("sub"))
            except jwt.ExpiredSignatureError:
                logger.warning("Token expired")
                raise HTTPException(status_code=401, detail="Token expired")
            except Exception as e:
                logger.warning("JWT verification failed: %s", e)
                # fall through to error
        # if no payload and no static match, reject
        if payload is None:
            logger.warning("Invalid token presented")
            raise HTTPException(status_code=403, detail="Invalid token")

    # Read request payload
    body = await request.json()
    if "summary" not in body:
        raise HTTPException(status_code=400, detail="Missing summary field")

    # Build metadata - include client identity if present in token payload
    client_id = payload.get("sub") if isinstance(payload, dict) else None
    metadata = {
        "pack_id": body.get("pack_id"),
        "pack_version": body.get("pack_version"),
        "project_root": body.get("project_root"),
        "client": client_id
    }

    run_id = insert_report(body, metadata=metadata)
    return {"status": "ok", "run_id": run_id}

app.include_router(downloads_router)
app.mount("/", StaticFiles(directory="server/static", html=True), name="static")