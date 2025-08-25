from pathlib import Path
from agent.scanner import run_scan


def test_run_scan_with_mock_evaluator(monkeypatch, tmp_path: Path):
    # Create dummy evaluator
    def fake_run(root, inputs):
        return {"exists": True, "missing_fields": 0}

    monkeypatch.setattr("agent.scanner._run_evaluator", lambda r, e, i: fake_run(r, i))

    rules = [{
        "id": "R1",
        "clause": "Art.10",
        "title": "Dataset documentation completeness",
        "severity": "Critical",
        "evaluator": "file_presence",
        "inputs": {"file": "dummy.json"},
        "expression": "exists and missing_fields == 0"
    }]

    results = run_scan(tmp_path, rules)
    assert results["summary"]["passed"] == 1
    assert results["results"][0]["status"] == "PASS"
