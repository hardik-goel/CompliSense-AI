"""Regulatory-change watcher core (Phase 5.1).

Monitors the LAW (the primary sources our rulepacks cite), not the customer. When a watched
source changes, we raise a **human-gated** review item — we never silently edit a rulepack or
rescore anyone. A qualified human decides whether the change affects our rules and updates
them against `LEGAL_REVIEW_NEEDED.md`.

This module is the pure core: derive the watch list from loaded rulepacks, normalize +
hash fetched content, and detect a change vs the last snapshot. I/O (fetching, persistence,
scheduling) lives in the API/cron layer.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

# Seed watchlist (Phase 5.4): the primary legal sources we monitor for change, independent of
# whether a rule currently cites them. These are unioned with the pack-derived sources so we
# notice a change (e.g. a new MeitY notification) BEFORE a rule exists for it. A detected
# change never edits a rulepack — it raises a human-gated proposal (see build_change_proposal).
SEED_WATCHLIST: List[Dict[str, Any]] = [
    {
        "url": "https://www.meity.gov.in/documents/press-release",
        "label": "MeitY press releases",
        "jurisdiction": "DPDP_INDIA",
    },
    {
        "url": "https://egazette.gov.in/(S(dpdp))/default.aspx",
        "label": "e-Gazette (DPDP entries)",
        "jurisdiction": "DPDP_INDIA",
    },
    {
        "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "label": "EUR-Lex AI Act consolidated text",
        "jurisdiction": "EU_AI_ACT",
    },
    {
        "url": "https://digital-strategy.ec.europa.eu/en/policies/ai-office",
        "label": "European AI Office guidance index",
        "jurisdiction": "EU_AI_ACT",
    },
]

# Citation reference patterns, used to map a diff back to the rules it likely affects.
# EU: "Art. 9", "Article 50(2)"; DPDP: "s.8", "Section 9", "Rule 8(1)".
_CITATION_REF_RE = re.compile(
    r"(?:Art(?:icle|\.)?\s*\d+[a-z]?(?:\(\d+\))?"
    r"|Rule\s*\d+(?:\(\d+\))?"
    r"|(?:s(?:ection|\.)?)\s*\d+[a-z]?(?:\(\d+\))?)",
    re.IGNORECASE,
)

# A date-ish token in a diff suggests an enforcement-date change proposal.
_DATE_HINT_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
    r"|(?:enforce|enforcement|applic\w*|in force|effective|deferr\w*|postpon\w*))\b",
    re.IGNORECASE,
)

# Words hinting a brand-new obligation (→ propose a new rule stub, not just a date bump).
_NEW_OBLIGATION_RE = re.compile(
    r"\b(?:new (?:article|obligation|prohibition|requirement)"
    r"|shall (?:not )?(?:be prohibited|ensure|establish|maintain|appoint)"
    r"|is prohibited|introduc\w+|add\w+ (?:a|an) (?:new )?(?:article|obligation))\b",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Whitespace-normalize so cosmetic reflow doesn't read as a legal change.

    Collapses runs of whitespace, strips each line, drops blank lines. Content changes
    still change the hash; reformatting alone does not.
    """
    if not text:
        return ""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def collect_watch_sources(packs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Derive the de-duplicated watch list from loaded rulepacks.

    Each entry: {url, rule_ids, pack_ids} — the rules (across packs) that cite that source,
    so a detected change maps straight to the rules a human must re-verify.
    """
    by_url: Dict[str, Dict[str, Any]] = {}
    for pack in packs or []:
        pack_id = pack.get("pack_id") or pack.get("id") or "unknown"
        for rule in pack.get("rules", []) or []:
            url = rule.get("source_url")
            if not url:
                continue
            entry = by_url.setdefault(url, {"url": url, "rule_ids": set(), "pack_ids": set()})
            entry["rule_ids"].add(rule.get("id", "?"))
            entry["pack_ids"].add(pack_id)
    return [
        {"url": e["url"], "rule_ids": sorted(e["rule_ids"]), "pack_ids": sorted(e["pack_ids"])}
        for e in sorted(by_url.values(), key=lambda x: x["url"])
    ]


def detect_change(prev_hash: Optional[str], new_text: str) -> Dict[str, Any]:
    """Compare a freshly fetched source against the last stored hash.

    ``is_baseline`` marks the first time we see a source (store, don't alert).
    ``changed`` is True only when a prior hash exists and differs.
    """
    new_hash = content_hash(new_text)
    if prev_hash is None:
        return {"is_baseline": True, "changed": False, "prev_hash": None, "new_hash": new_hash}
    return {"is_baseline": False, "changed": new_hash != prev_hash, "prev_hash": prev_hash, "new_hash": new_hash}


def merge_watch_sources(
    pack_sources: List[Dict[str, Any]],
    seed: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Union pack-derived sources with the seed watchlist, keyed by URL.

    Pack-derived entries carry ``rule_ids``/``pack_ids``; seed-only entries carry a
    ``label``/``jurisdiction`` and empty rule lists (nothing cites them yet). When a URL
    appears in both, the pack entry's rule mapping is kept and the seed label is attached.
    """
    seed = SEED_WATCHLIST if seed is None else seed
    by_url: Dict[str, Dict[str, Any]] = {}
    for s in pack_sources or []:
        by_url[s["url"]] = {**s}
    for s in seed or []:
        entry = by_url.setdefault(
            s["url"], {"url": s["url"], "rule_ids": [], "pack_ids": []}
        )
        entry.setdefault("label", s.get("label"))
        entry.setdefault("jurisdiction", s.get("jurisdiction"))
        entry["seeded"] = True
    return [by_url[u] for u in sorted(by_url)]


def diff_summary(prev_text: str, new_text: str, max_lines: int = 8) -> Dict[str, Any]:
    """A lightweight, dependency-free line-level diff summary between two source snapshots.

    Returns counts of added/removed normalized lines plus a capped sample of each. Not a
    full unified diff — enough for a human reviewer to see WHAT moved without loading a
    diffing dependency into the compiled agent.
    """
    prev_lines = set(normalize_text(prev_text or "").splitlines())
    new_lines = set(normalize_text(new_text or "").splitlines())
    added = sorted(new_lines - prev_lines)
    removed = sorted(prev_lines - new_lines)
    return {
        "added_count": len(added),
        "removed_count": len(removed),
        "added_sample": added[:max_lines],
        "removed_sample": removed[:max_lines],
        "truncated": len(added) > max_lines or len(removed) > max_lines,
    }


def _normalize_citation_ref(token: str) -> str:
    """Canonicalize a citation reference token for loose matching (e.g. 'Article 9' -> 'art9')."""
    t = token.lower()
    t = re.sub(r"\b(article|art\.?)\b", "art", t)
    t = re.sub(r"\bsection|s\.?\b", "s", t)
    return re.sub(r"[^a-z0-9]", "", t)


def match_rules_by_citation(
    changed_text: str, rules: List[Dict[str, Any]]
) -> List[str]:
    """Return rule IDs whose act/rule citation shares a reference token with the changed text.

    Complements the URL-based mapping: even if the changed source is a broad index page, a
    diff that mentions "Article 50" is routed to the rules that cite Article 50.
    """
    refs = {
        _normalize_citation_ref(m.group(0))
        for m in _CITATION_REF_RE.finditer(changed_text or "")
    }
    if not refs:
        return []
    hits: List[str] = []
    for rule in rules or []:
        citation = " ".join(
            str(rule.get(k) or "") for k in ("act_citation", "rule_citation", "clause")
        )
        rule_refs = {
            _normalize_citation_ref(m.group(0))
            for m in _CITATION_REF_RE.finditer(citation)
        }
        if refs & rule_refs:
            hits.append(rule.get("id", "?"))
    return sorted(set(hits))


def propose_action(diff: Dict[str, Any]) -> str:
    """Heuristic proposed action for a detected change (review-only by default).

    Returns one of: ``date_change`` | ``new_rule_stub`` | ``review_only``. This is a triage
    hint for the human reviewer, never an instruction the system acts on.
    """
    sample = " ".join(diff.get("added_sample", []) + diff.get("removed_sample", []))
    if _NEW_OBLIGATION_RE.search(sample):
        return "new_rule_stub"
    if _DATE_HINT_RE.search(sample):
        return "date_change"
    return "review_only"


def build_change_proposal(
    source: Dict[str, Any],
    prev_text: str,
    new_text: str,
    all_rules: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a structured, human-review-ONLY change proposal for a detected source change.

    Fields: source (url/label), diff summary, affected rule IDs (URL-mapped ∪ citation-matched),
    and a proposed action hint. NEVER auto-applied — a reviewer approves it into a YAML patch
    stub under ``rulepacks/proposals/`` or rejects it.
    """
    diff = diff_summary(prev_text, new_text)
    changed_blob = " ".join(diff.get("added_sample", []) + diff.get("removed_sample", []))
    url_rule_ids = list(source.get("rule_ids") or [])
    citation_rule_ids = match_rules_by_citation(changed_blob, all_rules or [])
    affected = sorted(set(url_rule_ids) | set(citation_rule_ids))
    return {
        "source": {
            "url": source.get("url"),
            "label": source.get("label"),
            "jurisdiction": source.get("jurisdiction"),
            "pack_ids": list(source.get("pack_ids") or []),
        },
        "diff_summary": diff,
        "affected_rule_ids": affected,
        "affected_via_citation": citation_rule_ids,
        "proposed_action": propose_action(diff),
        "auto_applied": False,
        "note": (
            "Human review required. This proposal is a triage hint derived from a detected "
            "source change; it does not modify any rulepack."
        ),
    }
