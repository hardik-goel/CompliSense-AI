import yaml
from pathlib import Path
import json, hashlib
from jsonschema import Draft202012Validator
from typing import Dict, Any

from agent.evaluators.file_presence import _is_empty_value


def _substantive_coverage(data: Any, schema: Dict[str, Any]) -> float:
    """Fraction of the schema's target fields that are present AND substantive.

    Schema-valid only means structure/types are ok — it does not mean the document
    actually says anything. This measures whether the expected fields carry real values
    (not blank/placeholder), closing the "schema-valid but empty" gameability (gap 3).
    """
    if not isinstance(data, dict):
        return 0.0
    target = list(schema.get("required") or schema.get("properties", {}).keys())
    if not target:
        return 1.0 if data else 0.0
    populated = sum(1 for k in target if k in data and not _is_empty_value(data.get(k)))
    return round(populated / len(target), 4)

def run(root: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs:
      file: relative data file (YAML or JSON)
      schema_file: relative JSON Schema file
      coverage_min: float (0..1) -> optional metric the schema may compute
    Output context:
      schema_valid: bool
      schema_validation_report: str
      coverage: float (if present in data)
      file_hash: str
    """
    data_path = (root / inputs["file"]).resolve()
    schema_path = (root / inputs["schema_file"]).resolve()
    ctx: Dict[str, Any] = {"schema_valid": False, "coverage": 0.0}

    if not (data_path.exists() and schema_path.exists()):
        ctx["schema_validation_report"] = "missing data or schema file"
        return ctx

    raw = data_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) if data_path.suffix in {".yml", ".yaml"} else json.loads(raw)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            ctx["schema_validation_report"] = "; ".join([e.message for e in errors])
        else:
            ctx["schema_valid"] = True
            ctx["schema_validation_report"] = "ok"
    except Exception as e:
        ctx["schema_validation_error"] = str(e)
        ctx["schema_validation_report"] = f"Validation error: {str(e)}"

    # Coverage: prefer an explicit self-reported metric, else measure substantive
    # field population (NOT a blanket 1.0 for a schema-valid-but-empty document).
    cov = data.get("coverage") if isinstance(data, dict) else None
    if isinstance(cov, (int, float)):
        ctx["coverage"] = float(cov)
    elif ctx.get("schema_valid"):
        ctx["coverage"] = _substantive_coverage(data, schema)
    else:
        ctx["coverage"] = 0.0

    ctx["file_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    
    # Add signals for confidence scoring
    ctx["signals"] = {
        "file_exists": True,
        "schema_valid": ctx.get("schema_valid", False),
        "coverage_met": ctx.get("coverage", 0.0) >= inputs.get("coverage_min", 0.0)
    }
    
    return ctx
