"""
Module for loading and iterating over rulepacks.

Loading now runs schema-v2 validation (see ``compliance/rulepack_schema.py``). By default
validation is NON-FATAL: issues are logged as warnings so existing flows keep working while
packs are migrated. Pass ``strict=True`` (or set ``RULEPACK_STRICT=1``) to hard-fail on an
invalid pack — useful in CI / pack authoring.
"""

from pathlib import Path
import logging
import os

import yaml
from typing import Dict, Any, List

try:  # keep loader importable even if the agent is run without the compliance pkg on path
    from compliance.rulepack_schema import validate_pack, RulepackValidationError
except Exception:  # pragma: no cover - defensive fallback
    validate_pack = None  # type: ignore
    RulepackValidationError = RuntimeError  # type: ignore

logger = logging.getLogger(__name__)


def load_rulepack(path: Path, validate: bool = True, strict: bool | None = None) -> Dict[str, Any]:
    """
    Load a rulepack YAML file from disk and (optionally) validate it against schema v2.

    Args:
        path: Path to the rulepack YAML file.
        validate: Run schema-v2 validation after loading (default True).
        strict: If True, raise on validation failure. If None, falls back to the
            ``RULEPACK_STRICT`` env var (``1``/``true`` enables strict mode).

    Returns:
        dict: Parsed contents of the rulepack file.

    Raises:
        RulepackValidationError: when ``strict`` is enabled and the pack is invalid.
    """
    pack = yaml.safe_load(path.read_text(encoding="utf-8"))

    if validate and validate_pack is not None and isinstance(pack, dict):
        if strict is None:
            strict = os.getenv("RULEPACK_STRICT", "").lower() in ("1", "true", "yes")
        result = validate_pack(pack)
        if not result.ok:
            if strict:
                raise RulepackValidationError(result.summary())
            logger.warning("Rulepack %s: %s", path.name, result.summary())

    return pack


def iter_rules(pack: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract the list of rules from a loaded rulepack.

    Args:
        pack (dict): Rulepack dictionary (parsed YAML).

    Returns:
        list: A list of rule dictionaries.
    """
    return pack.get("rules", [])
