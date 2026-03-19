from pathlib import Path
import json, hashlib
from typing import Dict, Any, List

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def run(root: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs:
      file: relative path
      required_json_fields: optional[List[str]]
    Output context:
      exists: bool
      missing_fields: int
      missing_fields_list: List[str]
      file_hash: str (if exists)
      model_card_snapshot/dataset_card_snapshot: str (optional raw text)
    """
    rel = Path(inputs["file"])
    path = (root / rel).resolve()
    ctx: Dict[str, Any] = {"exists": path.exists(), "missing_fields": 0, "missing_fields_list": []}
    if not ctx["exists"]:
        return ctx

    # Hash for evidence
    ctx["file_hash"] = _sha256(path)

    req = inputs.get("required_json_fields", [])
    if req:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            missing: List[str] = [k for k in req if k not in data or data.get(k) in (None, "", [])]
            ctx["missing_fields"] = len(missing)
            ctx["missing_fields_list"] = missing
            # Optional snapshot for PDF appendix
            key = "model_card_snapshot" if "model_card" in str(rel) else "dataset_card_snapshot"
            ctx[key] = json.dumps({k: data.get(k) for k in req}, indent=2)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            ctx["parse_error"] = str(e)
            ctx["missing_fields"] = len(req)  # Treat parse error as all missing
    
    # Add signals for confidence scoring
    ctx["signals"] = {
        "file_exists": ctx["exists"],
        "all_fields_present": ctx.get("missing_fields", 0) == 0 if ctx["exists"] else False
    }
    
    return ctx
