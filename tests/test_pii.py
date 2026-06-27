"""PII inference from field names (Phase 4.1) — pure, names-only."""

from compliance.pii import infer_pii, pii_to_suggestion


def _cats(findings):
    return {f.category for f in findings}


def test_infers_common_categories():
    cats = _cats(infer_pii(["user_email", "mobile_no", "pan_number", "full_name", "latitude"]))
    assert {"email", "phone", "government_id", "name", "location"} <= cats


def test_camelcase_and_keys():
    cats = _cats(infer_pii(["userEmailID", "creditCardNumber", "bloodGroup"]))
    assert {"email", "financial", "health"} <= cats


def test_short_keyword_requires_exact_token_no_false_positive():
    # "company" must NOT match government_id via substring "pan".
    assert _cats(infer_pii(["company", "panel_id", "spanish_name"])) & {"government_id"} == set()
    # exact token "pan" does match.
    assert "government_id" in _cats(infer_pii(["pan"]))


def test_confidence_levels():
    findings = {f.category: f for f in infer_pii(["aadhaar_number", "name"])}
    assert findings["government_id"].confidence == "high"
    assert findings["name"].confidence == "low"


def test_matched_on_records_field_names_not_values():
    findings = {f.category: f for f in infer_pii(["primary_email", "backup_email"])}
    assert findings["email"].matched_on == ["backup_email", "primary_email"]


def test_no_pii_returns_empty():
    assert infer_pii(["created_at", "row_id", "status", "count"]) == []
    assert infer_pii([]) == []
    assert infer_pii([None, "", 5]) == []


def test_suggestion_maps_to_manifest_field():
    sug = pii_to_suggestion(infer_pii(["user_email", "aadhaar"]))
    assert sug.manifest_field == "pii_categories"
    assert set(sug.suggested_value) == {"email", "government_id"}
    assert sug.action == "review"  # PII is always human-confirmed
    assert sug.confidence == "high"
    assert "user_email" in sug.evidence_signals


def test_suggestion_none_when_no_findings():
    assert pii_to_suggestion([]) is None
