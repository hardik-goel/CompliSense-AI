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
            "severity": r["severity"],
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


### NOT SURE IF THIS CLAUDE CODE IS OKAY
# # agent/scanner.py
# from pathlib import Path
# from typing import Iterator, Dict, Any, List
# import hashlib
# import json
# from datetime import datetime
#
#
# def run_scan(project_path: Path, rules: Iterator) -> Dict[str, Any]:
#     """
#     Run compliance scan on the given project path
#
#     Args:
#         project_path: Root directory of the ML project
#         rules: Iterator of rules to evaluate
#
#     Returns:
#         Dictionary containing scan results
#     """
#     results = []
#     passed = 0
#     failed = 0
#     warnings = 0
#
#     print(f"Scanning project: {project_path}")
#
#     # Collect project files
#     project_files = discover_project_files(project_path)
#
#     # Run each rule
#     for rule in rules:
#         rule_id = rule.get("id", "unknown")
#         print(f"  Checking rule: {rule_id}")
#
#         try:
#             result = evaluate_rule(rule, project_path, project_files)
#             results.append(result)
#
#             if result["status"] == "passed":
#                 passed += 1
#             elif result["status"] == "failed":
#                 failed += 1
#             elif result["status"] == "warning":
#                 warnings += 1
#
#         except Exception as e:
#             print(f"  ⚠️  Error evaluating rule {rule_id}: {str(e)}")
#             results.append({
#                 "rule_id": rule_id,
#                 "status": "error",
#                 "message": str(e),
#                 "severity": rule.get("severity", "unknown")
#             })
#             failed += 1
#
#     # Build summary
#     summary = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "project_path": str(project_path),
#         "total_rules": len(results),
#         "passed": passed,
#         "failed": failed,
#         "warnings": warnings,
#         "compliance_rate": (passed / len(results) * 100) if results else 0
#     }
#
#     return {
#         "summary": summary,
#         "results": results,
#         "project_files": {
#             "total_files": len(project_files),
#             "python_files": len([f for f in project_files if f.suffix == ".py"]),
#             "config_files": len([f for f in project_files if f.suffix in [".yaml", ".yml", ".json"]]),
#             "model_files": len([f for f in project_files if f.suffix in [".pkl", ".h5", ".pt", ".pth"]])
#         }
#     }
#
#
# def discover_project_files(project_path: Path) -> List[Path]:
#     """
#     Discover all relevant files in the project
#
#     Args:
#         project_path: Root directory
#
#     Returns:
#         List of file paths
#     """
#     exclude_dirs = {
#         ".git", "__pycache__", ".pytest_cache",
#         "node_modules", ".venv", "venv", "env",
#         ".tox", ".eggs", "dist", "build"
#     }
#
#     files = []
#     for item in project_path.rglob("*"):
#         # Skip excluded directories
#         if any(excluded in item.parts for excluded in exclude_dirs):
#             continue
#
#         if item.is_file():
#             files.append(item)
#
#     return files
#
#
# def evaluate_rule(rule: Dict[str, Any], project_path: Path, project_files: List[Path]) -> Dict[str, Any]:
#     """
#     Evaluate a single compliance rule
#
#     Args:
#         rule: Rule definition
#         project_path: Project root
#         project_files: List of discovered files
#
#     Returns:
#         Rule evaluation result
#     """
#     rule_id = rule.get("id", "unknown")
#     evaluator = rule.get("evaluator", "file_presence")
#     inputs = rule.get("inputs", {})
#     expression = rule.get("expression", "true")
#     severity = rule.get("severity", "medium")
#
#     # Default result
#     result = {
#         "rule_id": rule_id,
#         "title": rule.get("title", "Untitled"),
#         "clause": rule.get("clause", ""),
#         "severity": severity,
#         "status": "unknown",
#         "message": "",
#         "evidence": {}
#     }
#
#     try:
#         if evaluator == "file_presence":
#             # Check if required files exist
#             required_file = inputs.get("file")
#             if required_file:
#                 file_path = project_path / required_file
#                 exists = file_path.exists()
#
#                 # Check for required JSON fields if specified
#                 missing_fields = []
#                 if exists and required_file.endswith(".json"):
#                     required_fields = inputs.get("required_json_fields", [])
#                     if required_fields:
#                         try:
#                             with open(file_path) as f:
#                                 data = json.load(f)
#                             missing_fields = [f for f in required_fields if f not in data]
#                         except:
#                             missing_fields = required_fields
#
#                 # Evaluate expression
#                 eval_context = {
#                     "exists": exists,
#                     "missing_fields": len(missing_fields)
#                 }
#
#                 passed = eval(expression, {}, eval_context)
#
#                 result["status"] = "passed" if passed else "failed"
#                 result["message"] = (
#                         f"File {'found' if exists else 'not found'}: {required_file}" +
#                         (f" (missing {len(missing_fields)} required fields)" if missing_fields else "")
#                 )
#                 result["evidence"] = {
#                     "file_exists": exists,
#                     "missing_fields": missing_fields
#                 }
#
#         elif evaluator == "schema_validate":
#             # Validate file against JSON schema
#             schema_file = inputs.get("schema_file")
#             target_file = inputs.get("file")
#
#             if schema_file and target_file:
#                 target_path = project_path / target_file
#                 schema_path = project_path / schema_file
#
#                 if target_path.exists() and schema_path.exists():
#                     import jsonschema
#
#                     with open(target_path) as f:
#                         data = json.load(f)
#                     with open(schema_path) as f:
#                         schema = json.load(f)
#
#                     try:
#                         jsonschema.validate(data, schema)
#                         result["status"] = "passed"
#                         result["message"] = f"Schema validation passed for {target_file}"
#                     except jsonschema.ValidationError as e:
#                         result["status"] = "failed"
#                         result["message"] = f"Schema validation failed: {e.message}"
#                 else:
#                     result["status"] = "failed"
#                     result["message"] = "Required files not found"
#
#         else:
#             # Unknown evaluator
#             result["status"] = "warning"
#             result["message"] = f"Unknown evaluator: {evaluator}"
#
#     except Exception as e:
#         result["status"] = "error"
#         result["message"] = f"Error evaluating rule: {str(e)}"
#
#     return result
