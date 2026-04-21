import requests
from datetime import datetime

def build_summary_payload(project_id: str, results: dict, scan_id: str | None = None, scan_name: str | None = None):
    return {
        "project_id": project_id,
        "scan_summary": results.get("summary", {}),
        "findings_json": results,
        "timestamp": datetime.utcnow().isoformat(),
        "scan_id": scan_id,
        "scan_name": scan_name,
    }

def upload_summary(saas_url: str, token: str, payload: dict):
    headers = {
        "X-API-Key": token,
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{saas_url.rstrip('/')}/api/v1/upload-scan",
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json()
