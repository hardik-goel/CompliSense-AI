from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf
import json

def run_agent(model_root: str, out_dir: str, rulepack_path: str):
    root = Path(model_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rp = load_rulepack(Path(rulepack_path))
    results = run_scan(root, iter_rules(rp))

    # Save JSON
    findings_path = out / "findings.json"
    findings_path.write_text(json.dumps(results, indent=2))

    # Save PDF
    pdf_path = out / "audit_report.pdf"
    render_pdf(results, pdf_path)

    return {
        "json": str(findings_path),
        "pdf": str(pdf_path),
        "summary": results["summary"]
    }
