"""Regulatory-change watcher core (Phase 5.1) — pure."""

from compliance.regwatch import collect_watch_sources, content_hash, detect_change, normalize_text


def test_normalize_ignores_cosmetic_whitespace():
    a = normalize_text("Section  5.\n\n  Notice   requirements. ")
    b = normalize_text("Section 5.\nNotice requirements.")
    assert a == b
    assert content_hash("Section  5. ") == content_hash("Section 5.")


def test_content_change_changes_hash():
    assert content_hash("Rule 6: 72 hours") != content_hash("Rule 6: 6 hours")


def test_collect_watch_sources_dedupes_and_maps_rules():
    packs = [
        {"pack_id": "dpdp_core", "rules": [
            {"id": "R1", "source_url": "https://law/a"},
            {"id": "R2", "source_url": "https://law/a"},
            {"id": "R3", "source_url": "https://law/b"},
            {"id": "R4"},  # no source_url -> ignored
        ]},
        {"pack_id": "dpdp_ext", "rules": [{"id": "R5", "source_url": "https://law/a"}]},
    ]
    sources = collect_watch_sources(packs)
    by_url = {s["url"]: s for s in sources}
    assert set(by_url) == {"https://law/a", "https://law/b"}
    assert by_url["https://law/a"]["rule_ids"] == ["R1", "R2", "R5"]
    assert by_url["https://law/a"]["pack_ids"] == ["dpdp_core", "dpdp_ext"]


def test_detect_change_baseline_then_change():
    base = detect_change(None, "text v1")
    assert base["is_baseline"] is True and base["changed"] is False
    same = detect_change(base["new_hash"], "text v1")
    assert same["changed"] is False
    changed = detect_change(base["new_hash"], "text v2")
    assert changed["changed"] is True and changed["new_hash"] != base["new_hash"]
