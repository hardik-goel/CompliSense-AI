"""Artefact generator catalog (Tier-1.5) — pure."""

from compliance.artefacts import CONNECTABLE_SOURCES, needed_artefacts, spec_for


def test_connectable_sources_are_the_four_connectors():
    assert CONNECTABLE_SOURCES == ["AWS", "GCP", "Azure", "GitHub"]


def test_needed_maps_gaps_to_artefacts_with_sources():
    project = {"discovered_manifest": {"has_security_safeguards": True}}
    needed = needed_artefacts(["DPDP-SEC5-NOTICE-001", "DPDP-SEC8-OBLIGATIONS-001"], project)
    ids = {a["artefact_id"] for a in needed}
    assert {"privacy_notice", "security_safeguards"} <= ids
    sec = next(a for a in needed if a["artefact_id"] == "security_safeguards")
    # connector source is available (project has discovered facts)
    conn = next(s for s in sec["sources"] if s["source"] == "connector_discovery")
    assert conn["available"] is True
    assert sec["draftable"] is True


def test_connector_source_unavailable_without_discovery():
    needed = needed_artefacts(["DPDP-SEC8-OBLIGATIONS-001"], {})
    sec = needed[0]
    conn = next(s for s in sec["sources"] if s["source"] == "connector_discovery")
    assert conn["available"] is False  # no discovered_manifest -> can't auto-fill


def test_manual_artefact_flagged():
    needed = needed_artefacts(["DPDP-SEC8-PROCESSOR-001"], {})
    proc = needed[0]
    assert proc["manual_note"] and any(s["source"] == "manual" for s in proc["sources"])


def test_unknown_gap_skipped_and_deduped():
    needed = needed_artefacts(["NOPE-001", "DPDP-SEC5-NOTICE-001", "DPDP-SEC5-NOTICE-001"], {})
    assert len(needed) == 1 and needed[0]["artefact_id"] == "privacy_notice"


def test_spec_for_roundtrip():
    s = spec_for("retention_schedule")
    assert s and s["rule_id"] == "DPDP-SEC8-OBLIGATIONS-003" and s["filename"] == "retention_schedule.md"
    assert spec_for("does_not_exist") is None
