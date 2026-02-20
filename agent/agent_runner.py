from datetime import datetime
from pathlib import Path
import json

from agent.audit.trail import hash_directory
from agent.config import AgentConfig
from agent.report.dashboard import render_dashboard
from agent.report.exec_pdf import export_exec_pdf
from agent.report.export import export_dashboard
from agent.report.history import load_runs, compare_runs
from agent.report.screenshot import export_dashboard_images
from agent.report.trends import build_trends
from agent.rules.loader import load_rulepack, iter_rules
from agent.saas_upload import build_summary_payload, upload_summary
from agent.scanner import run_scan
from agent.report.render import render_pdf
from agent.scoring.heatmap import build_heatmap
from agent.scoring.overall import compute_overall_compliance, verdict_from_score
from agent.utils.resources import resource_path


def run_agent(
    model_root: str,
    out_dir: str,
    rulepack_path: str,
    progress_callback=None,
    config: AgentConfig = AgentConfig()
):
    root = Path(model_root)
    run_id = datetime.utcnow().strftime("run_%Y%m%dT%H%M%S")
    out = Path(out_dir) / run_id
    out.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback("Loading rulepack…")

    rp_path = Path(resource_path("rulepacks")) / rulepack_path
    rp = load_rulepack(rp_path)

    if progress_callback:
        progress_callback({"event": "INFO", "message": "Scanning model directory…"})

    rules = iter_rules(rp)

    if progress_callback:
        progress_callback({"event": "SCAN_START"})

    # ---- RUN SCAN ----
    results = run_scan(
        root,
        rules,
        llm_enabled=config.llm_enabled,
        progress_callback=progress_callback,
        cancel_event=config.cancel_flag
    )
    # ---- DERIVED COMPLIANCE ASSESSMENT ----

    artifacts = results["artifacts"]
    rule_results = results["results"]

    # Average rule confidence
    avg_rule_confidence = (
        sum(r["confidence"] for r in rule_results) / len(rule_results)
        if rule_results else 0
    )

    overall_compliance = compute_overall_compliance(
        artifacts_pct=artifacts["compliance_pct"],
        avg_rule_confidence=avg_rule_confidence
    )

    verdict = verdict_from_score(overall_compliance)

    why_not_compliant = {
        "missing_artifacts": [a["name"] for a in artifacts["missing"]],
        "failed_rules": [r["title"] for r in rule_results if r["status"] == "FAIL"]
    }

    assessment = {
        "verdict": verdict,
        "overall_compliance_pct": overall_compliance,
        "artifact_compliance_pct": artifacts["compliance_pct"],
        "avg_rule_confidence": round(avg_rule_confidence, 2),
        "why_not_compliant": why_not_compliant,
        "tier": getattr(config, "tier", "FREE")
    }

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

    runs = load_runs(Path(out_dir))
    trends = build_trends(runs) if len(runs) > 1 else None
    comparison = None

    if len(runs) >= 2:
        comparison = compare_runs(runs[-2], runs[-1])
    # ---- PDF ----
    pdf_path = out / "audit_report.pdf"
    render_pdf(
        {
            "summary": results["summary"],
            "results": results["results"],
            "artifacts": artifacts
        },
        assessment,
        pdf_path
    )

    if progress_callback:
        progress_callback("Generating dashboard…")

    # ---- DASHBOARD + HEATMAP ----
    heatmap = build_heatmap(results["results"])
    dashboard_path = render_dashboard(results, out, heatmap, comparison=comparison, trends=trends)
    export_exec_pdf(dashboard_path, out)
    try:
        export_dashboard_images(dashboard_path, out)
    except Exception:
        pass

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
        "assessment": assessment,
        "summary": results["summary"],
        "results": results["results"],
        "artifacts": artifacts,
        "json": str(findings_path),
        "pdf": str(pdf_path),
        "dashboard": str(dashboard_path)
    }
