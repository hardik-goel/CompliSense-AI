"""Record of Processing Activities (ROPA) builder — deterministic, from confirmed facts."""

from compliance.dataflow import DataSource, infer_data_flows
from compliance.ropa import (
    UNKNOWN,
    ProcessingActivity,
    build_ropa,
    ropa_to_markdown,
)

BASE = {
    "entity_type": "startup",
    "sector": "saas",
    "offers_in_india": True,
    "pii_categories": ["email", "phone"],
    "storage_locations": ["aws"],
    "consent_mechanism": "explicit_optin",
    "retention_defined": True,
    "grievance_email": "dpo@example.com",
}


def _flow():
    return infer_data_flows([
        DataSource(name="users_db", field_names=["email", "phone", "full_name"],
                   provider="aws", region="ap-south-1"),
        DataSource(name="analytics", field_names=["email", "latitude"],
                   provider="gcp", region="us-central1"),
    ])


# --- rows ---------------------------------------------------------------------------

def test_declared_activity_becomes_a_row_with_its_purpose():
    ropa = build_ropa(BASE, activities=[ProcessingActivity(
        activity_id="signup", purpose="Account creation and login",
        categories=["email"], data_principals=["customers"],
        stores=["users_db"], retention="24 months after account closure",
        processors=["AWS"])])
    assert len(ropa["rows"]) == 1
    row = ropa["rows"][0]
    assert row["purpose"] == "Account creation and login"
    assert row["categories"] == ["email"]
    assert row["retention"] == "24 months after account closure"
    assert row["provenance"] == "declared"


def test_without_activities_rows_are_derived_per_store_with_unknown_purpose():
    ropa = build_ropa(BASE, flow_report=_flow())
    names = {r["store"] for r in ropa["rows"]}
    assert names == {"users_db", "analytics"}
    assert all(r["purpose"] == UNKNOWN for r in ropa["rows"])
    assert all(r["provenance"] == "inferred" for r in ropa["rows"])


def test_falls_back_to_declared_storage_locations_when_no_flow_report():
    ropa = build_ropa(BASE)
    assert [r["store"] for r in ropa["rows"]] == ["aws"]
    assert ropa["rows"][0]["categories"] == ["email", "phone"]


def test_inferred_row_carries_categories_and_evidence_field_names():
    ropa = build_ropa(BASE, flow_report=_flow())
    users = next(r for r in ropa["rows"] if r["store"] == "users_db")
    assert set(users["categories"]) >= {"email", "phone", "name"}
    # Field NAMES are the evidence we surface; values never are.
    assert "email" in users["evidence_field_names"]


# --- cross-border -------------------------------------------------------------------

def test_non_india_store_is_flagged_cross_border_on_its_row():
    ropa = build_ropa(BASE, flow_report=_flow())
    users = next(r for r in ropa["rows"] if r["store"] == "users_db")
    analytics = next(r for r in ropa["rows"] if r["store"] == "analytics")
    assert users["cross_border"] is False
    assert analytics["cross_border"] is True
    assert analytics["region"] == "us-central1"
    assert ropa["has_cross_border"] is True


# --- legal basis --------------------------------------------------------------------

def test_legal_basis_follows_declared_consent_mechanism():
    assert build_ropa(BASE)["rows"][0]["legal_basis"] == "consent"


def test_legal_basis_is_unknown_when_no_consent_mechanism_declared():
    ropa = build_ropa({**BASE, "consent_mechanism": "none"})
    assert ropa["rows"][0]["legal_basis"] == UNKNOWN


# --- honesty: unknowns are never dressed up as complete -----------------------------

def test_undefined_retention_becomes_unknown_and_is_listed_as_a_gap():
    ropa = build_ropa({**BASE, "retention_defined": False})
    assert ropa["rows"][0]["retention"] == UNKNOWN
    assert any(u["field"] == "retention" for u in ropa["unknowns"])


def test_unknown_purpose_is_listed_with_how_to_fill_guidance():
    ropa = build_ropa(BASE)
    purpose_gap = next(u for u in ropa["unknowns"] if u["field"] == "purpose")
    assert purpose_gap["how_to_fill"]


def test_completeness_is_below_100_while_anything_is_unknown():
    ropa = build_ropa(BASE)
    assert ropa["unknowns"]
    assert ropa["completeness"]["percent"] < 100


def test_completeness_reaches_100_when_every_field_is_declared():
    ropa = build_ropa(BASE, activities=[ProcessingActivity(
        activity_id="signup", purpose="Account creation", categories=["email"],
        data_principals=["customers"], stores=["users_db"], retention="24 months",
        legal_basis="consent", processors=["AWS"])])
    assert ropa["unknowns"] == []
    assert ropa["completeness"]["percent"] == 100


# --- controller block + provenance ---------------------------------------------------

def test_controller_block_carries_entity_facts_and_grievance_contact():
    c = build_ropa(BASE)["controller"]
    assert c["entity_type"] == "startup" and c["sector"] == "saas"
    assert c["grievance_contact"] == "dpo@example.com"
    assert c["is_significant_data_fiduciary"] is False


def test_supports_rules_are_cited_and_ropa_is_not_claimed_as_a_named_duty():
    ropa = build_ropa(BASE)
    assert "DPDP-SEC8-PROCESSOR-001" in ropa["supports_rules"]
    assert "DPDP-SEC16-TRANSFER-001" in ropa["supports_rules"]
    assert "not a named" in ropa["notes"]["status"].lower()


def test_generated_at_is_caller_supplied_so_the_builder_stays_pure():
    assert build_ropa(BASE, generated_at="2026-08-11T00:00:00Z")["generated_at"] == "2026-08-11T00:00:00Z"
    assert build_ropa(BASE)["generated_at"] is None


# --- markdown render ------------------------------------------------------------------

def test_markdown_renders_a_table_row_per_activity():
    md = ropa_to_markdown(build_ropa(BASE, flow_report=_flow()))
    assert "| users_db |" in md and "| analytics |" in md


def test_markdown_carries_the_legal_review_disclaimer_and_unknown_section():
    md = ropa_to_markdown(build_ropa(BASE))
    assert "REQUIRES LEGAL REVIEW" in md.upper()
    assert UNKNOWN in md


# --- DPDPA domain overlay ---------------------------------------------------------------

def test_each_row_is_tagged_with_the_dpdpa_domains_that_apply_to_it():
    ropa = build_ropa(BASE, flow_report=_flow())
    analytics = next(r for r in ropa["rows"] if r["store"] == "analytics")
    users = next(r for r in ropa["rows"] if r["store"] == "users_db")
    assert 4 in users["domains"] and 8 not in users["domains"]
    assert 8 in analytics["domains"]


def test_register_lists_the_domains_applicable_to_the_fiduciary_with_titles():
    domains = build_ropa({**BASE, "cross_border_transfer": True})["domains"]
    assert 8 in domains["applicable"]
    assert any(d["title"] == "Cross-border data transfer" for d in domains["legend"])
    assert all(d["act_citation"] for d in domains["legend"])


def test_domain_legend_always_carries_all_eight_even_when_not_applicable():
    domains = build_ropa(BASE)["domains"]
    assert [d["number"] for d in domains["legend"]] == list(range(1, 9))
    assert 6 not in domains["applicable"]


def test_markdown_renders_the_domain_column_and_the_domain_legend():
    md = ropa_to_markdown(build_ropa(BASE, flow_report=_flow()))
    assert "DPDPA domains" in md
    assert "Cross-border data transfer" in md
