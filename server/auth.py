# server/auth.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta
from pathlib import Path

app = FastAPI()

# Load private key (SaaS side, protect this file)
PRIVATE_KEY_PATH = Path("/Users/hardikgoel/compli-keys/private.pem")  # set via env in prod
PRIVATE_KEY = PRIVATE_KEY_PATH.read_text()

# Simple in-memory "installation codes" (dev only)
VALID_INSTALL_CODES = {"one-time-install-123": "client-001"}

class IssueRequest(BaseModel):
    install_code: str
    # optional: client_id, scopes

@app.post("/auth/issue")
def issue_token(req: IssueRequest):
    client = VALID_INSTALL_CODES.get(req.install_code)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid install code")
    now = datetime.utcnow()
    payload = {
        "sub": client,
        "iat": now,
        "exp": now + timedelta(minutes=60),   # short-lived dev token
        "scope": "upload:summary download:rulepack",
        "iss": "https://saas.example.com"
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}
