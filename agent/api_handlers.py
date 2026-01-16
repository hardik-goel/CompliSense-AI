# agent/api_handlers.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import tempfile, requests, os, shutil, json
from typing import Optional
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf
from agent.db.mongo import insert_report, get_mongo_client  # optional for direct insert
import logging

app = FastAPI(title="CompliSense Local Agent API")
log = logging.getLogger("agent.api")

class RunRequest(BaseModel):
    model_root: str
    output_dir: str
    rulepack_source: Optional[str] = "embed"  # "embed" | "url" | "local"
    rulepack_path: Optional[str] = None       # if local
    rulepack_url: Optional[str] = None        # if url
    upload_summary: bool = False
    saas_url: Optional[str] = None
    saas_token: Optional[str] = None  # Bearer token to upload summary (if any)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(req: RunRequest):
    """
    Main run endpoint: download the rulepack if needed, run the scanner locally,
    write findings.json and PDF to output_dir, optionally upload summary to SaaS.
    """
    model_root = Path(req.model_root).resolve()
    output_dir = Path(req.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: obtain rulepack path
    rp_path = None
    tempdir = None
    try:
        if req.rulepack_source == "embed":
            # Assume the agent bundle contains a copy at ./rulepacks/euai_core_v1.yaml
            rp_path = Path(__file__).parents[1] / "rulepacks" / "euai_core_v1.yaml"
            if not rp_path.exists():
                raise HTTPException(status_code=400, detail="Embedded rulepack not found in agent bundle.")
        elif req.rulepack_source == "local":
            if not req.rulepack_path:
                raise HTTPException(status_code=400, detail="rulepack_path required when rulepack_source=local")
            rp_path = Path(req.rulepack_path).resolve()
            if not rp_path.exists():
                raise HTTPException(status_code=404, detail="Local rulepack not found.")
        elif req.rulepack_source == "url":
            if not req.rulepack_url:
                raise HTTPException(status_code=400, detail="rulepack_url required when source=url")
            # download to temp
            tempdir = Path(tempfile.mkdtemp(prefix="rules_"))
            r = requests.get(req.rulepack_url, timeout=30)
            r.raise_for_status()
            rp_path = tempdir / "rulepack.yaml"
            rp_path.write_bytes(r.content)
            # Optional: verify signature here
        else:
            raise HTTPException(status_code=400, detail="invalid rulepack_source")

        # Step 2: load rulepack & rules
        pack = load_rulepack(rp_path)
        rules = iter_rules(pack)

        # Step 3: Run scanner
        results = run_scan(model_root, rules)

        # Step 4: Save JSON + PDF
        findings_path = output_dir / "findings.json"
        findings_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

        pdf_path = output_dir / "audit_report.pdf"
        render_pdf(results, pdf_path)

        # Step 5: Optionally upload summary to SaaS (only minimal metadata + summary)
        if req.upload_summary:
            if not req.saas_url or not req.saas_token:
                raise HTTPException(status_code=400, detail="saas_url and saas_token required to upload")
            payload = {
                "run_id": results.get("run_id") if results.get("run_id") else None,
                "pack_id": pack.get("pack_id"),
                "pack_version": pack.get("version"),
                "project_root": str(model_root),
                "summary": results.get("summary"),
                # do not send full raw results unless explicit consent
            }
            headers = {"Authorization": f"Bearer {req.saas_token}", "Content-Type": "application/json"}
            r = requests.post(f"{req.saas_url.rstrip('/')}/results", json=payload, headers=headers, timeout=30)
            if r.status_code >= 400:
                log.error("Failed to upload summary: %s %s", r.status_code, r.text)
                # don't fail run; just record upload failure
                results["_upload_error"] = {"status": r.status_code, "text": r.text}

        return {"status": "ok", "findings": str(findings_path), "pdf": str(pdf_path), "summary": results.get("summary")}
    finally:
        if tempdir:
            shutil.rmtree(tempdir, ignore_errors=True)
