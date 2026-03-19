"""
Core scanning engine with enhanced error handling.
Executes evaluators, computes compliance confidence, risk,
and aggregates audit-ready results.
"""

from pathlib import Path
from typing import Dict, Any, List
from importlib import import_module
from time import perf_counter
import logging

import yaml
from rule_engine import Rule
from agent.scoring.confidence import compute_confidence
from agent.scoring.risk import classify_risk
from agent.remediation.generator import generate_remediation
from agent.inference.llm import infer
from agent.utils.resources import resource_path

logger = logging.getLogger(__name__)


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
    """Scan for required artifacts with better error handling."""
    try:
        manifest = Path(resource_path("agent/artefacts/required_artifacts.yaml"))
        if not manifest.exists():
            logger.error(f"Required artifacts manifest not found at {manifest}")
            return {
                "required_total": 0,
                "present": [],
                "missing": [],
                "compliance_pct": 0.0,
                "error": f"Manifest file not found: {manifest}"
            }
        
        spec = yaml.safe_load(manifest.read_text())
        if not spec or "artifacts" not in spec:
            logger.error("Invalid manifest structure")
            return {
                "required_total": 0,
                "present": [],
                "missing": [],
                "compliance_pct": 0.0,
                "error": "Invalid manifest structure"
            }

        missing = []
        present = []

        for a in spec["artifacts"]:
            found = False
            for f in a.get("files", []):
                try:
                    if (root / f).exists():
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"Error checking file {f}: {e}")
                    continue

            if found:
                present.append(a["id"])
            else:
                missing.append(a)

        total = len(spec["artifacts"])
        compliance_pct = round(len(present) / total * 100, 2) if total > 0 else 0.0

        return {
            "required_total": total,
            "present": present,
            "missing": missing,
            "compliance_pct": compliance_pct
        }
    except Exception as e:
        logger.exception(f"Error scanning required artifacts: {e}")
        return {
            "required_total": 0,
            "present": [],
            "missing": [],
            "compliance_pct": 0.0,
            "error": str(e)
        }


def _run_evaluator(root: Path, evaluator: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run evaluator with enhanced error handling."""
    # Explicitly import all evaluators so PyInstaller finds them
    from agent.evaluators import file_presence
    from agent.evaluators import schema_validate
    from agent.evaluators import techdoc_coverage
    from agent.evaluators import keyword_check
    from agent.evaluators import model_introspect

    EVALUATORS = {
        "file_presence": file_presence,
        "schema_validate": schema_validate,
        "techdoc_coverage": techdoc_coverage,
        "keyword_check": keyword_check,
        "model_introspect": model_introspect,
    }

    if evaluator not in EVALUATORS:
        logger.error(f"Failed to find evaluator {evaluator}")
        return {
            "engine_error": f"Evaluator '{evaluator}' not found. Available evaluators: {', '.join(EVALUATORS.keys())}",
            "evaluator": evaluator
        }

    mod = EVALUATORS[evaluator]
    try:
        if not hasattr(mod, 'run'):
            raise AttributeError(f"Evaluator {evaluator} has no 'run' function")
        return mod.run(root, inputs)
    except AttributeError as e:
        logger.error(f"Evaluator {evaluator} missing required function: {e}")
        return {
            "engine_error": f"Evaluator '{evaluator}' is invalid: {e}",
            "evaluator": evaluator
        }
    except Exception as e:
        logger.exception(f"Error running evaluator {evaluator}: {e}")
        return {
            "engine_error": f"Error in evaluator '{evaluator}': {str(e)}",
            "evaluator": evaluator
        }


def run_scan(
    root: Path,
    rules: List[Dict[str, Any]],
    llm_enabled: bool = False,
    progress_callback=None,
    cancel_event=None
) -> Dict[str, Any]:
    """Run compliance scan with enhanced error handling."""
    
    # Validate inputs
    if not root.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root}")
    if not rules:
        logger.warning("No rules provided for scan")
        return {
            "summary": {"passed": 0, "partial": 0, "failed": 0},
            "results": [],
            "artifacts": {"required_total": 0, "present": [], "missing": [], "compliance_pct": 0.0},
            "error": "No rules provided"
        }

    results = []
    counts = {"passed": 0, "partial": 0, "failed": 0}
    
    try:
        artifact_scan = scan_required_artifacts(root)
    except Exception as e:
        logger.exception(f"Error scanning artifacts: {e}")
        artifact_scan = {
            "required_total": 0,
            "present": [],
            "missing": [],
            "compliance_pct": 0.0,
            "error": str(e)
        }
    
    # ---- Discover files once ----
    try:
        all_files = [
            str(p.relative_to(root))
            for p in root.rglob("*")
            if p.is_file()
        ]
    except Exception as e:
        logger.warning(f"Error discovering files: {e}")
        all_files = []

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
                "rule_id": r.get("id", f"rule_{idx}"),
                "index": idx,
                "total": total_rules
            })

        start = perf_counter()
        ctx: Dict[str, Any] = {}

        # Validate rule structure
        if "evaluator" not in r:
            logger.error(f"Rule {r.get('id', idx)} missing 'evaluator' field")
            ctx = {"engine_error": "Rule missing 'evaluator' field"}
        else:
            try:
                ctx = _run_evaluator(root, r["evaluator"], r.get("inputs", {}))
            except Exception as e:
                logger.exception(f"Unexpected error in evaluator: {e}")
                ctx = {"engine_error": f"Unexpected error: {str(e)}"}

        elapsed_sec = round(perf_counter() - start, 3)
        elapsed_ms = elapsed_sec * 1000

        # ---- Files used by rule ----
        files_used = [
            v for v in r.get("inputs", {}).values()
            if isinstance(v, str) and "/" in v
        ]

        # ---- Rule evaluation ----
        rule_expr = r.get("expression", "False")
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
                rule = Rule(rule_expr)
                ok = bool(rule.matches(eval_ctx))
            except Exception as e:
                logger.warning(f"Error evaluating rule expression '{rule_expr}': {e}")
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
            try:
                confidence = compute_confidence(signals, weights)
            except Exception as e:
                logger.warning(f"Error computing confidence: {e}")
                confidence = 100 if status == "PASS" else (60 if status == "PARTIAL" else 20)
        elif status == "PASS":
            confidence = 100
        elif status == "PARTIAL":
            confidence = 60
        elif status == "MISSING":
            confidence = 40
        else:
            confidence = 20

        risk = classify_risk(confidence, r.get("severity", "unknown"))

        if confidence < 50 and llm_enabled:
            try:
                ctx["llm_inference"] = infer(signals)
            except Exception as e:
                logger.warning(f"LLM inference failed: {e}")

        remediation = []
        if status != "PASS":
            try:
                remediation = generate_remediation(r.get("id", ""), confidence)
            except Exception as e:
                logger.warning(f"Error generating remediation: {e}")

        # ---- Extract evidence ----
        evidence = {}
        if ctx.get("exists"):
            evidence["file_found"] = True
            if ctx.get("file_hash"):
                evidence["file_hash"] = ctx["file_hash"][:16] + "..."  # Truncate for display
        if ctx.get("schema_valid"):
            evidence["schema_valid"] = True
        if ctx.get("missing_fields", 0) > 0:
            evidence["missing_fields"] = ctx.get("missing_fields_list", [])
        if ctx.get("coverage") is not None:
            evidence["coverage"] = ctx.get("coverage")
        if ctx.get("coverage_score") is not None:
            evidence["coverage_score"] = ctx.get("coverage_score")
        if ctx.get("schema_validation_report"):
            evidence["validation_report"] = ctx.get("schema_validation_report")
        if ctx.get("parse_error"):
            evidence["parse_error"] = ctx.get("parse_error")
        if ctx.get("engine_error"):
            evidence["error"] = ctx.get("engine_error")

        # ---- SLA evaluation ----
        sla = r.get("sla", {})
        sla_status = "OK"
        if "fail_ms" in sla and elapsed_ms > sla["fail_ms"]:
            sla_status = "FAIL"
        elif "warn_ms" in sla and elapsed_ms > sla["warn_ms"]:
            sla_status = "WARN"

        results.append({
            "rule_id": r.get("id", f"rule_{idx}"),
            "clause": r.get("clause", "Unknown"),
            "title": r.get("title", "Untitled rule"),
            "severity": r.get("severity", "unknown"),
            "status": status,
            "confidence": confidence,
            "risk": risk,
            "execution_time_sec": elapsed_sec,
            "sla_status": sla_status,
            "files_used": files_used,
            "remediation": remediation,
            "evidence": evidence,
            "context": ctx
        })

        if progress_callback:
            progress_callback({
                "event": "RULE_END",
                "rule_id": r.get("id", f"rule_{idx}"),
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
