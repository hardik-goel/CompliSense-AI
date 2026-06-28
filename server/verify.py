# server/verify.py
import os
from pathlib import Path
from typing import Any, Dict

import jwt
from fastapi import Header, HTTPException

# Environment-driven public-key path; read lazily inside the verifier (no hardcoded path,
# no read at import time).
PUB_KEY_PATH = Path(os.getenv("COMPLISENSE_PUBLIC_KEY_PATH", "compli-keys/public.pem"))


def verify_bearer_token(authorization: str = Header(...)) -> Dict[str, Any]:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer")
    if not PUB_KEY_PATH.exists():
        raise HTTPException(status_code=503, detail="Public key not configured (set COMPLISENSE_PUBLIC_KEY_PATH)")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, PUB_KEY_PATH.read_text(), algorithms=["RS256"], issuer="https://saas.example.com")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    # You may check scopes here
    return payload
