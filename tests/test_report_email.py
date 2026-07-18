"""Emailed HTML readiness report — client + operator (Prompt 3B, Task 6)."""

from saas.app.report_email import (
    build_assessment_view,
    render_client_email,
    render_operator_email,
)

# Fixture assessment: 4 PASS / 1 GAP / 2 NA (mirrors the score_manifest report shape).
REPORT = {
    "readiness_score": 67,
    "scoring_available": True,
    "rules_current_as_of": "2026-07-18",
    "ready": [
        {"rule_id": "DPDP-SEC5-NOTICE-001", "title": "Privacy notice covers processing essentials"},
        {"rule_id": "DPDP-SEC6-CONSENT-001", "title": "Consent record and withdrawal mechanism documented"},
        {"rule_id": "DPDP-SEC8-OBLIGATIONS-001", "title": "Security safeguards and deletion controls documented"},
        {"rule_id": "DPDP-SEC13-GRIEVANCE-001", "title": "Grievance redressal workflow is documented"},
    ],
    "gaps": [
        {"rule_id": "DPDP-SEC8-OBLIGATIONS-002", "title": "Breach register structure is maintained",
         "severity": "Major", "status": "GAP",
         "act_citation": "DPDP Act 2023, s.8(6) (breach intimation)",
         "framing": "Prepare by 13 May 2027 (enforceable)."},
    ],
    "not_applicable": [
        {"rule_id": "DPDP-SEC10-SDF-001", "title": "Significant Data Fiduciary obligations are mapped",
         "reason": "Not a Significant Data Fiduciary — DPO/DPIA not required. threshold detail"},
        {"rule_id": "DPDP-SEC9-CHILDREN-001", "title": "Children's data safeguards are documented",
         "reason": "No children's data processed."},
    ],
}

ANSWERS = {"sector": "saas", "registered_users": 12000, "processes_children_data": False, "notified_as_sdf": False}


def _view():
    return build_assessment_view(REPORT, ANSWERS, "founder@startup.example",
                                 cta_url="https://calendly.com/x?email=founder%40startup.example",
                                 submitted_at="2026-07-18T10:00:00", unsubscribe_contact="privacy@complisenseai.com")


def test_client_email_renders_all_sections():
    subject, html = render_client_email(_view())
    # subject line
    assert "67%" in subject and "1 gap" in subject and "May 2027" in subject
    # 4 passes all present
    for t in ["Privacy notice covers processing essentials", "Consent record and withdrawal",
              "Security safeguards", "Grievance redressal workflow"]:
        assert t in html
    # the 1 gap with its FULL citation (not truncated, not empty — ties to the P3 gaps bug)
    assert "Breach register structure is maintained" in html
    assert "DPDP Act 2023, s.8(6) (breach intimation)" in html
    # NA items present
    assert "Significant Data Fiduciary obligations are mapped" in html
    assert "Children&#39;s data safeguards are documented" in html or "Children's data safeguards are documented" in html
    # exactly ONE primary CTA button
    assert html.count("Book a 20-minute call") == 1
    # disclaimer + rules-current date
    assert "not legal advice" in html.lower() and "2026-07-18" in html
    assert "attorney-client" in html.lower()


def test_operator_email_has_intel_and_raw_answers():
    view = _view()
    subject, html = render_operator_email(view)
    assert "founder@startup.example" in html
    # intel block: sector, users, gap-by-severity, suggested angle (whatever it computed)
    assert "saas" in html and "12000" in html
    assert "Major" in html
    assert view["suggested_angle"] in html and view["suggested_angle"]
    # raw answers table
    assert "registered_users" in html
    # still carries findings + disclaimer + date
    assert "Breach register structure is maintained" in html
    assert "2026-07-18" in html


def test_suggested_angle_rules():
    # >=2 Major/Critical gaps -> pilot fit
    r = dict(REPORT, gaps=[
        {"rule_id": "A", "title": "A", "severity": "Major", "status": "GAP", "act_citation": "x"},
        {"rule_id": "B", "title": "B", "severity": "Critical", "status": "GAP", "act_citation": "y"},
    ])
    v = build_assessment_view(r, ANSWERS, "e@x.com", "u", "t", "p")
    assert v["suggested_angle"] == "Strong done-with-me pilot fit."
    # only PARTIALs -> nurture
    r2 = dict(REPORT, gaps=[{"rule_id": "A", "title": "A", "severity": "Minor", "status": "NEEDS_REVIEW", "act_citation": "x"}])
    v2 = build_assessment_view(r2, ANSWERS, "e@x.com", "u", "t", "p")
    assert v2["suggested_angle"] == "Light-touch; likely self-serve, nurture."
    # children's data -> higher stakes (overrides)
    v3 = build_assessment_view(r, {**ANSWERS, "processes_children_data": True}, "e@x.com", "u", "t", "p")
    assert "Higher-stakes" in v3["suggested_angle"]


def test_html_injection_via_answers_is_escaped():
    v = build_assessment_view(REPORT, {**ANSWERS, "sector": "<script>alert(1)</script>"},
                              "e@x.com", "u", "t", "p")
    _, html = render_operator_email(v)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_no_gap_never_renders_empty_when_gaps_exist():
    # ties to P3 bug: a detected gap must appear, not just be counted.
    _, html = render_client_email(_view())
    assert html.count("Breach register structure is maintained") >= 1
