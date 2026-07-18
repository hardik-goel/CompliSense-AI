#!/usr/bin/env python3
"""Regenerate LEGAL_REVIEW_NEEDED.md from rulepacks/*.yaml.

The checklist is a living professional-review artefact: one row per rule across every
REGISTERED rulepack (see compliance/registry.py), flagged by verification/date status so a
reviewer can triage. It NEVER changes rule content — it only mirrors it. Regenerate after any
rulepack change:

    3.11_venv/bin/python scripts/gen_legal_review.py

Deterministic (no timestamps) so the output is diff-friendly in git.
"""

from __future__ import annotations

from pathlib import Path

from agent.rules.loader import load_rulepack
from compliance.registry import get_rulepack_ids

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "LEGAL_REVIEW_NEEDED.md"
AS_OF = "2026-07-18"

INTRO = f"""# LEGAL_REVIEW_NEEDED.md — living professional-review checklist

> **Status: Rule content pending professional legal review as of {AS_OF}.**
> CompliSense rulepacks are compliance-readiness engineering artefacts, NOT legal
> advice and NOT a legal determination of compliance. Every rule below must be
> reviewed by (a) a qualified Indian data-protection practitioner (DPDP) and
> (b) an EU AI Act specialist before any unqualified public compliance claim.
>
> This file is GENERATED from `rulepacks/*.yaml` by `scripts/gen_legal_review.py`.
> Regenerate after any pack change; do not edit by hand. When a reviewer signs off a
> pack, set its `legal_review_status: reviewed`, `reviewer`, and `reviewed_on` in the
> pack header and tick the rows here.

## Priority flags
- ⚠️ **secondary_source_only** / **interpretation_uncertain** = NOT yet verified
  against primary statute text. Highest review priority.
- 🕒 **provisional_pending_amendment** = enforcement date may move. As of {AS_OF} the
  Digital Omnibus on AI is FINAL, so EU high-risk dates are now `phased_confirmed`.
"""

APPENDIX = """

---

## Reviewer notes — history (pending counsel)

- **EU AI Act readiness scoring is role-gated and self-attested.** EU rules remain
  `secondary_source_only` pending primary-text verification; the score is gated by the EU
  disclaimer ("PENDING professional legal review").
- **Open-source exemption mechanism** (`applicability.open_source_exempt` + manifest
  `is_open_source`): WHICH EU rules carry the carve-out is not yet mapped — counsel decides.
- **`DPDP-SEC8-RETENTION-CLASS-001`** (Rule 8(1) Third-Schedule 3-year inactivity erasure,
  gated `third_schedule_class_only`): verify erasure-period framing against primary text.

## Digital Omnibus update (2026-07-18, v2 packs) — HIGHEST priority for counsel

- **Confirmed EU high-risk dates.** The Digital Omnibus on AI is treated as FINAL (EP
  16 Jun 2026, Council 29 Jun 2026, in force Jul 2026). Annex III stand-alone high-risk
  moved from `provisional_pending_amendment` to `phased_confirmed` at 2027-12-02; Annex I
  embedded high-risk documented at 2028-08-02. **These dates are SECONDARY-SOURCED — verify
  against the consolidated OJ text before any public claim.**
- **New Art. 5 prohibition `EUAI-ART5-PROHIBITED-002`** (AI-generated NCII/CSAM,
  "nudifiers", 2026-12-02) and **`EUAI-ART50-LEGACY-MARKING-001`** (Art. 50(2) legacy
  machine-readable marking, 2026-12-02): both `secondary_source_only`, `interpretation_uncertain`.
- **New deployer/authrep/FRIA/incident rules** (`EUAI-ART26/27/22/73`): confirm scope,
  FRIA trigger conditions (Art. 27), and the non-EU authorised-representative gate (Art. 22).
- **Citation corrections (v2 only):** QMS retagged Art. 16 → **Art. 17**; data governance
  retagged Art. 18 → **Art. 10**; record-keeping/logging retagged Art. 20 → **Art. 12/19**.
  Confirm the corrected articles against the consolidated text.
- **New DPDP rules** `DPDP-SEC14-NOMINATION-001` (Act s.14) and `DPDP-SEC9-GUARDIAN-001`
  (s.9 proviso, persons with disability): verify against the Act + DPDP Rules 2025.
"""


def _flags(rule: dict) -> str:
    verification = rule.get("verification") or ""
    date_status = rule.get("date_status") or ""
    marks = []
    if verification in ("secondary_source_only", "interpretation_uncertain"):
        marks.append("⚠️")
    if rule.get("interpretation_uncertain") and "⚠️" not in marks:
        marks.append("⚠️")
    if date_status == "provisional_pending_amendment":
        marks.append("🕒")
    return " ".join(marks)


def _row(rule: dict) -> str:
    act = rule.get("act_citation") or "—"
    rulec = rule.get("rule_citation") or "—"
    # Keep the table on one line: collapse any newlines from folded YAML.
    act = " ".join(str(act).split())
    rulec = " ".join(str(rulec).split())
    verification = rule.get("verification") or "—"
    flags = _flags(rule)
    verif_cell = f"{verification} {flags}".strip()
    return (
        f"| [ ] | {rule.get('id')} | {act} | {rulec} | "
        f"{rule.get('status')} | {rule.get('enforcement_date')} | "
        f"{rule.get('date_status')} | {verif_cell} |"
    )


def build() -> str:
    parts = [INTRO]
    for pack_id in get_rulepack_ids():
        path = REPO_ROOT / "rulepacks" / f"{pack_id}.yaml"
        if not path.exists():
            continue
        pack = load_rulepack(path, validate=False)
        lrs = pack.get("legal_review_status", "pending")
        parts.append(f"\n## {pack_id}.yaml  (`legal_review_status: {lrs}`)\n")
        parts.append("| ✓ | Rule ID | Act citation | Rule citation | Status | Enforce | date_status | Verification |")
        parts.append("|---|---------|--------------|---------------|--------|---------|-------------|--------------|")
        for rule in pack.get("rules", []) or []:
            parts.append(_row(rule))
    parts.append(APPENDIX)
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")
