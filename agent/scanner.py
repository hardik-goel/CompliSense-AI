"""
Core scanning engine.
Executes evaluators, computes compliance confidence, risk,
and aggregates audit-ready results.
"""

from pathlib import Path
from typing import Dict, Any, List
from importlib import import_module
from time import perf_counter

from rule_engine import Rule
from agent.scoring.confidence import compute_confidence
from agent.scoring.risk import classify_risk
from agent.remediation.generator import generate_remediation
from agent.inference.llm import infer


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

        thresholds = r.get("thresholds")
        score = ctx.get("coverage_score")

        if thresholds and score is not None:
            if score >= thresholds.get("pass", 1.0):
                status = "PASS"
                ok = True
            elif score >= thresholds.get("partial", 0):
                status = "PARTIAL"
                ok = False
            else:
                status = "FAIL"
                ok = False
        else:
            try:
                ok = bool(rule.matches(ctx))
            except Exception as e:
                ok = False
                ctx["expression_error"] = str(e)

            status = "PASS" if ok else "FAIL"

        counts[
            "passed" if status == "PASS"
            else "partial" if status == "PARTIAL"
            else "failed"
        ] += 1

        # ---- Confidence & risk ----
        signals = ctx.get("signals", {})
        weights = r.get("weights", {})

        confidence = (
            compute_confidence(signals, weights)
            if weights
            else (100 if ok else 50 if status == "PARTIAL" else 30)
        )

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
        "results": results
    }
