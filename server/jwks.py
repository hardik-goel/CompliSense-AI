# server/jwks.py
from fastapi import FastAPI
from pathlib import Path
import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes

app = FastAPI()

PUB_KEY_PATH = Path("/Users/hardikgoel/compli-keys/public.pem")
pub_pem = PUB_KEY_PATH.read_text()

@app.get("/.well-known/jwks.json")
def jwks():
    # Simple conversion: serve PEM as-is (agent can load PEM)
    # For full JWKS, convert to modulus/exponent
    return {"keys": [{"kty":"RSA", "pem": pub_pem}]}
