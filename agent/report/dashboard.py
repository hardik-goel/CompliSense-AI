from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def render_dashboard(
    findings: dict,
    out_dir: Path,
    heatmap: dict,
    comparison: dict = None,
    trends: dict = None
) -> Path:
    """
    Renders the HTML compliance dashboard with executive summary,
    trends, heatmap, and detailed findings.
    """

    # -----------------------------
    # Executive summary calculations
    # -----------------------------
    severity_weight = {
        "Critical": 3,
        "Major": 2,
        "Minor": 1
    }

    total_weight = 0
    failed_weight = 0
    partial_weight = 0
    critical_failures = 0

    for r in findings["results"]:
        w = severity_weight.get(r.get("severity"), 1)
        total_weight += w

        if r["status"] == "FAIL":
            failed_weight += w
            if r.get("severity") == "Critical":
                critical_failures += 1
        elif r["status"] == "PARTIAL":
            # Partial gets half penalty
            partial_weight += w * 0.5

    # Calculate compliance score: full penalty for FAIL, half penalty for PARTIAL
    total_penalty = failed_weight + partial_weight
    compliance_score = (
        round(100 - (total_penalty / total_weight * 100), 1)
        if total_weight > 0
        else 100.0
    )

    # -----------------------------
    # Compliance badge (R / Y / G)
    # -----------------------------
    if compliance_score >= 85:
        badge = "GREEN"
    elif compliance_score >= 60:
        badge = "YELLOW"
    else:
        badge = "RED"

    # -----------------------------
    # Auto-generated executive narrative
    # -----------------------------
    if badge == "GREEN":
        narrative = (
            "The system demonstrates strong alignment with the selected regulatory pack. "
            "Only minor gaps were identified, with no critical systemic risks."
        )
    elif badge == "YELLOW":
        narrative = (
            "The system shows partial alignment with the selected regulatory pack. "
            "Several material gaps require remediation, though no immediate "
            "high-risk violations were detected."
        )
    else:
        narrative = (
            "The system does not meet the selected regulatory pack expectations. "
            "Critical governance or documentation failures were detected "
            "and require immediate remediation."
        )

    exec_summary = {
        "compliance_score": compliance_score,
        "critical_failures": critical_failures,
        "badge": badge,
        "narrative": narrative
    }

    SEVERITY_ORDER = {"Critical": 3, "Major": 2, "Minor": 1}

    # Include both FAIL and PARTIAL for remediation recommendations
    failed_rules = [
        r for r in findings["results"]
        if r["status"] in ("FAIL", "PARTIAL")
    ]

    failed_rules.sort(
        key=lambda r: (
            SEVERITY_ORDER.get(r.get("severity"), 1),
            -r.get("confidence", 0)
        ),
        reverse=True
    )

    top_remediations = []
    for r in failed_rules[:3]:
        if r.get("remediation"):
            top_remediations.append({
                "rule_id": r["rule_id"],
                "action": r["remediation"][0]
            })

    exec_summary["top_remediations"] = top_remediations

    # -----------------------------
    # Render dashboard
    # -----------------------------
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates")
    )
    tpl = env.get_template("dashboard.html.j2")

    html = tpl.render(
        results=findings["results"],
        summary=findings["summary"],
        heatmap=heatmap,
        comparison=comparison,
        trends=trends,
        exec=exec_summary
    )

    out_path = out_dir / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
