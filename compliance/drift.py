"""Scan-to-scan drift detection for continuous monitoring (Phase 2).

Pure, side-effect-free logic. Given two scan results (or their compact rule-state
snapshots), compute what changed: which rules regressed, which improved, which
were resolved, and the change in posture score.

Design notes
------------
- **Readiness framing, never compliance.** A "regression" means a rule moved from a
  more-ready state to a less-ready state since the previous scan. It is not a legal
  determination — it is a drift signal for the operator.
- **NOT_APPLICABLE is not a failure.** Applicability can flip between scans (e.g. the
  manifest profile changed). Those transitions are tracked separately, never counted
  as regressions or improvements.
- **MISSING and FAIL are both "failing".** Per scanner semantics, MISSING means the
  required artefact/field was absent; for drift purposes both are unmet.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Readiness rank: higher = more ready. NOT_APPLICABLE has no rank (excluded from
# regression/improvement math and handled via the applicability-transition buckets).
_RANK: Dict[str, int] = {
    "FAIL": 0,
    "MISSING": 0,
    "PARTIAL": 1,
    "PASS": 2,
}

_FAILING = {"FAIL", "MISSING"}
_PASSING = {"PASS"}


def rule_states_from_findings(findings_json: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract a compact, storable per-rule snapshot from a full findings payload.

    Keeps only what drift + timeline need (rule_id, status, title, severity) — never raw
    artefact text — so monitoring history stays small and free of uploaded content.
    """
    if not isinstance(findings_json, dict):
        return []
    results = findings_json.get("results")
    if not isinstance(results, list):
        return []
    states: List[Dict[str, Any]] = []
    for idx, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        states.append(
            {
                "rule_id": item.get("rule_id") or item.get("id") or f"rule_{idx}",
                "status": (item.get("status") or "UNKNOWN").upper(),
                "title": item.get("title", "Untitled rule"),
                "severity": item.get("severity", "unknown"),
            }
        )
    return states


def posture_score(summary: Optional[Dict[str, Any]]) -> Optional[float]:
    """Readiness posture as a 0-100 percentage over *applicable* rules.

    passed = ready, partial = half-ready, failed = gap. NOT_APPLICABLE excluded.
    Returns None when there are no applicable rules to score (avoids a fake 0/100).
    Mirrors the manifest readiness formula (compliance/readiness.py) for consistency.
    """
    if not isinstance(summary, dict):
        return None
    passed = summary.get("passed", 0) or 0
    partial = summary.get("partial", 0) or 0
    failed = summary.get("failed", 0) or 0
    scored = passed + partial + failed
    if scored <= 0:
        return None
    return round(100 * (passed + 0.5 * partial) / scored, 1)


def _index_states(states: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for state in states or []:
        rule_id = state.get("rule_id")
        if rule_id is None:
            continue
        indexed[str(rule_id)] = state
    return indexed


def _classify(prev_status: Optional[str], curr_status: Optional[str]) -> str:
    """Classify a single rule's movement between two scans.

    Returns one of: regressed, improved, unchanged, became_not_applicable,
    became_applicable, added, removed.
    """
    prev_na = prev_status == "NOT_APPLICABLE"
    curr_na = curr_status == "NOT_APPLICABLE"

    if prev_status is None:
        return "added"
    if curr_status is None:
        return "removed"
    if prev_na and curr_na:
        return "unchanged"
    if not prev_na and curr_na:
        return "became_not_applicable"
    if prev_na and not curr_na:
        return "became_applicable"

    prev_rank = _RANK.get(prev_status)
    curr_rank = _RANK.get(curr_status)
    if prev_rank is None or curr_rank is None:
        return "unchanged" if prev_status == curr_status else "changed"
    if curr_rank < prev_rank:
        return "regressed"
    if curr_rank > prev_rank:
        return "improved"
    return "unchanged"


def compute_drift(
    prev_states: List[Dict[str, Any]],
    curr_states: List[Dict[str, Any]],
    prev_score: Optional[float] = None,
    curr_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Diff two scan snapshots.

    Args:
        prev_states / curr_states: lists of {rule_id, status, title, severity}
            (use ``rule_states_from_findings`` to build these).
        prev_score / curr_score: optional precomputed posture scores for the delta.

    Returns a dict with categorized rule-change lists, counts, and a score delta.
    Each change entry carries rule_id/title/severity + from/to statuses so callers
    can render it without re-fetching the source scans.
    """
    prev_idx = _index_states(prev_states)
    curr_idx = _index_states(curr_states)
    all_ids = sorted(set(prev_idx) | set(curr_idx))

    buckets: Dict[str, List[Dict[str, Any]]] = {
        "regressions": [],
        "improvements": [],
        "added": [],
        "removed": [],
        "became_not_applicable": [],
        "became_applicable": [],
        "unchanged": [],
    }

    for rule_id in all_ids:
        prev = prev_idx.get(rule_id)
        curr = curr_idx.get(rule_id)
        prev_status = prev.get("status") if prev else None
        curr_status = curr.get("status") if curr else None
        movement = _classify(prev_status, curr_status)

        # Source of truth for title/severity is whichever side has the rule (curr wins).
        meta = curr or prev or {}
        entry = {
            "rule_id": rule_id,
            "title": meta.get("title", "Untitled rule"),
            "severity": meta.get("severity", "unknown"),
            "from": prev_status,
            "to": curr_status,
        }

        if movement == "regressed":
            buckets["regressions"].append(entry)
        elif movement == "improved":
            buckets["improvements"].append(entry)
        elif movement in ("added", "removed", "became_not_applicable", "became_applicable"):
            buckets[movement].append(entry)
        else:  # unchanged / changed (non-ranked equal)
            buckets["unchanged"].append(entry)

    score_delta: Optional[float] = None
    if prev_score is not None and curr_score is not None:
        score_delta = round(curr_score - prev_score, 1)

    counts = {key: len(val) for key, val in buckets.items()}
    has_regression = counts["regressions"] > 0

    return {
        "prev_score": prev_score,
        "curr_score": curr_score,
        "score_delta": score_delta,
        "has_regression": has_regression,
        "counts": counts,
        **buckets,
    }
