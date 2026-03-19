"""
Core scanning engine.
Executes evaluators, computes compliance confidence, risk,
and aggregates audit-ready results.
"""

from pathlib import Path
from typing import Dict, Any, List
from importlib import import_module
from time import perf_counter

import yaml
from rule_engine import Rule
from agent.scoring.confidence import compute_confidence
from agent.scoring.risk import classify_risk
from agent.remediation.generator import generate_remediation
from agent.inference.llm import infer
from agent.utils.resources import resource_path


def _is_missing_evidence(ctx: Dict[str, Any]) -> bool:
    """
    Evidence is missing if evaluator returned no meaningful signals.
    """
    if not ctx:
        return True
    if ctx.get("engine_error"):
        return False
    signals = ctx.get("signals")
    return signals in (None, {}, [])


def scan_required_artifacts(root: Path) -> Dict[str, Any]:
    manifest = Path(resource_path("agent/artefacts/required_artifacts.yaml"))
    spec = yaml.safe_load(manifest.read_text())

    missing = []
    present = []

    for a in spec["artifacts"]:
        found = False
        for f in a["files"]:
            if (root / f).exists():
                found = True
                break

        if found:
            present.append(a["id"])
        else:
            missing.append(a)

    total = len(spec["artifacts"])
    compliance_pct = round(len(present) / total * 100, 2)

    return {
        "required_total": total,
        "present": present,
        "missing": missing,
        "compliance_pct": compliance_pct
    }


def _run_evaluator(root: Path, evaluator: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    mod = import_module(f"agent.evaluators.{evaluator}")
    return mod.run(root, inputs)


def run_scan(
    root: Path,
    rules: List[Dict[str, Any]],
    llm_enabled: bool = False,
    progress_callback=None,
    cancel_event=None
) -> Dict[str, Any]:

    results = []
    counts = {"passed": 0, "partial": 0, "failed": 0}
    artifact_scan = scan_required_artifacts(root)
    # ---- Discover files once ----
    all_files = [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
    ]

    if progress_callback:
        progress_callback({"event": "FILES_DISCOVERED", "files": all_files})

    total_rules = len(rules)

    for idx, r in enumerate(rules, start=1):

        if cancel_event and cancel_event.is_set():
            if progress_callback:
                progress_callback({"event": "SCAN_CANCELLED"})
            break

        if progress_callback:
            progress_callback({
                "event": "RULE_START",
                "rule_id": r["id"],
                "index": idx,
                "total": total_rules
            })

        start = perf_counter()
        ctx: Dict[str, Any] = {}

        try:
            ctx = _run_evaluator(root, r["evaluator"], r.get("inputs", {}))
        except Exception as e:
            ctx = {"engine_error": str(e)}

        elapsed_sec = round(perf_counter() - start, 3)
        elapsed_ms = elapsed_sec * 1000

        # ---- Files used by rule ----
        files_used = [
            v for v in r.get("inputs", {}).values()
            if isinstance(v, str) and "/" in v
        ]

        # ---- Rule evaluation ----
        rule = Rule(r.get("expression", "False"))
        status = "FAIL"
        ok = False
        missing = _is_missing_evidence(ctx)

        thresholds = r.get("thresholds")
        # Check for both coverage_score (from techdoc_coverage) and coverage (from schema_validate)
        score = ctx.get("coverage_score") or ctx.get("coverage")
        
        # For file_presence evaluator with thresholds, use missing_fields count
        missing_fields = ctx.get("missing_fields")
        if thresholds and missing_fields is not None:
            # Thresholds for file_presence are based on missing_fields count (lower is better)
            pass_threshold = thresholds.get("pass", 0.0)  # Allow 0 missing for pass
            partial_threshold = thresholds.get("partial", 2.0)  # Allow up to 2 missing for partial
            
            if missing_fields <= pass_threshold:
                status = "PASS"
                ok = True
            elif missing_fields <= partial_threshold:
                status = "PARTIAL"
                ok = False
            else:
                status = "FAIL"
                ok = False
        elif thresholds and score is not None:
            # For score-based thresholds (coverage_score or coverage)
            pass_threshold = thresholds.get("pass", 1.0)
            partial_threshold = thresholds.get("partial", 0.5)
            
            if score >= pass_threshold:
                status = "PASS"
                ok = True
            elif score >= partial_threshold:
                status = "PARTIAL"
                ok = False
            else:
                status = "FAIL"
                ok = False
        else:
            # For expression-based rules, inject rule inputs into context for evaluation
            eval_ctx = ctx.copy()
            # Add rule inputs to context so expressions can reference them (e.g., coverage_min)
            for key, value in r.get("inputs", {}).items():
                if key not in eval_ctx:  # Don't override evaluator results
                    eval_ctx[key] = value
            
            try:
                ok = bool(rule.matches(eval_ctx))
            except Exception as e:
                ok = False
                ctx["expression_error"] = str(e)

            if ok:
                status = "PASS"
            elif missing:
                status = "MISSING"
            else:
                status = "FAIL"

        if status == "PASS":
            counts["passed"] += 1
        elif status in ("PARTIAL", "MISSING"):
            counts["partial"] += 1
        else:
            counts["failed"] += 1

        # ---- Confidence & risk ----
        signals = ctx.get("signals", {})
        weights = r.get("weights", {})
        
        # Build signals from context if not explicitly provided
        if not signals:
            signals = {}
            if ctx.get("exists"):
                signals["file_exists"] = True
            if ctx.get("schema_valid"):
                signals["schema_valid"] = True
            if ctx.get("missing_fields", 0) == 0:
                signals["all_fields_present"] = True
            if score is not None:
                signals["coverage_score"] = score

        # Use weighted confidence if weights are provided, otherwise use status-based
        if weights and signals:
            confidence = compute_confidence(signals, weights)
        elif status == "PASS":
            confidence = 100
        elif status == "PARTIAL":
            confidence = 60
        elif status == "MISSING":
            confidence = 40
        else:
            confidence = 20

        risk = classify_risk(confidence)

        if confidence < 50 and llm_enabled:
            ctx["llm_inference"] = infer(signals)

        remediation = generate_remediation(r["id"], confidence) if status != "PASS" else []

        # ---- SLA evaluation ----
        sla = r.get("sla", {})
        sla_status = "OK"
        if "fail_ms" in sla and elapsed_ms > sla["fail_ms"]:
            sla_status = "FAIL"
        elif "warn_ms" in sla and elapsed_ms > sla["warn_ms"]:
            sla_status = "WARN"

        results.append({
            "rule_id": r["id"],
            "clause": r["clause"],
            "title": r["title"],
            "severity": r.get("severity", "unknown"),
            "status": status,
            "confidence": confidence,
            "risk": risk,
            "execution_time_sec": elapsed_sec,
            "sla_status": sla_status,
            "files_used": files_used,
            "remediation": remediation,
            "context": ctx
        })

        if progress_callback:
            progress_callback({
                "event": "RULE_END",
                "rule_id": r["id"],
                "status": status,
                "index": idx,
                "total": total_rules
            })

    if progress_callback:
        progress_callback({"event": "SCAN_COMPLETE"})

    return {
        "summary": counts,
        "results": results,
        "artifacts": artifact_scan
    }
