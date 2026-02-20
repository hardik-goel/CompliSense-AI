from pathlib import Path
from agent.evaluators.model_introspect import run as introspect

def run(root: Path, inputs: dict):
    score = 0.0
    evidence = {}

    # Explicit documentation
    explicit_files = inputs.get("explicit_files", [])
    explicit_found = any((root / f).exists() for f in explicit_files)
    if explicit_found:
        score += 0.7
        evidence["explicit"] = True
    else:
        evidence["explicit"] = False

    # Implicit signals
    implicit_score = 0.0
    if "model_introspect" in inputs.get("implicit_evaluators", []):
        introspection = introspect(root, {})
        if introspection.get("model_found"):
            implicit_score += 0.3
            evidence["model_introspection"] = introspection

    score += implicit_score

    return {
        "coverage_score": round(score, 2),
        "evidence": evidence,
        "signals": {
            "explicit_docs": evidence.get("explicit", False),
            "model_found": evidence.get("model_introspection", {}).get("model_found", False)
        }
    }
