"""
Cross-document consistency checks (audit gap 4).

The rules engine evaluates each artefact in isolation, so contradictory facts spread across
documents (e.g. a grievance contact that differs between the privacy notice and the
grievance SOP) all pass individually. This module compares declared values ACROSS files.

Design choices, on purpose:
- **Advisory only.** Findings are informational; they do NOT change pass/fail counts. In a
  compliance tool a false "you contradict yourself" is worse than silence, so this never
  fails a scan — it surfaces a hint for human review.
- **Explicit, configured checks.** No fuzzy guessing. Each check names exact files + keys.
  A check fires only when 2+ named sources are present AND their values genuinely differ.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from agent.evaluators.file_presence import _is_empty_value


def _load(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(raw) or {}
    return json.loads(raw)


def _normalise(v: Any) -> str:
    return str(v).strip().lower()


# Default high-confidence DPDP checks. Each source is (relative_file, top_level_key).
DEFAULT_DPDP_CHECKS: List[Dict[str, Any]] = [
    {
        "id": "CONSISTENCY-DPDP-GRIEVANCE-CONTACT",
        "description": "Grievance/contact point should match across the privacy notice and grievance SOP.",
        "sources": [
            ["compliance/privacy_notice.json", "grievance_contact"],
            ["compliance/grievance_redressal.yaml", "contact_point"],
        ],
    },
    {
        "id": "CONSISTENCY-DPDP-FIDUCIARY-NAME",
        "description": "Data fiduciary name should match across the privacy notice and consent record.",
        "sources": [
            ["compliance/privacy_notice.json", "data_fiduciary_name"],
            ["compliance/consent_record.json", "data_fiduciary_name"],
        ],
    },
]


def run_consistency_checks(root: Path, checks: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Run configured cross-document checks. Returns a list of advisory findings."""
    findings: List[Dict[str, Any]] = []
    for check in checks or []:
        observed: Dict[str, Any] = {}
        for rel, key in check.get("sources", []):
            path = (root / rel).resolve()
            if not path.exists():
                continue
            try:
                data = _load(path)
            except (json.JSONDecodeError, UnicodeDecodeError, yaml.YAMLError):
                continue
            if isinstance(data, dict) and key in data and not _is_empty_value(data.get(key)):
                observed[f"{rel}#{key}"] = data[key]

        distinct = {_normalise(v) for v in observed.values()}
        if len(observed) >= 2 and len(distinct) > 1:
            findings.append({
                "id": check["id"],
                "description": check["description"],
                "status": "INCONSISTENT",
                "severity": "Advisory",
                "observed": observed,
            })
    return findings
