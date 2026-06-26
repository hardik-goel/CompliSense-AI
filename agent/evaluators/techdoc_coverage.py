from pathlib import Path
import json
from agent.evaluators.model_introspect import run as introspect
from agent.evaluators.file_presence import _is_empty_value

# Baseline number of substantive fields a technical doc (e.g. model card) should carry.
_EXPECTED_DOC_FIELDS = 6


def _doc_substance(path: Path) -> float:
    """0..1 — how populated a JSON technical doc is (not just that it exists).

    Closes gap 5: an empty `{}` model_card.json no longer earns the full explicit score.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0.0
    if not isinstance(data, dict) or not data:
        return 0.0
    populated = sum(1 for v in data.values() if not _is_empty_value(v))
    return min(1.0, populated / _EXPECTED_DOC_FIELDS)


def run(root: Path, inputs: dict):
    score = 0.0
    evidence = {}

    # Explicit documentation — scaled by how populated the doc actually is.
    explicit_files = inputs.get("explicit_files", [])
    existing = [root / f for f in explicit_files if (root / f).exists()]
    if existing:
        substance = max(_doc_substance(p) for p in existing)
        score += round(0.7 * substance, 2)
        evidence["explicit"] = True
        evidence["explicit_substance"] = substance
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
