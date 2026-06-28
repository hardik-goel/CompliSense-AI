# server/jwks.py
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI()

# Public-key path is environment-driven (no hardcoded local path); read lazily so the
# module imports cleanly even where the key is absent.
PUB_KEY_PATH = Path(os.getenv("COMPLISENSE_PUBLIC_KEY_PATH", "compli-keys/public.pem"))


@app.get("/.well-known/jwks.json")
def jwks():
    if not PUB_KEY_PATH.exists():
        raise HTTPException(status_code=503, detail="Public key not configured (set COMPLISENSE_PUBLIC_KEY_PATH)")
    # Serve PEM as-is (agent can load PEM). For full JWKS, convert to modulus/exponent.
    return {"keys": [{"kty": "RSA", "pem": PUB_KEY_PATH.read_text()}]}
