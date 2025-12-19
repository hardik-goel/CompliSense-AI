"""
Core scanning engine.
Executes evaluators, computes compliance confidence, risk,
and aggregates audit-ready results.
"""

from pathlib import Path
from typing import Dict, Any, List
from importlib import import_module
from rule_engine import Rule

from agent.scoring.confidence import compute_confidence
from agent.scoring.risk import classify_risk
from agent.remediation.generator import generate_remediation
from agent.inference.llm import infer


def _run_evaluator(root: Path, evaluator: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically load and run an evaluator.
    """
    mod = import_module(f"agent.evaluators.{evaluator}")
    return mod.run(root, inputs)


def run_scan(
    root: Path,
    rules: List[Dict[str, Any]],
    llm_enabled: bool = False
) -> Dict[str, Any]:
    """
    Execute all rules against a given model/artifact directory.
    """

    results = []
    counts = {"passed": 0, "failed": 0}

    for r in rules:
        ctx: Dict[str, Any] = {}

        # ---------- Run evaluator ----------
        try:
            ctx = _run_evaluator(root, r["evaluator"], r.get("inputs", {}))
        except Exception as e:
            ctx = {
                "engine_error": f"Evaluator failed: {str(e)}"
            }

        # ---------- Evaluate rule expression ----------
        expr = r.get("expression", "False")
        rule = Rule(expr)

        try:
            ok = bool(rule.matches(ctx))
        except Exception as e:
            ok = False
            ctx["expression_error"] = str(e)

        status = "PASS" if ok else "FAIL"
        counts["passed" if ok else "failed"] += 1

        # ---------- Confidence & risk ----------
        signals = ctx.get("signals", {})
        weights = r.get("weights", {})

        if weights:
            confidence = compute_confidence(signals, weights)
        else:
            confidence = 100 if ok else 30  # fallback

        risk = classify_risk(confidence)

        # ---------- Optional LLM inference ----------
        if confidence < 50 and llm_enabled:
            ctx["llm_inference"] = infer(signals)

        # ---------- Remediation ----------
        remediation = []
        if status != "PASS":
            remediation = generate_remediation(r["id"], confidence)

        results.append({
            "rule_id": r["id"],
            "clause": r["clause"],
            "title": r["title"],
            # agent/scanner.py
            "severity": r.get("severity", "unknown"),  # Use a default if missing
            "status": status,
            "confidence": confidence,
            "risk": risk,
            "remediation": remediation,
            "context": ctx
        })

    return {
        "summary": counts,
        "results": results
    }
