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
import logging
import re
import uuid
from typing import Any, Dict, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from compliance.legal_text import legal_footer_text
from compliance.manifest import build_manifest
from compliance.readiness import score_manifest, top_gaps
from saas.app.config import settings
from saas.app.database import get_collection
from saas.app.mail import MailMessage, get_mailer
from saas.app.readiness import _load_pack, _ALLOWED_PACKS, require_admin
from saas.app.report_email import (
    build_assessment_view,
    render_client_email,
    render_operator_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/readiness", tags=["readiness-leads"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RATE_LIMIT_MAX = 5          # max submissions
_RATE_LIMIT_WINDOW_SEC = 300  # per IP per 5 minutes
_DPDP_DEADLINE = "13 May 2027"
# Public demo booking base (same as the landing page). The client email CTA prefills the
# lead's email. Warm-inbound DIRECT_DEMO_URL stays env-only and is never used here.
_CALENDLY = "https://calendly.com/hardik-goel214/complisense-ai"


def _booking_url(email: str) -> str:
    return f"{_CALENDLY}?email={quote(email)}" if email else _CALENDLY


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
    # Render the client + operator HTML reports (Prompt 3B) from the already-scored findings.
    view = build_assessment_view(
        report, payload.answers, email,
        cta_url=_booking_url(email), submitted_at=now.isoformat(),
        unsubscribe_contact=settings.lead_privacy_contact,
    )
    client_subject, client_html = render_client_email(view)
    lead["rendered_client_html"] = client_html
    lead["findings"] = {"passes": view["passes"], "gaps": view["gaps"], "nas": view["nas"]}

    delivered = _deliver(view, client_subject, client_html, email)
    lead["email_delivery"] = delivered

    try:
        leads_collection().insert_one(lead)
    except Exception as e:
        logger.warning("Could not persist lead: %s", e)

    return {
        "ok": True,
        "delivered": delivered.get("client", False),
        "readiness_score": report.get("readiness_score"),
        "summary": report.get("summary"),
        "top_gaps": top_gaps(report, 3),
        "lead_id": lead["id"],
        "privacy_notice_url": "https://complisenseai.com/privacy",
    }


def _deliver(view: Dict[str, Any], client_subject: str, client_html: str, email: str) -> Dict[str, Any]:
    """Send client + operator emails. Non-blocking: failures are logged + recorded (for
    retry_pending_leads), never raised into the request path. Operator address is server-side
    only (never returned to the client)."""
    mailer = get_mailer()
    status = {"client": False, "operator": None}
    try:
        status["client"] = mailer.send(MailMessage(
            to=[email], subject=client_subject, html=client_html,
            text=f"Your DPDP readiness. Prepare by {_DPDP_DEADLINE}. {legal_footer_text()}",
            reply_to=settings.support_email,
        ))
    except Exception as e:
        logger.warning("Client email failed: %s", e)
    if settings.operator_notify_email:
        op_subject, op_html = render_operator_email(view)
        status["operator"] = False
        try:
            status["operator"] = mailer.send(MailMessage(
                to=[settings.operator_notify_email], subject=op_subject, html=op_html,
                text=f"Lead {email}: {view.get('score')}% — {view.get('suggested_angle')}",
            ))
        except Exception as e:
            logger.warning("Operator email failed: %s", e)
    return status


def retry_pending_leads(limit: int = 50) -> Dict[str, Any]:
    """Resend emails for leads whose delivery previously failed (never lose a lead silently).

    Re-renders the operator email from stored answers; reuses the stored client HTML. Callable
    from a cron. Best-effort; updates email_delivery on success.
    """
    retried = 0
    try:
        pending = list(leads_collection().find(
            {"$or": [{"email_delivery.client": False}, {"email_delivery.operator": False}]}
        ).limit(limit))
    except Exception:
        pending = []
    for lead in pending:
        report_like = {
            "readiness_score": lead.get("readiness_score"),
            "scoring_available": True,
            "rules_current_as_of": None,
            "ready": [{"title": p.get("title"), "rule_id": p.get("rule_id")} for p in lead.get("findings", {}).get("passes", [])],
            "gaps": lead.get("findings", {}).get("gaps", []),
            "not_applicable": [{"title": n.get("title"), "reason": n.get("why")} for n in lead.get("findings", {}).get("nas", [])],
        }
        view = build_assessment_view(
            report_like, lead.get("answers", {}), lead.get("email", ""),
            cta_url=_booking_url(lead.get("email", "")),
            submitted_at=str(lead.get("created_at", "")),
            unsubscribe_contact=settings.lead_privacy_contact,
        )
        subject, html_body = render_client_email(view)
        status = _deliver(view, subject, lead.get("rendered_client_html") or html_body, lead.get("email", ""))
        try:
            leads_collection().update_one({"id": lead.get("id")}, {"$set": {"email_delivery": status}})
        except Exception:
            pass
        retried += 1
    return {"retried": retried}


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
