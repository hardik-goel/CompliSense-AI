"""Drift core logic (Phase 2.2) — pure, no DB."""

from compliance.drift import compute_drift, posture_score, rule_states_from_findings


def test_posture_score_basic():
    assert posture_score({"passed": 3, "partial": 0, "failed": 1}) == 75.0
    assert posture_score({"passed": 1, "partial": 2, "failed": 1}) == 50.0  # (1 + 1)/4
    assert posture_score({"passed": 4, "partial": 0, "failed": 0}) == 100.0


def test_posture_score_none_when_no_applicable_rules():
    # not_applicable-only / empty must not read as a fake 0.
    assert posture_score({"passed": 0, "partial": 0, "failed": 0, "not_applicable": 5}) is None
    assert posture_score({}) is None
    assert posture_score(None) is None


def test_rule_states_extraction_drops_artefact_text():
    findings = {
        "results": [
            {"rule_id": "r1", "status": "pass", "title": "T1", "severity": "high", "evidence": {"raw": "secret"}},
            {"id": "r2", "status": "FAIL", "title": "T2", "severity": "low"},
        ]
    }
    states = rule_states_from_findings(findings)
    assert states == [
        {"rule_id": "r1", "status": "PASS", "title": "T1", "severity": "high"},
        {"rule_id": "r2", "status": "FAIL", "title": "T2", "severity": "low"},
    ]
    assert "evidence" not in states[0]  # raw artefact content never carried into history


def test_rule_states_handles_bad_input():
    assert rule_states_from_findings(None) == []
    assert rule_states_from_findings({"results": "nope"}) == []
    assert rule_states_from_findings({}) == []


def _s(rule_id, status):
    return {"rule_id": rule_id, "status": status, "title": rule_id, "severity": "medium"}


def test_regression_detected():
    prev = [_s("r1", "PASS"), _s("r2", "PASS")]
    curr = [_s("r1", "FAIL"), _s("r2", "PASS")]
    drift = compute_drift(prev, curr, 100.0, 50.0)
    assert drift["has_regression"] is True
    assert drift["counts"]["regressions"] == 1
    assert drift["regressions"][0]["rule_id"] == "r1"
    assert drift["regressions"][0]["from"] == "PASS"
    assert drift["regressions"][0]["to"] == "FAIL"
    assert drift["score_delta"] == -50.0


def test_improvement_and_resolution():
    prev = [_s("r1", "FAIL"), _s("r2", "MISSING")]
    curr = [_s("r1", "PASS"), _s("r2", "PARTIAL")]
    drift = compute_drift(prev, curr, 0.0, 75.0)
    assert drift["has_regression"] is False
    assert drift["counts"]["improvements"] == 2
    assert drift["score_delta"] == 75.0


def test_partial_is_between_fail_and_pass():
    # PASS -> PARTIAL is a regression; FAIL -> PARTIAL is an improvement.
    drift = compute_drift([_s("a", "PASS"), _s("b", "FAIL")], [_s("a", "PARTIAL"), _s("b", "PARTIAL")])
    assert drift["counts"]["regressions"] == 1
    assert drift["counts"]["improvements"] == 1


def test_added_and_removed_rules():
    drift = compute_drift([_s("old", "PASS")], [_s("new", "FAIL")])
    assert drift["counts"]["added"] == 1
    assert drift["counts"]["removed"] == 1
    assert drift["added"][0]["rule_id"] == "new"
    assert drift["removed"][0]["rule_id"] == "old"


def test_not_applicable_transitions_are_not_regressions():
    prev = [_s("r1", "PASS"), _s("r2", "NOT_APPLICABLE")]
    curr = [_s("r1", "NOT_APPLICABLE"), _s("r2", "PASS")]
    drift = compute_drift(prev, curr)
    assert drift["has_regression"] is False
    assert drift["counts"]["regressions"] == 0
    assert drift["counts"]["became_not_applicable"] == 1
    assert drift["counts"]["became_applicable"] == 1


def test_score_delta_none_when_missing_scores():
    drift = compute_drift([_s("r1", "PASS")], [_s("r1", "PASS")])
    assert drift["score_delta"] is None
    assert drift["counts"]["unchanged"] == 1
