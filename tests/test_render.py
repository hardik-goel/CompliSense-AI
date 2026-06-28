from pathlib import Path
from agent.report.render import render_pdf


def test_render_pdf(tmp_path: Path):
    # Realistic scanner-shaped payload: render_pdf is always called with full run_scan
    # output (summary + results + artifacts) plus the cli-added report_context.
    results = {
        "summary": {"passed": 1, "partial": 0, "failed": 0, "not_applicable": 0},
        "results": [
            {
                "rule_id": "R1",
                "clause": "Art.10",
                "title": "Dataset doc",
                "severity": "Critical",
                "status": "PASS",
                "confidence": 100,
                "context": {"exists": True},
            }
        ],
        "artifacts": {
            "required_total": 1,
            "present": ["R1"],
            "missing": [],
            "compliance_pct": 100.0,
        },
        "report_context": {
            "rulepack_id": "dpdp_india_core",
            "rulepack_version": "1.0.0",
            "program_label": "DPDP-Core",
        },
    }
    out_path = tmp_path / "report.pdf"
    # Exercise the legacy 2-arg form (results, out_path).
    render_pdf(results, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 0
