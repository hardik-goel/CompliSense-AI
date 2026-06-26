"""
First-party funnel analytics (Phase 1.6).

Real funnel data WITHOUT a third-party tracker — consistent with the privacy promise. We
record minimal, non-PII events server-side (event name, timestamp, a few safe properties)
into a Mongo collection. No raw questionnaire answers, no IP, no email. Best-effort: a
storage hiccup never breaks the user-facing request.

Funnel of interest: readiness_completed → signup → (later) first_scan.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional

from saas.app.database import get_collection

logger = logging.getLogger(__name__)

# Properties we will never store, even if passed in, to keep events PII-free.
_BLOCKED_PROPS = {"email", "answers", "name", "ip", "grievance_email", "password"}


def events_collection():
    return get_collection("analytics_events")


def score_bucket(score: int) -> str:
    if score >= 85:
        return "85-100"
    if score >= 50:
        return "50-84"
    if score >= 25:
        return "25-49"
    return "0-24"


def record_event(event: str, props: Optional[Dict[str, Any]] = None) -> None:
    """Record a non-PII funnel event. Best-effort; swallows storage errors."""
    safe = {k: v for k, v in (props or {}).items() if k not in _BLOCKED_PROPS}
    try:
        events_collection().insert_one({
            "event": event,
            "ts": dt.datetime.utcnow(),
            "props": safe,
        })
    except Exception as e:  # pragma: no cover - never break the request path
        logger.warning("analytics record_event(%s) failed: %s", event, e)


def funnel_summary() -> Dict[str, Any]:
    """Aggregate counts per event (admin view)."""
    try:
        pipeline = [{"$group": {"_id": "$event", "count": {"$sum": 1}}}]
        rows = list(events_collection().aggregate(pipeline))
        return {row["_id"]: row["count"] for row in rows}
    except Exception as e:
        logger.warning("analytics funnel_summary failed: %s", e)
        return {}
