"""Regulator-ready evidence export API (Phase 8).

Assembles a grounded evidence pack (compliance/evidence.py) from a project's readiness,
posture history, monitoring alerts, connector discoveries, and PII inferences, and serves it
as JSON or a downloadable HTML document. Role-gated: any team role (viewer+) may export;
non-members get a 404.
"""

from __future__ import annotations

import datetime as dt
import html
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pymongo import DESCENDING

from agent.db.mongo import insert_audit_log
from compliance.evidence import build_evidence_pack
from compliance.manifest import build_manifest
from compliance.readiness import score_manifest
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.readiness import _ALLOWED_PACKS, _load_pack
from saas.app.teams import get_project_with_role

router = APIRouter(prefix="/projects", tags=["evidence"])
_DEFAULT_PACK = "dpdp_india_core_v1"


def _runs(project_id: str):
    return list(get_collection("scan_runs").find({"project_id": project_id}).sort("created_at", DESCENDING))


def _alerts(project_id: str):
    return list(get_collection("monitor_alerts").find({"project_id": project_id}))


def _discoveries(project_id: str):
    return list(get_collection("connector_discoveries").find({"project_id": project_id}))


def _pii(project_id: str):
    return list(get_collection("pii_inferences").find({"project_id": project_id}))


def _gap_states(project_id: str):
    return list(get_collection("gap_states").find({"project_id": project_id}))


def _assemble(project: dict[str, Any], prepared_by: str | None, pack_id: str) -> dict[str, Any]:
    if pack_id not in _ALLOWED_PACKS:
        pack_id = _DEFAULT_PACK
    answers = {**(project.get("manifest_answers") or {}), **(project.get("discovered_manifest") or {})}
    pack = _load_pack(pack_id)
    report = score_manifest(build_manifest(answers), pack)
    pid = project["id"]
    return build_evidence_pack(
        project=serialize_document(project),
        readiness_report=report,
        runs=[serialize_document(r) for r in _runs(pid)],
        alerts=[serialize_document(a) for a in _alerts(pid)],
        discoveries=[serialize_document(d) for d in _discoveries(pid)],
        pii_inferences=[serialize_document(p) for p in _pii(pid)],
        generated_at=dt.datetime.utcnow().isoformat(),
        prepared_by=prepared_by,
        rulepack_id=pack_id,
        gap_states=[serialize_document(g) for g in _gap_states(pid)],
        pack_version=pack.get("pack_version") or pack.get("version"),
        rules_current_as_of=pack.get("rules_current_as_of") or pack.get("current_as_of"),
    )


@router.get("/{project_id}/evidence")
async def get_evidence(project_id: str, pack_id: str = _DEFAULT_PACK,
                       current_user: dict[str, Any] = Depends(get_current_user)):
    project, role = get_project_with_role(project_id, current_user, "export_evidence")
    _audit_export(current_user, project_id, role, pack_id, "json")
    return _assemble(project, current_user.get("email"), pack_id)


@router.get("/{project_id}/evidence/export.html")
async def export_evidence_html(project_id: str, pack_id: str = _DEFAULT_PACK,
                               current_user: dict[str, Any] = Depends(get_current_user)):
    project, role = get_project_with_role(project_id, current_user, "export_evidence")
    _audit_export(current_user, project_id, role, pack_id, "html")
    pack = _assemble(project, current_user.get("email"), pack_id)
    document = _render_html(pack)
    filename = f"evidence_{project_id}.html"
    return Response(content=document, media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _audit_export(user: dict[str, Any], project_id: str, role: str, pack_id: str, fmt: str) -> None:
    try:
        insert_audit_log({"user_id": user["id"], "project_id": project_id, "source": "evidence_export",
                          "status": "exported", "timestamp": dt.datetime.utcnow(),
                          "metadata": {"role": role, "pack_id": pack_id, "format": fmt}})
    except Exception:
        pass


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "—"))


def _render_html(pack: dict[str, Any]) -> str:
    meta = pack["meta"]
    r = pack["readiness"]
    gaps_rows = "".join(
        f"<tr><td>{_esc(g.get('title'))}</td><td><code>{_esc(g.get('rule_id'))}</code></td>"
        f"<td>{_esc(g.get('rule_citation') or g.get('act_citation'))}</td>"
        f"<td>{_esc(g.get('status'))}</td><td>{_esc(g.get('framing'))}</td></tr>"
        for g in r.get("gaps", []))
    cite_rows = "".join(
        f"<tr><td><code>{_esc(c.get('rule_id'))}</code></td><td>{_esc(c.get('act_citation'))}</td>"
        f"<td>{_esc(c.get('rule_citation'))}</td><td>{_esc(c.get('source_url'))}</td>"
        f"<td>{_esc(c.get('verification'))}</td></tr>"
        for c in pack.get("citations", []))
    hist_rows = "".join(
        f"<tr><td>{_esc(h.get('at'))}</td><td>{_esc(h.get('score'))}%</td></tr>"
        for h in pack.get("posture_history", []))
    gov = pack.get("governance", {})
    gov_rows = "".join(
        f"<tr><td><code>{_esc(a.get('rule_id'))}</code></td><td>{_esc(a.get('status'))}</td>"
        f"<td>{_esc(a.get('assignee_user_id'))}</td>"
        f"<td>{_esc(a.get('signed_off_by_email') or a.get('signed_off_by'))}</td>"
        f"<td>{_esc(a.get('signed_off_at'))}</td></tr>"
        for a in gov.get("assignments", []))
    summary = r.get("summary") or {}
    mon = pack.get("monitoring", {})
    pii = pack.get("pii_data_flow", {})
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{_esc(meta['title'])}</title>
<style>body{{font-family:-apple-system,Segoe UI,sans-serif;max-width:920px;margin:2rem auto;padding:1rem;color:#1a1a1a}}
h1{{font-size:1.5rem}} h2{{font-size:1.1rem;margin-top:1.6rem;border-bottom:1px solid #ddd;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0;font-size:.85rem}} th,td{{border:1px solid #ddd;padding:6px;text-align:left}}
th{{background:#f5f5f5}} .muted{{color:#666;font-size:.85rem}} .disc{{background:#fff8e6;border:1px solid #f0d28a;padding:10px;border-radius:6px;font-size:.85rem}}</style>
</head><body>
<h1>{_esc(meta['title'])}</h1>
<p class="muted">Project: <strong>{_esc(meta['project_name'])}</strong> ({_esc(meta['project_id'])}) ·
Standard: {_esc(meta['compliance_standard'])} · Rulepack: {_esc(meta.get('rulepack_applied'))} ·
Generated: {_esc(meta['generated_at'])} · Prepared by: {_esc(meta['prepared_by'])}</p>
<div class="disc">{_esc(pack['disclaimer'])}</div>

<h2>Readiness</h2>
<p>Score: <strong>{_esc(r.get('score'))}%</strong> — ready {_esc(summary.get('ready'))},
gaps {_esc(summary.get('gaps'))}, applicable {_esc(summary.get('applicable'))},
not applicable {_esc(summary.get('not_applicable'))}.</p>

<h2>Out of scope for your profile</h2>
{("<ul>" + "".join(f"<li><strong>{_esc(x.get('label'))}</strong> — {_esc(x.get('note'))}</li>" for x in (r.get('scope_exclusions') or [])) + "</ul>") if r.get('scope_exclusions') else '<p class="muted">No deliberate scope exclusions for this pack.</p>'}

<h2>Gaps (prepare-by readiness items)</h2>
<table><thead><tr><th>Item</th><th>Rule</th><th>Citation</th><th>Status</th><th>Framing</th></tr></thead>
<tbody>{gaps_rows or '<tr><td colspan="5">No gaps recorded.</td></tr>'}</tbody></table>

<h2>Posture over time</h2>
<table><thead><tr><th>At</th><th>Score</th></tr></thead>
<tbody>{hist_rows or '<tr><td colspan="2">No scan history.</td></tr>'}</tbody></table>
<p class="muted">Monitoring: {_esc(mon.get('scans_recorded'))} scan(s) recorded, latest
{_esc(mon.get('latest_score'))}%, {_esc(mon.get('open_alerts'))} open alert(s).</p>

<h2>PII &amp; data flow</h2>
<p>Categories: {_esc(', '.join(pii.get('categories', [])) or '—')} ·
Cross-border flagged: {_esc(pii.get('cross_border_flagged'))}.</p>

<h2>Gap governance (assignment &amp; sign-off)</h2>
<table><thead><tr><th>Rule</th><th>Status</th><th>Assignee</th><th>Signed off by</th><th>At</th></tr></thead>
<tbody>{gov_rows or '<tr><td colspan="5">No gap assignments recorded.</td></tr>'}</tbody></table>
<p class="muted">{_esc(gov.get('signed_off_count', 0))} gap(s) signed off. Sign-off is an internal
attestation that a readiness item was handled — not a determination of legal compliance.</p>

<h2>Citations &amp; sources</h2>
<table><thead><tr><th>Rule</th><th>Act citation</th><th>Rule citation</th><th>Source</th><th>Verification</th></tr></thead>
<tbody>{cite_rows or '<tr><td colspan="5">—</td></tr>'}</tbody></table>

<p class="muted">{_esc(meta.get('freshness_footer'))}</p>
<p class="muted">CompliSense-AI provides a regulatory-readiness assessment, not legal advice, and does
not create any attorney-client relationship. To the maximum extent permitted by law,
CompliSense's liability is limited as set out in our Terms; we are not liable for any
regulatory fine or penalty imposed on you.</p>
<p class="muted">Generated by CompliSense-AI. Confirmed manifest facts and discovery summaries
only — no credentials, raw artefacts, or personal-data values are included.</p>
</body></html>"""
