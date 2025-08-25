"""
Module for loading and iterating over rulepacks.
"""

from pathlib import Path
import yaml
from typing import Dict, Any, List


def load_rulepack(path: Path) -> Dict[str, Any]:
    """
    Load a rulepack YAML file from disk.

    Args:
        path (Path): Path to the rulepack YAML file.

    Returns:
        dict: Parsed contents of the rulepack file.
    """
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def iter_rules(pack: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract the list of rules from a loaded rulepack.

    Args:
        pack (dict): Rulepack dictionary (parsed YAML).

    Returns:
        list: A list of rule dictionaries.
    """
    return pack.get("rules", [])
