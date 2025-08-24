from pathlib import Path
import yaml
from typing import Dict, Any, List

def load_rulepack(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def iter_rules(pack: Dict[str, Any]) -> List[Dict[str, Any]]:
    return pack.get("rules", [])
