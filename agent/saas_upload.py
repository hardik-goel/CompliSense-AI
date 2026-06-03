import requests
from datetime import datetime

def build_summary_payload(project_id_or_results, results: dict | None = None, scan_id: str | None = None, scan_name: str | None = None):
    if isinstance(project_id_or_results, dict) and results is None:
        project_id = "local_project"
        findings = project_id_or_results
    else:
        project_id = project_id_or_results
        findings = results or {}
    return {
        "project_id": project_id,
        "scan_summary": findings.get("summary", {}),
        "findings_json": findings,
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
