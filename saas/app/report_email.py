"""Emailed HTML readiness report — client + operator renders (Prompt 3B).

Takes a completed readiness assessment (the output of ``compliance.readiness.score_manifest``
plus the visitor's answers/email) and renders two email-client-safe HTML emails from Jinja2
templates. It does NOT recompute rules — it reuses the findings already scored.

Mapping: score_manifest returns ready[] / gaps[] (status GAP or NEEDS_REVIEW) / not_applicable[].
Here: ready -> PASS, gaps with status GAP -> GAP, gaps with status NEEDS_REVIEW -> PARTIAL,
not_applicable -> NA.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES = Path(__file__).resolve().parents[2] / "agent" / "report" / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES)),
    autoescape=select_autoescape(["html", "j2", "html.j2"]),
)

DEADLINE = "13 May 2027"

# One-line "what closing this looks like" per DPDP obligation. Falls back to a generic hint.
_CLOSE_HINTS = {
    "DPDP-SEC5-NOTICE-001": "Publish a standalone, plain-language privacy notice covering purposes, rights and grievance contact.",
    "DPDP-SEC6-CONSENT-001": "Capture explicit opt-in consent with a timestamped record and an easy withdrawal path.",
    "DPDP-SEC8-OBLIGATIONS-001": "Document your security safeguards — encryption, access control, logging.",
    "DPDP-SEC8-OBLIGATIONS-002": "Stand up a breach-response process and a breach register (Board + affected-person tracks).",
    "DPDP-SEC8-OBLIGATIONS-003": "Define retention periods and an erasure workflow per data class.",
    "DPDP-SEC13-GRIEVANCE-001": "Publish a grievance/contact point and a response SLA.",
    "DPDP-SEC8-PROCESSOR-001": "Maintain a processor inventory with data-processing agreements.",
    "DPDP-SEC11-ACCESS-001": "Document an access-request workflow with identity verification.",
    "DPDP-SEC12-CORRECTION-001": "Track correction/erasure requests to closure.",
    "DPDP-SEC16-TRANSFER-001": "Document your cross-border transfer posture and vendor assessment.",
    "DPDP-SEC14-NOMINATION-001": "Add a nomination path to your rights SOP (capture, record, activation, honour).",
    "DPDP-SEC9-GUARDIAN-001": "Document the lawful-guardian consent path for persons with disability.",
}


def _severity(item: Dict[str, Any]) -> str:
    return item.get("severity") or "Minor"


def build_assessment_view(
    report: Dict[str, Any],
    answers: Dict[str, Any],
    email: str,
    cta_url: str,
    submitted_at: str,
    unsubscribe_contact: str,
) -> Dict[str, Any]:
    """Shape a scored report into the view both email templates render from."""
    passes = [{"title": r.get("title"), "rule_id": r.get("rule_id")} for r in report.get("ready", [])]

    gaps: List[Dict[str, Any]] = []
    partial_only = True
    for g in report.get("gaps", []):
        rid = g.get("rule_id")
        status = g.get("status")  # GAP | NEEDS_REVIEW
        if status == "GAP":
            partial_only = False
        gaps.append({
            "title": g.get("title"),
            "rule_id": rid,
            "severity": _severity(g),
            "status": status,
            "citation": g.get("act_citation") or g.get("rule_citation") or "",
            "framing": g.get("framing") or "",
            "close_hint": _CLOSE_HINTS.get(rid, "Document and publish this control, then keep evidence of it."),
        })

    nas = [{"title": n.get("title"), "why": (n.get("reason") or "Not applicable to your profile.").split(". ")[0]}
           for n in report.get("not_applicable", [])]

    gap_counts = {"Critical": 0, "Major": 0, "Minor": 0}
    for g in gaps:
        gap_counts[g["severity"]] = gap_counts.get(g["severity"], 0) + 1

    # Sales-intel "suggested angle" — higher stakes first, then major-gap volume, then partials.
    children = bool(answers.get("processes_children_data") in (True, "true", "yes", "1"))
    is_sdf = bool(answers.get("notified_as_sdf") in (True, "true", "yes", "1"))
    if children or is_sdf:
        angle = "Higher-stakes (children's data / SDF) — prioritise outreach."
    elif gap_counts["Major"] + gap_counts["Critical"] >= 2:
        angle = "Strong done-with-me pilot fit."
    elif gaps and partial_only:
        angle = "Light-touch; likely self-serve, nurture."
    elif not gaps:
        angle = "Already well-prepared — nurture / referral candidate."
    else:
        angle = "Standard follow-up."

    return {
        "email": email,
        "score": report.get("readiness_score"),
        "scoring_available": report.get("scoring_available", True),
        "sector": answers.get("sector", "—"),
        "user_count": answers.get("registered_users", "—"),
        "submitted_at": submitted_at,
        "rules_current_as_of": report.get("rules_current_as_of") or "—",
        "deadline": DEADLINE,
        "cta_url": cta_url,
        "unsubscribe_contact": unsubscribe_contact,
        "passes": passes,
        "gaps": gaps,
        "nas": nas,
        "gap_counts": gap_counts,
        "suggested_angle": angle,
        "answers": answers,
    }


def render_client_email(view: Dict[str, Any]) -> Tuple[str, str]:
    """Return (subject, html) for the client-facing email."""
    score = view.get("score")
    n = len(view.get("gaps", []))
    subject = (
        f"Your DPDP readiness: {score}% — {n} gap{'s' if n != 1 else ''} to close before May 2027"
        if view.get("scoring_available") and score is not None
        else "Your DPDP readiness assessment — obligations to prepare"
    )
    body = _env.get_template("email_client.html.j2").render(**view)
    return subject, body


def render_operator_email(view: Dict[str, Any]) -> Tuple[str, str]:
    """Return (subject, html) for the operator-facing email."""
    subject = f"New lead: {view.get('email')} — {view.get('score')}% ({view['gap_counts']['Major']} Major gaps)"
    body = _env.get_template("email_operator.html.j2").render(**view)
    return subject, body
