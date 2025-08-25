"""
Module for scanning artefacts against rulepack rules.
Handles evaluator execution, rule expression evaluation, and result aggregation.
"""

from pathlib import Path
from typing import Dict, Any, List
from rule_engine import Rule
from importlib import import_module


def _run_evaluator(root: Path, evaluator: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically import and run an evaluator module.

    Args:
        root (Path): Root path to artefacts.
        evaluator (str): Evaluator name (e.g., "file_presence", "schema_validate").
        inputs (dict): Input configuration for the evaluator.

    Returns:
        dict: Context dictionary with evaluation results.
    """
    mod = import_module(f"agent.evaluators.{evaluator}")
    return mod.run(root, inputs)


def run_scan(root: Path, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute all rules against artefacts in the given root.

    Args:
        root (Path): Path to the artefacts root.
        rules (list): List of rules from the rulepack.

    Returns:
        dict: Summary of passed/failed rules and detailed results.
    """
    results = []
    counts = {"passed": 0, "failed": 0}

    for r in rules:
        ctx = _run_evaluator(Path(root), r["evaluator"], r.get("inputs", {}))
        expr = r["expression"]
        rule = Rule(expr)  # e.g. "exists and missing_fields == 0"

        ok = False
        try:
            ok = bool(rule.matches(ctx))
        except Exception as e:
            ctx["engine_error"] = str(e)

        status = "PASS" if ok else "FAIL"
        counts["passed" if ok else "failed"] += 1

        results.append({
            "rule_id": r["id"],
            "clause": r["clause"],
            "title": r["title"],
            "severity": r["severity"],
            "status": status,
            "context": ctx
        })

    return {"summary": counts, "results": results}
