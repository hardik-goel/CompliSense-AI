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
