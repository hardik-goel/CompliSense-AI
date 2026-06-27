"""Tier-1 connector discovery API (Phase 3.2).

Wires the read-only connectors (connectors/) to the product: a user runs discovery against
their own cloud/SCM account, reviews the resulting manifest *suggestions*, and confirms the
ones they accept into the project. Guardrails are enforced here, not just in the connectors:

  - **Credentials are never stored.** They arrive in the request body, are filtered to the
    exact accepted kwargs (no client_factory/http_get injection from the wire), used for the
    single discovery call, and discarded. Only signals + suggestions persist, and only with
    explicit ``consent_to_store``.
  - **Suggested, user confirms.** Discovery never writes to the manifest. ``/apply`` does,
    and only for the fields the user accepted.
  - **Full audit trail** of every discovery + apply.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from connectors import available_providers, get_connector
from connectors.base import ConnectorError
from connectors.mapping import signals_to_suggestions
from connectors.registry import CONNECTOR_REQUIREMENTS, CONNECTORS
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.projects import get_project_for_user, projects_collection

router = APIRouter(tags=["connectors"])

# Exact kwargs each connector accepts from the wire. Anything else is dropped so a caller
# can never inject client_factory/http_get (which would bypass real auth) or unknown args.
ALLOWED_CREDS: dict[str, set[str]] = {
    "aws": {"role_arn", "region", "external_id"},
    "gcp": {"project_id", "access_token", "region"},
    "azure": {"subscription_id", "access_token"},
    "github": {"org", "token"},
}
# Subset that must be present to even attempt discovery.
REQUIRED_CREDS: dict[str, set[str]] = {
    "aws": {"role_arn"},
    "gcp": {"project_id", "access_token"},
    "azure": {"subscription_id", "access_token"},
    "github": {"org", "token"},
}
# Placeholder args used only to render each connector's least-privilege handout.
_POLICY_PLACEHOLDERS: dict[str, dict[str, Any]] = {
    "aws": {"role_arn": "arn:aws:iam::ACCOUNT_ID:role/CompliSenseReadOnly"},
    "gcp": {"project_id": "YOUR_PROJECT_ID"},
    "azure": {"subscription_id": "YOUR_SUBSCRIPTION_ID"},
    "github": {"org": "YOUR_ORG"},
}


def discoveries_collection():
    return get_collection("connector_discoveries")


class DiscoverRequest(BaseModel):
    credentials: dict[str, Any] = Field(default_factory=dict)
    consent_to_store: bool = False


class ApplyRequest(BaseModel):
    accepted_fields: list[str] = Field(default_factory=list)


def _least_privilege(provider: str) -> dict[str, Any]:
    conn = get_connector(provider, **_POLICY_PLACEHOLDERS.get(provider, {}))
    return conn.least_privilege_policy()


@router.get("/api/v1/connectors")
async def list_connectors(current_user: dict[str, Any] = Depends(get_current_user)):
    """Catalog: providers, the inputs each needs, and the read-only access to grant."""
    return {
        "providers": [
            {
                "provider": p,
                "requirements": CONNECTOR_REQUIREMENTS.get(p, []),
                "least_privilege_policy": _least_privilege(p),
            }
            for p in available_providers()
        ]
    }


@router.post("/projects/{project_id}/connectors/{provider}/discover")
async def run_discovery(
    project_id: str,
    provider: str,
    body: DiscoverRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Run read-only discovery against the user's account; return signals + suggestions.

    Persists (signals + suggestions, never credentials) only with ``consent_to_store``.
    """
    get_project_for_user(project_id, current_user["id"])
    if provider not in CONNECTORS:
        raise HTTPException(status_code=404, detail=f"Unknown provider. Available: {available_providers()}")

    allowed = ALLOWED_CREDS.get(provider, set())
    creds = {k: v for k, v in (body.credentials or {}).items() if k in allowed}
    missing = REQUIRED_CREDS.get(provider, set()) - {k for k, v in creds.items() if v}
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required credentials: {sorted(missing)}")

    try:
        connector = get_connector(provider, **creds)
        signals = connector.discover()
    except ConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # SDK/network failure reaching the customer account
        raise HTTPException(status_code=502, detail=f"Discovery failed: {exc}") from exc
    finally:
        creds = None  # drop credentials immediately

    suggestions = signals_to_suggestions(signals)
    signal_dicts = [s.to_dict() for s in signals]
    suggestion_dicts = [s.to_dict() for s in suggestions]

    discovery_id = f"disc_{uuid.uuid4().hex[:12]}"
    now = dt.datetime.utcnow()
    stored = False
    if body.consent_to_store:
        discoveries_collection().insert_one({
            "discovery_id": discovery_id,
            "project_id": project_id,
            "user_id": current_user["id"],
            "provider": provider,
            "created_at": now,
            "signals": signal_dicts,
            "suggestions": suggestion_dicts,
            "applied_fields": [],
        })
        stored = True

    try:
        insert_audit_log({
            "user_id": current_user["id"], "project_id": project_id,
            "source": "connector_discovery", "status": "completed", "timestamp": now,
            "metadata": {"provider": provider, "signals": len(signal_dicts),
                         "suggestions": len(suggestion_dicts), "stored": stored},
        })
    except Exception:
        pass

    return {
        "discovery_id": discovery_id if stored else None,
        "provider": provider,
        "stored": stored,
        "signals": signal_dicts,
        "suggestions": suggestion_dicts,
        "disclaimer": "Read-only discovery. Suggestions are proposals — review and confirm; "
                      "nothing is applied automatically. Not legal advice.",
    }


@router.get("/projects/{project_id}/connectors/discoveries")
async def list_discoveries(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    docs = list(discoveries_collection().find({"project_id": project_id}).sort("created_at", -1))
    out = []
    for d in docs:
        clean = serialize_document(d)
        out.append({"discovery_id": clean["discovery_id"], "provider": clean["provider"],
                    "created_at": clean["created_at"], "signal_count": len(clean.get("signals", [])),
                    "suggestion_count": len(clean.get("suggestions", [])),
                    "applied_fields": clean.get("applied_fields", [])})
    return {"project_id": project_id, "count": len(out), "discoveries": out}


@router.get("/projects/{project_id}/connectors/discoveries/{discovery_id}")
async def get_discovery(project_id: str, discovery_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    doc = discoveries_collection().find_one({"discovery_id": discovery_id, "project_id": project_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return serialize_document(doc)


@router.post("/projects/{project_id}/connectors/discoveries/{discovery_id}/apply")
async def apply_suggestions(
    project_id: str,
    discovery_id: str,
    body: ApplyRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Confirm accepted suggestions into the project's discovered manifest (human-in-the-loop)."""
    get_project_for_user(project_id, current_user["id"])
    doc = discoveries_collection().find_one({"discovery_id": discovery_id, "project_id": project_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Discovery not found")

    accepted = set(body.accepted_fields or [])
    by_field = {s["manifest_field"]: s["suggested_value"] for s in doc.get("suggestions", [])}
    to_apply = {f: by_field[f] for f in accepted if f in by_field}
    if not to_apply:
        raise HTTPException(status_code=400, detail="No matching accepted suggestions to apply")

    project = projects_collection().find_one({"id": project_id})
    manifest = dict((project or {}).get("discovered_manifest") or {})
    for field, value in to_apply.items():
        existing = manifest.get(field)
        if isinstance(existing, list) and isinstance(value, list):
            manifest[field] = sorted(set(existing) | set(value))  # union for multi-valued fields
        else:
            manifest[field] = value

    now = dt.datetime.utcnow()
    projects_collection().update_one(
        {"id": project_id}, {"$set": {"discovered_manifest": manifest, "updated_at": now}})
    discoveries_collection().update_one(
        {"discovery_id": discovery_id},
        {"$set": {"applied_fields": sorted(set(doc.get("applied_fields", [])) | set(to_apply))}})

    try:
        insert_audit_log({
            "user_id": current_user["id"], "project_id": project_id,
            "source": "connector_apply", "status": "applied", "timestamp": now,
            "metadata": {"discovery_id": discovery_id, "applied_fields": sorted(to_apply)},
        })
    except Exception:
        pass

    return {"project_id": project_id, "applied": sorted(to_apply), "discovered_manifest": manifest}
