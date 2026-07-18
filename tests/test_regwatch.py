"""Regulatory-change watcher core (Phase 5.1) — pure."""

from compliance.regwatch import (
    SEED_WATCHLIST,
    build_change_proposal,
    collect_watch_sources,
    content_hash,
    detect_change,
    diff_summary,
    draft_change_proposal,
    load_watchlist,
    match_rules_by_citation,
    merge_watch_sources,
    normalize_text,
    propose_action,
)


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


# ── Change-proposal pipeline (Phase 5.4) ─────────────────────────────────────

def test_merge_watch_sources_unions_seed():
    pack_sources = [{"url": "https://law/a", "rule_ids": ["R1"], "pack_ids": ["p"]}]
    merged = merge_watch_sources(pack_sources)
    by_url = {s["url"]: s for s in merged}
    # pack source preserved with its rule mapping
    assert by_url["https://law/a"]["rule_ids"] == ["R1"]
    # every seed URL is present, flagged seeded, with empty rule mapping
    for s in SEED_WATCHLIST:
        assert s["url"] in by_url
        assert by_url[s["url"]].get("seeded") is True


def test_merge_keeps_pack_mapping_when_url_also_seeded():
    # EUR-Lex is both cited by EU rules AND in the seed list — pack mapping must win.
    eurlex = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
    merged = merge_watch_sources([{"url": eurlex, "rule_ids": ["EUAI-ART9-RISK-MGMT-001"], "pack_ids": ["euai"]}])
    entry = {s["url"]: s for s in merged}[eurlex]
    assert entry["rule_ids"] == ["EUAI-ART9-RISK-MGMT-001"]


def test_diff_summary_counts_added_removed():
    d = diff_summary("line one\nline two", "line one\nline three\nline four")
    assert d["removed_count"] == 1 and d["added_count"] == 2
    assert "line three" in d["added_sample"] and "line two" in d["removed_sample"]


def test_match_rules_by_citation():
    rules = [
        {"id": "EUAI-ART50", "act_citation": "EU AI Act, Art. 50 (transparency)"},
        {"id": "EUAI-ART9", "act_citation": "EU AI Act, Art. 9 (risk management)"},
        {"id": "DPDP-S8", "act_citation": "DPDP Act 2023, s.8"},
    ]
    hits = match_rules_by_citation("Amendment to Article 50 marking obligations", rules)
    assert hits == ["EUAI-ART50"]


def test_propose_action_heuristics():
    assert propose_action({"added_sample": ["enforcement date moved to 2 Dec 2027"], "removed_sample": []}) == "date_change"
    assert propose_action({"added_sample": ["a new prohibition is introduced"], "removed_sample": []}) == "new_rule_stub"
    assert propose_action({"added_sample": ["editorial reword of a clause"], "removed_sample": []}) == "review_only"


def test_build_change_proposal_is_review_only_and_maps_rules():
    source = {"url": "https://eur-lex/ai", "label": "EUR-Lex", "rule_ids": ["EUAI-ART9"], "pack_ids": ["euai"]}
    rules = [{"id": "EUAI-ART50", "act_citation": "EU AI Act, Art. 50"}]
    proposal = build_change_proposal(
        source, prev_text="old text", new_text="new: Article 50 marking enforcement 2 Dec 2026", all_rules=rules,
    )
    assert proposal["auto_applied"] is False
    # URL-mapped rule ∪ citation-matched rule
    assert "EUAI-ART9" in proposal["affected_rule_ids"]
    assert "EUAI-ART50" in proposal["affected_rule_ids"]
    assert proposal["proposed_action"] in ("date_change", "new_rule_stub", "review_only")


def test_load_watchlist_from_config():
    # The shipped compliance/regwatch_sources.yaml drives the seed list.
    wl = load_watchlist()
    urls = {s["url"] for s in wl}
    assert any("eur-lex.europa.eu" in u for u in urls)
    assert any("meity.gov.in" in u for u in urls)
    assert all("url" in s for s in wl)


def test_draft_change_proposal_with_injected_llm():
    proposal = {
        "source": {"url": "https://eur-lex/ai", "label": "EUR-Lex"},
        "affected_rule_ids": ["EUAI-ART50-TRANSPARENCY-001"],
        "proposed_action": "date_change",
        "diff_summary": {"added_sample": ["Article 50 confirmed 2 Aug 2026"], "removed_sample": []},
    }
    seen = {}
    fake = lambda system, user: seen.update(system=system, user=user) or "Art 50 date reaffirmed."
    draft = draft_change_proposal(proposal, llm=fake)
    assert draft["affected_rule_ids"] == ["EUAI-ART50-TRANSPARENCY-001"]
    assert draft["proposed_action"] == "date_change"
    assert draft["summary"] == "Art 50 date reaffirmed."
    assert draft["draft_patch"]["auto_applied"] is False
    assert "Article 50" in seen["user"]  # diff excerpt reached the model


def test_draft_change_proposal_without_llm_is_safe():
    # No LLM injected -> still returns a well-formed draft (empty summary), never raises.
    draft = draft_change_proposal({"affected_rule_ids": [], "proposed_action": "review_only",
                                   "diff_summary": {}, "source": {}}, llm=None)
    assert draft["summary"] == "" and draft["draft_patch"]["auto_applied"] is False
