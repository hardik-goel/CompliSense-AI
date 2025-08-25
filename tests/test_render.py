from pathlib import Path
from agent.report.render import render_pdf


def test_render_pdf(tmp_path: Path):
    results = {
        "summary": {"passed": 1, "failed": 0},
        "results": [
            {
                "rule_id": "R1",
                "clause": "Art.10",
                "title": "Dataset doc",
                "severity": "Critical",
                "status": "PASS",
                "context": {"exists": True}
            }
        ]
    }
    out_path = tmp_path / "report.pdf"
    render_pdf(results, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 0
