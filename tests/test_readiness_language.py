"""Verdict/output language must be readiness-based, never a compliance determination."""

from agent.scoring.overall import verdict_from_score, readiness_framing


def test_no_verdict_says_compliant():
    for score in (10, 50, 60, 85, 99, 100):
        verdict = verdict_from_score(score).upper()
        assert "COMPLIANT" not in verdict, f"verdict leaked compliance language: {verdict}"


def test_verdicts_use_readiness_words():
    assert "READY" in verdict_from_score(90).upper()
    assert "GAPS" in verdict_from_score(60).upper()
    assert "NOT READY" in verdict_from_score(10).upper()


def test_readiness_framing_phased_is_prepare_not_violation():
    msg = readiness_framing("2027-05-13", "phased_confirmed").lower()
    assert "prepare by" in msg
    assert "violation" in msg  # phrased as "not a present-day violation"
    assert "not a present-day violation" in msg


def test_readiness_framing_provisional_flags_movement():
    msg = readiness_framing("2027-12-02", "provisional_pending_amendment").lower()
    assert "provisional" in msg


def test_readiness_framing_in_force():
    assert "enforceable now" in readiness_framing(None, "in_force").lower()
