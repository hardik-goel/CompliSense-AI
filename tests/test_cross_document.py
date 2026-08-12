"""Cross-document consistency checks (audit gap 4)."""

import json

from compliance.cross_document import run_consistency_checks
from agent.scanner import run_scan


CHECK = [{
    "id": "C1",
    "description": "fiduciary name matches",
    "sources": [["a.json", "name"], ["b.json", "name"]],
}]


def test_consistent_values_no_finding(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"name": "Acme Pvt Ltd"}))
    (tmp_path / "b.json").write_text(json.dumps({"name": "acme pvt ltd"}))  # case-insensitive match
    assert run_consistency_checks(tmp_path, CHECK) == []


def test_contradiction_flagged(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"name": "Acme Pvt Ltd"}))
    (tmp_path / "b.json").write_text(json.dumps({"name": "Globex Inc"}))
    out = run_consistency_checks(tmp_path, CHECK)
    assert len(out) == 1
    assert out[0]["status"] == "INCONSISTENT"
    assert out[0]["severity"] == "Advisory"


def test_single_source_present_no_finding(tmp_path):
    # Only one of the two named sources exists → cannot contradict.
    (tmp_path / "a.json").write_text(json.dumps({"name": "Acme"}))
    assert run_consistency_checks(tmp_path, CHECK) == []


def test_run_scan_attaches_consistency(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"name": "Acme"}))
    (tmp_path / "b.json").write_text(json.dumps({"name": "Globex"}))
    out = run_scan(tmp_path, [], consistency_checks=CHECK)
    # run_scan early-returns on empty rules; consistency runs only on the full path,
    # so use a trivial rule to reach the consistency stage.
    rules = [{
        "id": "R1", "evaluator": "file_presence",
        "inputs": {"file": "a.json", "required_json_fields": ["name"]},
        "expression": "exists", "severity": "Major",
    }]
    out = run_scan(tmp_path, rules, consistency_checks=CHECK)
    assert any(f["id"] == "C1" for f in out["consistency"])


def test_consistency_off_by_default(tmp_path):
    rules = [{
        "id": "R1", "evaluator": "file_presence",
        "inputs": {"file": "a.json", "required_json_fields": ["name"]},
        "expression": "exists", "severity": "Major",
    }]
    (tmp_path / "a.json").write_text(json.dumps({"name": "Acme"}))
    out = run_scan(tmp_path, rules)  # no checks passed
    assert out["consistency"] == []
