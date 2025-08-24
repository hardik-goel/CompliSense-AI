from pathlib import Path
from typing import Dict, Any, List

def run(root: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs:
      file: relative path (e.g., docs/instructions_for_use.md)
      must_include: List[str]
    Output:
      contains_all: bool
      missing_phrases: List[str]
    """
    path = (root / inputs["file"]).resolve()
    if not path.exists():
        return {"contains_all": False, "missing_phrases": inputs.get("must_include", [])}
    text = path.read_text(encoding="utf-8").lower()
    missing: List[str] = [p for p in inputs.get("must_include", []) if p.lower() not in text]
    return {"contains_all": len(missing) == 0, "missing_phrases": missing}
