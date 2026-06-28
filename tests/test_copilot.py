"""Remediation copilot core (Phase 7) — pure, injectable LLM, no SDK/network."""

from compliance.copilot import (
    DISCLAIMER, DRAFT_MARKER, SYSTEM_PROMPT, RemediationCopilot, _Refusal, build_context_block, default_llm,
)


RULE = {
    "rule_id": "DPDP-SEC5-NOTICE-001", "title": "Privacy notice",
    "rule_citation": "DPDP Rules 2025, Rule 3", "act_citation": "DPDP Act s.5",
    "framing": "Prepare by 2027-05-13 — not a present-day violation.",
    "requirement": "Provide an itemised, plain-language notice.",
}
FACTS = {"has_privacy_notice": False, "storage_locations": ["aws"]}


def test_context_block_has_rule_and_facts():
    block = build_context_block(RULE, FACTS)
    assert "DPDP Rules 2025, Rule 3" in block
    assert "has_privacy_notice: False" in block
    assert "CITED RULE" in block and "CONFIRMED FACTS" in block


def test_explain_passes_guardrailed_system_and_context():
    captured = {}
    def fake_llm(system, user):
        captured["system"], captured["user"] = system, user
        return "To be ready for the notice obligation, publish a plain-language notice."
    out = RemediationCopilot(fake_llm).explain(RULE, FACTS)
    assert out["mode"] == "explain" and out["grounded"] is True
    assert out["model"] == "claude-opus-4-8" and out["disclaimer"] == DISCLAIMER
    assert "NOT legal advice" in captured["system"] and "MUST NOT instruct" in captured["system"]
    assert "DPDP Rules 2025, Rule 3" in captured["user"]
    assert captured["system"] == SYSTEM_PROMPT


def test_draft_mode_stamps_legal_review_marker():
    # Model omits the marker -> draft() must inject it (belt-and-suspenders).
    out = RemediationCopilot(lambda s, u: "PRIVACY NOTICE\n...").draft(RULE, FACTS, "privacy policy section")
    assert out["mode"] == "draft"
    assert DRAFT_MARKER in out["answer"]
    assert "PRIVACY NOTICE" in out["answer"]
    assert out["draft_marker"] == DRAFT_MARKER


def test_draft_instruction_requests_marker():
    captured = {}
    RemediationCopilot(lambda s, u: captured.setdefault("u", u) or "x").draft(RULE, FACTS, "notice")
    assert DRAFT_MARKER in captured["u"]  # instruction tells the model to lead with it


def test_ungrounded_answer_flagged():
    msg = "I can't ground an answer in your data and the cited rule. Provide more detail or consult a qualified practitioner."
    out = RemediationCopilot(lambda s, u: msg).explain(RULE, {})
    assert out["grounded"] is False


def test_refusal_is_handled():
    def refusing(system, user):
        raise _Refusal()
    out = RemediationCopilot(refusing).explain(RULE, FACTS)
    assert out["grounded"] is False and "declined" in out["answer"].lower()


def test_default_llm_builds_without_anthropic_installed():
    # Constructing the callable must not import anthropic (import is lazy, inside the call).
    llm = default_llm()
    assert callable(llm)
