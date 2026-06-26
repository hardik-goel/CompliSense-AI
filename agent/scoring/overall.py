def compute_overall_compliance(artifacts_pct: float, avg_rule_confidence: float) -> float:
    return round(0.7 * artifacts_pct + 0.3 * avg_rule_confidence, 2)


def verdict_from_score(score: float) -> str:
    """Return a READINESS verdict, never a compliance determination.

    A passing scan must never read as "you are legally compliant" — compliance is a legal
    conclusion this tool does not make. Language is readiness/gap-based on purpose
    (audit finding H1 / liability scaffolding).
    """
    if score >= 85:
        return "AUDIT-READY (WITH CONDITIONS)"
    if score >= 50:
        return "PARTIALLY READY — GAPS IDENTIFIED"
    return "NOT READY — SIGNIFICANT GAPS"


def readiness_framing(enforcement_date: str | None, date_status: str | None) -> str:
    """One-line honest framing for a finding given its enforcement metadata.

    Keeps "obligation exists" separate from "enforceable now": a not-yet-enforceable unmet
    obligation is a "prepare by" item, never a present violation (audit finding M8).
    """
    if not enforcement_date:
        if date_status == "in_force":
            return "Enforceable now."
        return "Enforcement date not set."
    if date_status == "provisional_pending_amendment":
        return f"Prepare by ~{enforcement_date} (PROVISIONAL — date may move)."
    return f"Prepare by {enforcement_date} — not a present-day violation."
