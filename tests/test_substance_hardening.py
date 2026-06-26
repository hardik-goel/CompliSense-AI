"""file_presence must verify substance, not mere presence (audit H6)."""

import json
from pathlib import Path

from agent.evaluators.file_presence import run, _is_empty_value, _validate_value


def _write(tmp_path: Path, payload: dict) -> Path:
    f = tmp_path / "doc.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    return tmp_path


def test_placeholder_values_count_as_missing(tmp_path: Path):
    root = _write(tmp_path, {"a": "TODO", "b": "real value", "c": "  ", "d": "changeme"})
    ctx = run(root, {"file": "doc.json", "required_json_fields": ["a", "b", "c", "d"]})
    assert set(ctx["missing_fields_list"]) == {"a", "c", "d"}
    assert ctx["missing_fields"] == 3


def test_real_values_pass(tmp_path: Path):
    root = _write(tmp_path, {"a": "Acme Pvt Ltd", "b": ["x", "y"]})
    ctx = run(root, {"file": "doc.json", "required_json_fields": ["a", "b"]})
    assert ctx["missing_fields"] == 0


def test_email_validation_flags_non_email(tmp_path: Path):
    root = _write(tmp_path, {"grievance_contact": "call us"})
    ctx = run(root, {
        "file": "doc.json",
        "required_json_fields": ["grievance_contact"],
        "field_validations": {"grievance_contact": "email"},
    })
    assert "grievance_contact" in ctx["invalid_fields_list"]
    assert ctx["missing_fields"] == 1


def test_email_validation_accepts_email(tmp_path: Path):
    root = _write(tmp_path, {"grievance_contact": "privacy@acme.example"})
    ctx = run(root, {
        "file": "doc.json",
        "required_json_fields": ["grievance_contact"],
        "field_validations": {"grievance_contact": "email"},
    })
    assert ctx["invalid_fields_list"] == []
    assert ctx["missing_fields"] == 0


def test_iso_date_validation(tmp_path: Path):
    root = _write(tmp_path, {"d": "not-a-date"})
    ctx = run(root, {
        "file": "doc.json",
        "required_json_fields": ["d"],
        "field_validations": {"d": "iso_date"},
    })
    assert ctx["missing_fields"] == 1


def test_is_empty_helpers():
    assert _is_empty_value("TODO")
    assert _is_empty_value("")
    assert _is_empty_value(None)
    assert _is_empty_value([])
    assert not _is_empty_value("real")
    assert not _is_empty_value(0)


def test_validate_value_specs():
    assert _validate_value("a@b.co", "email")
    assert not _validate_value("nope", "email")
    assert _validate_value("2027-05-13", "iso_date")
    assert _validate_value("https://x.io", "url")
    assert _validate_value("abcdef", "min_length:3")
    assert not _validate_value("ab", "min_length:3")


# ── schema_validate substantive coverage (gap 3) + techdoc substance (gap 5) ──

import json as _json
from agent.evaluators.schema_validate import _substantive_coverage
from agent.evaluators import techdoc_coverage


def test_substantive_coverage_empty_doc_is_zero():
    schema = {"required": ["a", "b", "c", "d"]}
    assert _substantive_coverage({}, schema) == 0.0
    assert _substantive_coverage({"a": "TODO", "b": ""}, schema) == 0.0


def test_substantive_coverage_partial_and_full():
    schema = {"required": ["a", "b", "c", "d"]}
    assert _substantive_coverage({"a": "x", "b": "y"}, schema) == 0.5
    assert _substantive_coverage({"a": "x", "b": "y", "c": "z", "d": "w"}, schema) == 1.0


def test_schema_validate_empty_but_valid_is_not_full_coverage(tmp_path):
    # Schema only requires presence/typing; an all-placeholder doc is structurally valid
    # but must NOT score full coverage.
    schema = {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
    (tmp_path / "s.json").write_text(_json.dumps(schema))
    (tmp_path / "d.json").write_text(_json.dumps({"a": "TODO", "b": "n/a"}))
    from agent.evaluators.schema_validate import run as sv_run
    ctx = sv_run(tmp_path, {"file": "d.json", "schema_file": "s.json"})
    assert ctx["schema_valid"] is True
    assert ctx["coverage"] == 0.0  # valid structure, zero substance


def test_techdoc_empty_model_card_scores_low(tmp_path):
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "model_card.json").write_text("{}")
    out = techdoc_coverage.run(tmp_path, {"explicit_files": ["model/model_card.json"]})
    assert out["coverage_score"] == 0.0


def test_techdoc_populated_model_card_scores_high(tmp_path):
    (tmp_path / "model").mkdir()
    payload = {k: "real value" for k in
               ["intended_purpose", "architecture", "training_data_refs", "eval_metrics",
                "known_limitations", "release_version"]}
    (tmp_path / "model" / "model_card.json").write_text(_json.dumps(payload))
    out = techdoc_coverage.run(tmp_path, {"explicit_files": ["model/model_card.json"]})
    assert out["coverage_score"] == 0.7  # 6/6 populated -> full explicit credit
