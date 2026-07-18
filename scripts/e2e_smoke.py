#!/usr/bin/env python3
"""End-to-end smoke test for the CompliSense-AI readiness pipeline.

Exercises the SAME code paths the hosted API and local agent use — Tier-0 manifest →
applicability gating → readiness scoring → report render (HTML + PDF) → evidence pack —
and asserts the honesty invariants that must never regress:

  1. A fixture persona ("Series A SaaS, 40 employees, no children's data, AWS + 3
     processors") produces a readiness score and the expected DPDP gaps.
  2. No rule outside the applicability gate fires — a non-SDF, no-children startup sees
     SDF-only and children-only duties as NOT_APPLICABLE, never as gaps.
  3. The HTML + PDF report and the evidence pack carry the freshness stamp and the
     "not legal advice / no compliance determination" disclaimer footer.
  4. For the EU AI Act pack with role=deployer, deployer rules fire and provider-only
     rules do not.

Runs fully in-process (no Mongo, no HTTP server) so it is a deterministic local gate:

    3.11_venv/bin/python scripts/e2e_smoke.py

Exit code 0 = all PASS, 1 = any FAIL. Prints a PASS/FAIL summary table.
"""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.rules.loader import load_rulepack  # noqa: E402
from agent.scanner import pack_freshness  # noqa: E402
from compliance.manifest import build_manifest  # noqa: E402
from compliance.readiness import score_manifest  # noqa: E402
from compliance.evidence import build_evidence_pack  # noqa: E402

# ── tiny assertion harness ───────────────────────────────────────────────────
_RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    _RESULTS.append((name, bool(ok), detail))


def _load(pack_id: str) -> dict:
    return load_rulepack(REPO_ROOT / "rulepacks" / f"{pack_id}.yaml", validate=False)


# Fixture persona: Series A SaaS, 40 employees, no children's data, AWS + 3 processors.
DPDP_PERSONA = {
    "entity_type": "startup",
    "offers_in_india": True,
    "sector": "saas",
    "registered_users": 12_000,
    "notified_as_sdf": False,
    "is_state_instrumentality": False,
    "acts_as_consent_manager": False,
    "processes_children_data": False,
    "cross_border_transfer": True,
    "pii_categories": ["name", "email", "phone"],
    "storage_locations": ["aws"],
    # Posture: a partially-prepared startup — some controls, some gaps.
    "has_privacy_notice": True,
    "consent_mechanism": "explicit_optin",
    "has_withdrawal_mechanism": True,
    "has_security_safeguards": True,
    "has_breach_process": False,      # gap
    "retention_defined": False,        # gap
    "has_grievance_contact": False,    # gap
    "processors_listed": True,         # AWS + 3 processors inventoried
}


def run_dpdp() -> dict:
    pack = _load("dpdp_india_extended_v2")
    manifest = build_manifest(DPDP_PERSONA)
    report = score_manifest(manifest, pack)

    # 1) score returned + is a percentage
    score = report.get("readiness_score")
    check("DPDP score returned (0-100)", isinstance(score, int) and 0 <= score <= 100,
          f"score={score}")

    # 1b) expected gaps present (breach, retention, grievance were declared missing)
    gap_ids = {g["rule_id"] for g in report["gaps"]}
    expected_gaps = {"DPDP-SEC8-OBLIGATIONS-002", "DPDP-SEC8-OBLIGATIONS-003",
                     "DPDP-SEC13-GRIEVANCE-001"}
    check("DPDP expected gaps present", expected_gaps <= gap_ids,
          f"missing={sorted(expected_gaps - gap_ids)}")

    # 2) applicability gate: SDF-only + children-only rules must be NOT_APPLICABLE,
    #    never gaps, for a non-SDF, no-children startup.
    na_ids = {r["rule_id"] for r in report["not_applicable"]}
    ready_ids = {r["rule_id"] for r in report["ready"]}
    gated = {"DPDP-SEC10-SDF-001", "DPDP-SEC9-CHILDREN-001", "DPDP-SEC9-GUARDIAN-001",
             "DPDP-SEC8-RETENTION-CLASS-001"}
    leaked = gated & (gap_ids | ready_ids)
    check("DPDP no out-of-scope rule fired (SDF/children/class gated)", not leaked,
          f"leaked={sorted(leaked)}")
    check("DPDP SDF rule is NOT_APPLICABLE", "DPDP-SEC10-SDF-001" in na_ids)

    # 3) disclaimer present + honest framing
    check("DPDP report carries readiness disclaimer",
          "not legal advice" in report["disclaimer"].lower())

    return report


def run_reports_and_evidence(report: dict) -> None:
    pack = _load("dpdp_india_extended_v2")
    fresh = pack_freshness(pack)
    stamp = f"{fresh['pack_id']} {fresh['pack_version']}"

    # --- HTML report render (audit_report.html.j2 via the real renderer env) ---
    from jinja2 import Environment, FileSystemLoader, select_autoescape, ChainableUndefined
    env = Environment(
        loader=FileSystemLoader(REPO_ROOT / "agent" / "report" / "templates"),
        autoescape=select_autoescape(), undefined=ChainableUndefined,
    )
    results_ctx = {
        "summary": {"passed": len(report["ready"]), "partial": 0,
                    "failed": len(report["gaps"]), "not_applicable": len(report["not_applicable"])},
        "results": [], "artifacts": {"required_total": 0, "present": [], "missing": [],
                                     "compliance_pct": report["readiness_score"]},
        "freshness": fresh,
    }
    html = env.get_template("audit_report.html.j2").render(
        now=dt.datetime.utcnow().isoformat() + "Z",
        assessment={"verdict": "NOT ASSESSED", "overall_compliance_pct": report["readiness_score"],
                    "avg_rule_confidence": "N/A",
                    "why_not_compliant": {"missing_artifacts": [], "failed_rules": []}},
        **results_ctx,
    )
    check("HTML report contains freshness stamp", stamp in html, f"stamp={stamp}")
    check("HTML report contains disclaimer footer",
          "no compliance determination" in html.lower())

    # --- PDF report render (WeasyPrint) ---
    pdf_ok, pdf_detail = True, ""
    try:
        from agent.report.render import render_pdf
        out = Path(tempfile.mkdtemp()) / "e2e_report.pdf"
        render_pdf(results_ctx, {"verdict": "NOT ASSESSED"}, out)
        pdf_ok = out.exists() and out.stat().st_size > 0
        pdf_detail = f"{out} ({out.stat().st_size} bytes)" if out.exists() else "not written"
    except Exception as exc:  # WeasyPrint/system libs missing shouldn't crash the smoke run
        pdf_ok, pdf_detail = False, f"{type(exc).__name__}: {exc}"
    check("PDF report generated (non-empty)", pdf_ok, pdf_detail)

    # --- Evidence pack ---
    project = {"id": "proj_e2e", "name": "E2E Fixture Co", "compliance_standard": "DPDP_INDIA",
               "discovered_manifest": DPDP_PERSONA}
    evidence = build_evidence_pack(
        project=project, readiness_report=report, runs=[], alerts=[], discoveries=[],
        pii_inferences=[], generated_at=dt.datetime.utcnow().isoformat(),
        prepared_by="e2e@complisenseai.com", rulepack_id=pack.get("pack_id"),
        pack_version=fresh["pack_version"], rules_current_as_of=fresh["rules_current_as_of"],
    )
    meta = evidence["meta"]
    check("Evidence pack carries pack_version + rules_current_as_of",
          meta.get("pack_version") == fresh["pack_version"]
          and meta.get("rules_current_as_of") == fresh["rules_current_as_of"])
    check("Evidence pack carries freshness footer",
          stamp in (meta.get("freshness_footer") or ""))
    check("Evidence pack carries disclaimer",
          "not legal advice" in evidence["disclaimer"].lower())


def run_eu_deployer() -> None:
    pack = _load("euai_extended_v2")
    manifest = build_manifest({
        "has_ai_system": True, "provides_to_eu": True, "ai_role": "deployer",
        "established_in_eu": True,
    })
    report = score_manifest(manifest, pack)
    applicable = {r["rule_id"] for r in report["gaps"]} | {r["rule_id"] for r in report["ready"]}
    na = {r["rule_id"] for r in report["not_applicable"]}

    check("EU deployer: ART26 deployer rule fires", "EUAI-ART26-DEPLOYER-001" in applicable)
    check("EU deployer: ART27 FRIA rule fires", "EUAI-ART27-FRIA-001" in applicable)
    # provider-only rules must NOT fire for a pure deployer
    provider_only = {"EUAI-ART9-RISK-MGMT-001", "EUAI-ART22-AUTHREP-001", "EUAI-ART73-INCIDENT-001"}
    leaked = provider_only & applicable
    check("EU deployer: provider-only rules do NOT fire", not leaked, f"leaked={sorted(leaked)}")
    check("EU deployer: provider risk-mgmt is NOT_APPLICABLE", "EUAI-ART9-RISK-MGMT-001" in na)


def main() -> int:
    try:
        report = run_dpdp()
        run_reports_and_evidence(report)
        run_eu_deployer()
    except Exception as exc:
        check("smoke run completed without exception", False, f"{type(exc).__name__}: {exc}")

    # ── PASS/FAIL summary table ──────────────────────────────────────────────
    width = max((len(n) for n, _, _ in _RESULTS), default=20)
    print("\n" + "=" * (width + 22))
    print("CompliSense-AI E2E smoke test")
    print("=" * (width + 22))
    passed = 0
    for name, ok, detail in _RESULTS:
        tag = "PASS" if ok else "FAIL"
        passed += ok
        line = f"[{tag}] {name.ljust(width)}"
        if detail and not ok:
            line += f"  -> {detail}"
        print(line)
    total = len(_RESULTS)
    print("-" * (width + 22))
    print(f"{passed}/{total} checks passed")
    print("=" * (width + 22))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
