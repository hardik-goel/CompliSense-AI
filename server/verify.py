# server/verify.py
from fastapi import Depends, HTTPException, Header
import jwt
from pathlib import Path
from typing import Dict, Any

PUB_KEY_PATH = Path("/Users/hardikgoel/compli-keys/public.pem")
PUB_KEY = PUB_KEY_PATH.read_text()

def verify_bearer_token(authorization: str = Header(...)) -> Dict[str, Any]:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer")
    token = authorization.split(" ",1)[1]
    try:
        payload = jwt.decode(token, PUB_KEY, algorithms=["RS256"], issuer="https://saas.example.com")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    # You may check scopes here
    return payload
