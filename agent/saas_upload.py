import requests

def build_summary_payload(results: dict):
    return {
        "pack_id": "euai_core",
        "summary": results["summary"],
        "rules": [
            {
                "rule_id": r["rule_id"],
                "clause": r["clause"],
                "severity": r["severity"],
                "status": r["status"]
            }
            for r in results["results"]
        ]
    }

def upload_summary(saas_url: str, token: str, payload: dict):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{saas_url.rstrip('/')}/results",
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json()
