"""Lead capture for the public readiness tool (Prompt 3, Tasks 2 + 4).

A visitor can get an on-screen teaser score without an email. To receive the FULL report by
email they provide one — this is the capture point. On submit we:

1. Email the visitor their score + top gaps + "prepare by 13 May 2027" framing + a demo CTA.
2. Notify the operator (OPERATOR_NOTIFY_EMAIL) with the visitor's email, ALL answers, score.
3. Persist a lead (email, answers, score, consent timestamp, source) in the `leads` collection.

DPDP-for-ourselves (Task 4): because we now store personal data, the form requires explicit
(unticked-by-default) consent, records a consent timestamp, links a short privacy notice, and
exposes a deletion path. Spam controls: email validation, a honeypot field, and per-IP rate
limiting. Mail delivery is pluggable (saas/app/mail.py); tests inject a fake mailer.
"""

from __future__ import annotations

import datetime as dt
import html
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from agent.rules.loader import load_rulepack
from compliance.legal_text import legal_footer_html, legal_footer_text
from compliance.manifest import build_manifest
from compliance.readiness import score_manifest, top_gaps
from saas.app.config import settings
from saas.app.database import get_collection, serialize_document
from saas.app.mail import MailMessage, get_mailer
from saas.app.readiness import _load_pack, _ALLOWED_PACKS, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/readiness", tags=["readiness-leads"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RATE_LIMIT_MAX = 5          # max submissions
_RATE_LIMIT_WINDOW_SEC = 300  # per IP per 5 minutes
_DPDP_DEADLINE = "13 May 2027"


def leads_collection():
    return get_collection("leads")


def _valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 254 and bool(_EMAIL_RE.match(email.strip()))


def _client_ip(request: Optional[Request]) -> str:
    if request is None:
        return "unknown"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(ip: str, now: dt.datetime) -> bool:
    """Best-effort per-IP rate limit backed by the leads collection. Never fatal."""
    if ip == "unknown":
        return False
    try:
        since = now - dt.timedelta(seconds=_RATE_LIMIT_WINDOW_SEC)
        recent = leads_collection().count_documents({"ip": ip, "created_at": {"$gte": since}})
        return recent >= _RATE_LIMIT_MAX
    except Exception:
        return False


class LeadRequest(BaseModel):
    email: str
    answers: Dict[str, Any]
    pack_id: str = "dpdp_india_core_v1"
    consent: bool = False
    # Honeypot: a field real users never see/fill. Non-empty -> silently drop as bot spam.
    company_website: str = Field(default="", description="honeypot; leave empty")


def _score_email_html(email: str, report: Dict[str, Any]) -> str:
    score = report.get("readiness_score")
    scoring = report.get("scoring_available", True)
    gaps = top_gaps(report, 5)
    rows = "".join(
        f"<li style='margin-bottom:8px'><strong>{html.escape(str(g.get('title')))}</strong> "
        f"<span style='color:#6b7280'>({html.escape(str(g.get('severity')))})</span><br>"
        f"<span style='font-size:13px;color:#374151'>"
        f"{html.escape(str(g.get('act_citation') or g.get('rule_citation') or ''))} — "
        f"{html.escape(str(g.get('framing') or ''))}</span></li>"
        for g in gaps
    ) or "<li>No gaps detected in the answers you provided.</li>"
    headline = (
        f"Your readiness score: <strong>{score}%</strong>" if scoring and score is not None
        else "Your applicable obligations are ready to review"
    )
    demo = ""
    if settings.direct_demo_url or True:  # CTA always shown; link resolved by the app/booking
        demo = (
            "<p style='margin-top:20px'><a href='https://complisenseai.com/readiness' "
            "style='background:#4f46e5;color:#fff;padding:10px 18px;border-radius:8px;"
            "text-decoration:none;display:inline-block'>Book a demo — we'll walk your specific gaps</a></p>"
        )
    return (
        f"<div style='font-family:-apple-system,Segoe UI,sans-serif;max-width:640px;margin:0 auto;color:#111'>"
        f"<h2>{headline}</h2>"
        f"<p style='color:#374151'>Prepared for {html.escape(email)}. DPDP operational obligations "
        f"become enforceable ~<strong>{_DPDP_DEADLINE}</strong> — the items below are 'prepare by' "
        f"readiness gaps, not present-day violations.</p>"
        f"<h3>Top gaps to prepare</h3><ul>{rows}</ul>"
        f"{demo}"
        f"{legal_footer_html()}"
        f"</div>"
    )


def _operator_email_html(email: str, report: Dict[str, Any], answers: Dict[str, Any], ip: str) -> str:
    ans = "".join(
        f"<tr><td style='padding:2px 8px;color:#6b7280'>{html.escape(str(k))}</td>"
        f"<td style='padding:2px 8px'>{html.escape(str(v))}</td></tr>"
        for k, v in answers.items()
    )
    return (
        f"<div style='font-family:-apple-system,Segoe UI,sans-serif'>"
        f"<h2>New readiness lead</h2>"
        f"<p><strong>Email:</strong> {html.escape(email)}<br>"
        f"<strong>Score:</strong> {report.get('readiness_score')}% · "
        f"<strong>Pack:</strong> {html.escape(str(report.get('pack_id')))}<br>"
        f"<strong>Gaps:</strong> {report.get('summary', {}).get('gaps')} · "
        f"<strong>IP:</strong> {html.escape(ip)}</p>"
        f"<h3>All answers</h3><table style='border-collapse:collapse'>{ans}</table>"
        f"</div>"
    )


@router.post("/lead")
async def capture_lead(payload: LeadRequest, request: Request = None):
    """Capture a lead: validate + consent + rate-limit, score, persist, and dual-deliver email."""
    now = dt.datetime.utcnow()

    # Honeypot: pretend success so bots don't learn they were caught. Nothing stored/sent.
    if payload.company_website.strip():
        return {"ok": True, "delivered": False}

    if payload.pack_id not in _ALLOWED_PACKS:
        raise HTTPException(status_code=400, detail=f"Unsupported pack_id: {payload.pack_id}")
    if not _valid_email(payload.email):
        raise HTTPException(status_code=400, detail="A valid email is required to receive the report.")
    # DPDP-for-ourselves: explicit consent is mandatory before we store/contact.
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Consent is required to email your score and contact you.")

    ip = _client_ip(request)
    if _rate_limited(ip, now):
        raise HTTPException(status_code=429, detail="Too many submissions. Please try again shortly.")

    manifest = build_manifest(payload.answers)
    report = score_manifest(manifest, _load_pack(payload.pack_id))

    email = payload.email.strip().lower()
    lead = {
        "id": str(uuid.uuid4()),
        "email": email,
        "answers": payload.answers,
        "pack_id": payload.pack_id,
        "readiness_score": report.get("readiness_score"),
        "summary": report.get("summary"),
        "consent": True,
        "consent_text": "I agree CompliSense may email my readiness score and contact me about a demo.",
        "consent_at": now,          # DPDP: consent timestamp stored with the record
        "source": "readiness_tool",
        "ip": ip,
        "created_at": now,
    }
    try:
        leads_collection().insert_one(lead)
    except Exception as e:
        logger.warning("Could not persist lead: %s", e)

    mailer = get_mailer()
    delivered = False
    try:
        delivered = mailer.send(MailMessage(
            to=[email],
            subject="Your CompliSense DPDP readiness score",
            html=_score_email_html(email, report),
            text=f"Your readiness score: {report.get('readiness_score')}%. "
                 f"Prepare by {_DPDP_DEADLINE}. {legal_footer_text()}",
            reply_to=settings.support_email,
        ))
    except Exception as e:
        logger.warning("Visitor email failed: %s", e)

    # Operator notification (every lead + their full situation).
    if settings.operator_notify_email:
        try:
            mailer.send(MailMessage(
                to=[settings.operator_notify_email],
                subject=f"New readiness lead: {email} ({report.get('readiness_score')}%)",
                html=_operator_email_html(email, report, payload.answers, ip),
                text=f"Lead {email} scored {report.get('readiness_score')}%.",
            ))
        except Exception as e:
            logger.warning("Operator notify failed: %s", e)

    return {
        "ok": True,
        "delivered": delivered,
        "readiness_score": report.get("readiness_score"),
        "summary": report.get("summary"),
        "top_gaps": top_gaps(report, 3),
        "lead_id": lead["id"],
        "privacy_notice_url": "https://complisenseai.com/privacy",
    }


@router.delete("/lead")
async def delete_lead(
    email: str,
    x_admin_api_token: Optional[str] = Header(default=None, alias="X-Admin-Api-Token"),
    _admin: bool = Depends(require_admin),
):
    """Documented deletion path (DPDP erasure): remove all lead records for an email (admin).

    A Data Principal who asks for erasure emails LEAD_PRIVACY_CONTACT; the operator runs this.
    """
    result = leads_collection().delete_many({"email": email.strip().lower()})
    return {"deleted": getattr(result, "deleted_count", 0), "email": email.strip().lower()}
