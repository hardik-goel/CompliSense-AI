def build_trends(runs):
    """
    Builds trend data for dashboard:
    - compliance percentage
    - average numeric risk score over time
    """

    RISK_SCORE = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4
    }

    trend = {
        "runs": [],
        "compliance_pct": [],
        "avg_risk": [],
        "risk_direction": "INSUFFICIENT_DATA"
    }

    for run in runs:
        results = run["results"]   # ✅ FIXED
        total = len(results)

        if total == 0:
            continue

        passed = sum(1 for r in results if r["status"] == "PASS")

        avg_risk = sum(
            RISK_SCORE.get(r.get("risk"), 1)
            for r in results
        ) / total

        trend["runs"].append(run["run_id"])
        trend["compliance_pct"].append(round((passed / total) * 100, 1))
        trend["avg_risk"].append(round(avg_risk, 2))

    if len(trend["avg_risk"]) >= 3:
        delta = trend["avg_risk"][-1] - trend["avg_risk"][-3]
        if delta > 0.2:
            trend["risk_direction"] = "INCREASING"
        elif delta < -0.2:
            trend["risk_direction"] = "DECREASING"
        else:
            trend["risk_direction"] = "STABLE"

    return trend
