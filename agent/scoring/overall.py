def compute_overall_compliance(artifacts_pct: float, avg_rule_confidence: float) -> float:
    return round(0.7 * artifacts_pct + 0.3 * avg_rule_confidence, 2)

def verdict_from_score(score: float) -> str:
    if score >= 85:
        return "AUDIT-READY (WITH CONDITIONS)"
    if score >= 50:
        return "PARTIALLY COMPLIANT"
    return "NOT READY FOR AUDIT"
