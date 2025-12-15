from pathlib import Path

from agent.config import AgentConfig
from agent.report.dashboard import render_dashboard
from agent.rules.loader import load_rulepack, iter_rules
from agent.saas_upload import build_summary_payload, upload_summary
from agent.scanner import run_scan
from agent.report.render import render_pdf
import json


def run_agent(
    model_root: str,
    out_dir: str,
    rulepack_path: str,
    config: AgentConfig = AgentConfig()   # ← NEW
):
    root = Path(model_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Run TruthModule
    rp = load_rulepack(Path(rulepack_path))
    results = run_scan(root, iter_rules(rp))

    # Save JSON
    findings_path = out / "findings.json"
    findings_path.write_text(json.dumps(results, indent=2))

    # Save PDF
    pdf_path = out / "audit_report.pdf"
    render_pdf(results, pdf_path)

    # Save Dashboard
    dashboard_path = render_dashboard(results, out)

    # OPTIONAL: upload summary to SaaS
    if config.upload_enabled:
        payload = build_summary_payload(results)
        upload_summary(
            saas_url=config.saas_url,
            token=config.token,
            payload=payload
        )


    return {
        "json": str(findings_path),
        "pdf": str(pdf_path),
        "dashboard": str(dashboard_path),
        "summary": results["summary"]
    }
