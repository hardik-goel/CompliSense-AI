"""Data-flow inference (Phase 4.2) — pure, names-only."""

from compliance.dataflow import DataSource, infer_data_flows, is_india_region


def test_india_region_detection():
    assert is_india_region("ap-south-1") and is_india_region("asia-south1")
    assert is_india_region("Central India") and is_india_region("centralindia")
    assert not is_india_region("us-east-1") and not is_india_region(None)


def test_maps_categories_to_sources():
    report = infer_data_flows([
        DataSource("users_db", ["user_email", "mobile_no"], provider="aws", region="ap-south-1"),
        DataSource("kyc_bucket", ["aadhaar_number", "pan"], provider="aws", region="ap-south-1"),
    ])
    c2s = report["category_to_sources"]
    assert c2s["email"] == ["users_db"]
    assert set(c2s["government_id"]) == {"kyc_bucket"}
    assert report["has_cross_border"] is False


def test_flags_cross_border_pii():
    report = infer_data_flows([
        DataSource("analytics", ["user_email", "latitude"], provider="gcp", region="us-central1"),
    ])
    assert report["has_cross_border"] is True
    cats = {c["category"] for c in report["cross_border"]}
    assert {"email", "location"} <= cats
    xb = next(s for s in report["suggestions"] if s["manifest_field"] == "cross_border_transfer")
    assert xb["suggested_value"] is True and xb["action"] == "review"


def test_suggests_pii_and_storage():
    report = infer_data_flows([
        DataSource("db", ["full_name", "credit_card"], provider="aws", region="ap-south-1"),
        DataSource("warehouse", ["email"], provider="gcp", region="asia-south1"),
    ])
    sug = {s["manifest_field"]: s for s in report["suggestions"]}
    assert set(sug["pii_categories"]["suggested_value"]) >= {"name", "financial", "email"}
    assert sug["storage_locations"]["suggested_value"] == ["aws", "gcp"]
    assert sug["storage_locations"]["action"] == "confirm"


def test_unknown_provider_dropped_from_storage():
    report = infer_data_flows([DataSource("x", ["email"], provider="oracle_cloud", region="ap-south-1")])
    sug = {s["manifest_field"]: s for s in report["suggestions"]}
    assert "storage_locations" not in sug  # oracle_cloud is not a manifest storage option


def test_no_region_is_not_cross_border():
    # Unknown region must not be assumed cross-border.
    report = infer_data_flows([DataSource("db", ["email"], provider="on_prem")])
    assert report["has_cross_border"] is False


def test_children_data_suggests_applicability_flag():
    report = infer_data_flows([DataSource("kids", ["minor_name", "guardian_email"], "aws", "ap-south-1")])
    sug = {s["manifest_field"]: s for s in report["suggestions"]}
    assert "processes_children_data" in sug
    assert sug["processes_children_data"]["suggested_value"] is True
    assert sug["processes_children_data"]["action"] == "review"


def test_no_children_no_applicability_flag():
    report = infer_data_flows([DataSource("db", ["user_email"], "aws", "ap-south-1")])
    assert "processes_children_data" not in {s["manifest_field"] for s in report["suggestions"]}


def test_empty():
    report = infer_data_flows([])
    assert report["sources"] == [] and report["suggestions"] == []
