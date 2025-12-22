"""
Core scanning engine.
Executes evaluators, computes compliance confidence, risk,
and aggregates audit-ready results.
"""

from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from importlib import import_module
import json

from rule_engine import Rule
from agent.scoring.confidence import compute_confidence
from agent.scoring.risk import classify_risk
from agent.remediation.generator import generate_remediation
from agent.inference.llm import infer


def _run_evaluator(
    root: Path,
    evaluator: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Dynamically load and run an evaluator.
    """
    mod = import_module(f"agent.evaluators.{evaluator}")
    return mod.run(root, inputs)


def run_scan(
    root: Path,
    rules: List[Dict[str, Any]],
    llm_enabled: bool = False,
    progress_cb: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Execute all rules against a given model/artifact directory.

    progress_cb(done, total, rule_id) will be called after each rule
    so UI can update progress bar.
    """

    results: List[Dict[str, Any]] = []

    counts = {
        "passed": 0,
        "failed": 0,
        "error": 0
    }

    total_rules = len(rules)

    for idx, r in enumerate(rules, start=1):
        ctx: Dict[str, Any] = {}

        # -----------------------------
        # Run evaluator
        # -----------------------------
        try:
            ctx = _run_evaluator(
                root=root,
                evaluator=r["evaluator"],
                inputs=r.get("inputs", {})
            )
        except Exception as e:
            ctx = {
                "engine_error": f"Evaluator failed: {str(e)}"
            }

        # -----------------------------
        # Evaluate rule expression
        # -----------------------------
        expr = r.get("expression", "False")
        rule = Rule(expr)

        try:
            ok = bool(rule.matches(ctx))
        except Exception as e:
            ok = False
            ctx["expression_error"] = str(e)

        # -----------------------------
        # Final status (IMPORTANT)
        # -----------------------------
        if "engine_error" in ctx:
            status = "ERROR"
            counts["error"] += 1
        elif ok:
            status = "PASS"
            counts["passed"] += 1
        else:
            status = "FAIL"
            counts["failed"] += 1

        # -----------------------------
        # Confidence & risk
        # -----------------------------
        signals = ctx.get("signals", {})
        weights = r.get("weights", {})

        if weights:
            confidence = compute_confidence(signals, weights)
        else:
            confidence = 100 if status == "PASS" else 30

        risk = classify_risk(confidence)

        # -----------------------------
        # Optional LLM inference
        # -----------------------------
        if confidence < 50 and llm_enabled:
            ctx["llm_inference"] = infer(signals)

        # -----------------------------
        # Remediation
        # -----------------------------
        remediation = []
        if status in ("FAIL", "ERROR"):
            remediation = generate_remediation(
                r["id"],
                confidence
            )

        # -----------------------------
        # Collect result
        # -----------------------------
        results.append({
            "rule_id": r["id"],
            "clause": r.get("clause", "N/A"),
            "title": r.get("title", r["id"]),
            "severity": r.get("severity", "unknown"),
            "status": status,
            "confidence": confidence,
            "risk": risk,
            "remediation": remediation,
            "context": ctx
        })

        # -----------------------------
        # Progress callback (UI hook)
        # -----------------------------
        if progress_cb:
            progress_cb(idx, total_rules, r["id"])

    # -----------------------------
    # Write output to disk (FIX)
    # -----------------------------
    output_dir = root / "complisense_output"
    output_dir.mkdir(exist_ok=True)

    output = {
        "summary": counts,
        "results": results
    }

    (output_dir / "results.json").write_text(
        json.dumps(output, indent=2)
    )

    return output
