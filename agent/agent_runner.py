from datetime import datetime
from pathlib import Path
import json

from agent.audit.trail import hash_directory
from agent.config import AgentConfig
from agent.report.dashboard import render_dashboard
from agent.rules.loader import load_rulepack, iter_rules
from agent.saas_upload import build_summary_payload, upload_summary
from agent.scanner import run_scan
from agent.report.render import render_pdf
from agent.scoring.heatmap import build_heatmap
from agent.utils.resources import resource_path


def run_agent(
    model_root: str,
    out_dir: str,
    rulepack_path: str,
    progress_callback=None,
    config: AgentConfig = AgentConfig()
):
    root = Path(model_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback("Loading rulepack…")

    rp = load_rulepack(resource_path(rulepack_path))

    if progress_callback:
        progress_callback("Scanning model directory…")

    rules = iter_rules(rp)

    if progress_callback:
        progress_callback("Running compliance checks…")

    # ---- RUN SCAN ----
    results = run_scan(
        root,
        rules
    )

    if progress_callback:
        progress_callback("Writing findings.json…")

    # ---- AUDIT TRAIL ----
    audit = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_hash": hash_directory(root),
        "rulepack_version": rp.get("version")
    }

    (out / "audit_trail.json").write_text(
        json.dumps(audit, indent=2),
        encoding="utf-8"
    )

    if progress_callback:
        progress_callback("Generating audit_report.pdf…")

    # ---- SAVE JSON ----
    findings_path = out / "findings.json"
    findings_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    if progress_callback:
        progress_callback("Generating PDF report…")

    # ---- PDF ----
    pdf_path = out / "audit_report.pdf"
    render_pdf(results, pdf_path)

    if progress_callback:
        progress_callback("Generating dashboard…")

    # ---- DASHBOARD + HEATMAP ----
    heatmap = build_heatmap(results["results"])
    dashboard_path = render_dashboard(results, out, heatmap)

    # ---- OPTIONAL SAAS UPLOAD ----
    if config.upload_enabled:
        payload = build_summary_payload(results)
        upload_summary(
            saas_url=config.saas_url,
            token=config.token,
            payload=payload
        )

    if progress_callback:
        progress_callback("Scan complete.")

    return {
        "json": str(findings_path),
        "pdf": str(pdf_path),
        "dashboard": str(dashboard_path),
        "summary": results["summary"]
    }
