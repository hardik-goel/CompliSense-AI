from pathlib import Path
from typing import Dict, Any, List
from rule_engine import Rule
from importlib import import_module

def _run_evaluator(root: Path, evaluator: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    mod = import_module(f"agent.evaluators.{evaluator}")
    return mod.run(root, inputs)

def run_scan(root: Path, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = []
    counts = {"passed":0, "failed":0}
    for r in rules:
        ctx = _run_evaluator(Path(root), r["evaluator"], r.get("inputs", {}))
        expr = r["expression"]
        rule = Rule(expr)  # boolean expression like "exists and missing_fields == 0"
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
