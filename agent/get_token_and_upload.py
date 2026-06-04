# agent/get_token_and_upload.py
import os

import requests
from pathlib import Path

SAAS_BASE = os.getenv("COMPLISENSE_API_URL", "https://api.complisenseai.com")
INSTALL_CODE = "one-time-install-123"

# 1: fetch token
r = requests.post(f"{SAAS_BASE}/auth/issue", json={"install_code": INSTALL_CODE})
r.raise_for_status()
token = r.json()["access_token"]

# 2: use token when uploading summary
headers = {"Authorization": f"Bearer {token}"}
summary = {"pack_id": "euai_core", "pack_version":"1.0.0", "summary":{"passed":2,"failed":1}}
r2 = requests.post(f"{SAAS_BASE}/results", json=summary, headers=headers)
print(r2.status_code, r2.text)
