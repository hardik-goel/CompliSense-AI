from pathlib import Path
import json, hashlib, re
from datetime import date
from typing import Dict, Any, List
import yaml

# Values that are technically "present" but carry no substance. Treating these as missing
# closes the worst gameability vector: setting a required field to a placeholder to pass.
# (Audit finding H6 — verify substance, not mere presence.) Matched case-insensitively
# against the stripped value.
_PLACEHOLDER_VALUES = {
    "", "todo", "tbd", "tba", "n/a", "na", "none", "null", "changeme", "change-me",
    "xxx", "xx", "fixme", "placeholder", "fill", "fillme", "fill_me", "fill me",
    "<fill>", "...", "-", "—", "example", "sample",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _is_empty_value(v: Any) -> bool:
    """True if the value is absent in substance (None, empty container, or a placeholder)."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip().lower() in _PLACEHOLDER_VALUES
    if isinstance(v, (list, dict, tuple, set)):
        return len(v) == 0
    return False  # numbers, bools, etc. count as real values


def _validate_value(v: Any, spec: str) -> bool:
    """Validate a value against a simple type spec. Returns True if valid."""
    spec = str(spec).strip().lower()
    if _is_empty_value(v):
        return False
    if spec == "email":
        return isinstance(v, str) and bool(_EMAIL_RE.match(v.strip()))
    if spec in ("iso_date", "date"):
        try:
            date.fromisoformat(str(v).strip())
            return True
        except ValueError:
            return False
    if spec == "url":
        return isinstance(v, str) and v.strip().lower().startswith(("http://", "https://"))
    if spec.startswith("min_length:"):
        try:
            n = int(spec.split(":", 1)[1])
        except ValueError:
            return True
        return len(str(v).strip()) >= n
    # non_empty / unknown spec → already passed the empty check above
    return True


def run(root: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs:
      file: relative path
      required_json_fields: optional[List[str]]
      field_validations: optional[Dict[str, str]]  # field -> email|iso_date|url|min_length:N
    Output context:
      exists: bool
      missing_fields: int           # absent OR placeholder OR failing validation
      missing_fields_list: List[str]
      invalid_fields_list: List[str]  # present-but-failed-validation (subset detail)
      file_hash: str (if exists)
    """
    rel = Path(inputs["file"])
    path = (root / rel).resolve()
    ctx: Dict[str, Any] = {
        "exists": path.exists(),
        "missing_fields": 0,
        "missing_fields_list": [],
        "invalid_fields_list": [],
    }
    if not ctx["exists"]:
        return ctx

    # Hash for evidence
    ctx["file_hash"] = _sha256(path)

    req = inputs.get("required_json_fields", [])
    validations = inputs.get("field_validations", {}) or {}
    if req:
        try:
            raw_text = path.read_text(encoding="utf-8")
            if path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(raw_text) or {}
            else:
                data = json.loads(raw_text)

            missing: List[str] = []
            invalid: List[str] = []
            for k in req:
                if k not in data or _is_empty_value(data.get(k)):
                    missing.append(k)
                    continue
                if k in validations and not _validate_value(data.get(k), validations[k]):
                    invalid.append(k)
                    missing.append(k)  # an invalid value is not a satisfied requirement

            ctx["missing_fields"] = len(missing)
            ctx["missing_fields_list"] = missing
            ctx["invalid_fields_list"] = invalid
            # Optional snapshot for PDF appendix
            key = "model_card_snapshot" if "model_card" in str(rel) else "dataset_card_snapshot"
            ctx[key] = json.dumps({k: data.get(k) for k in req}, indent=2, default=str)
        except (json.JSONDecodeError, UnicodeDecodeError, yaml.YAMLError) as e:
            ctx["parse_error"] = str(e)
            ctx["missing_fields"] = len(req)  # Treat parse error as all missing

    # Add signals for confidence scoring
    ctx["signals"] = {
        "file_exists": ctx["exists"],
        "all_fields_present": ctx.get("missing_fields", 0) == 0 if ctx["exists"] else False,
        "no_invalid_values": len(ctx.get("invalid_fields_list", [])) == 0,
    }

    return ctx
