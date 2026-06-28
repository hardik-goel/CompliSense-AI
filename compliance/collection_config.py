"""Validate a 'collection source' declaration (pure).

The hosted app stores only NON-SECRET config for each source (bucket, prefix, repo, path, …).
Credentials are supplied locally when the agent runs — they must never reach our backend. This
validator enforces the allowed fields per source type and rejects anything that looks like a
secret, so a token can't be accidentally stored server-side.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

# type -> (required non-secret fields, optional non-secret fields)
SOURCE_SPECS: Dict[str, Tuple[List[str], List[str]]] = {
    "local":       (["path"], []),
    "s3":          (["bucket"], ["prefix", "region"]),
    "gcs":         (["bucket"], ["prefix"]),
    "azure_blob":  (["account_url", "container"], ["prefix"]),
    "github":      (["repo"], ["path", "ref"]),
    "notion":      ([], ["database_id"]),
    "gdrive":      ([], ["folder_id"]),
    "sharepoint":  ([], ["site"]),
}

# Substrings that mark a field as a secret — never allowed in stored config.
SECRET_HINTS = ("token", "secret", "password", "passwd", "credential", "access_key",
                "secret_key", "api_key", "apikey", "private", "session")


class CollectionConfigError(ValueError):
    pass


def validate_source(source: Dict[str, Any]) -> Dict[str, Any]:
    """Validate one source declaration; return a normalised {type,label,config}. Raises on error."""
    stype = (source.get("type") or "").strip()
    if stype not in SOURCE_SPECS:
        raise CollectionConfigError(f"unknown source type '{stype}'. Allowed: {', '.join(SOURCE_SPECS)}")
    required, optional = SOURCE_SPECS[stype]
    config = source.get("config") or {}
    if not isinstance(config, dict):
        raise CollectionConfigError("config must be an object")

    for key in config:
        low = key.lower()
        if any(h in low for h in SECRET_HINTS):
            raise CollectionConfigError(
                f"'{key}' looks like a secret — credentials are supplied locally when the agent "
                "runs and must not be stored here.")
        if key not in required and key not in optional:
            raise CollectionConfigError(f"'{key}' is not a valid field for source '{stype}'")

    for key in required:
        if not config.get(key):
            raise CollectionConfigError(f"source '{stype}' requires '{key}'")

    label = (source.get("label") or stype).strip()[:80]
    return {"type": stype, "label": label,
            "config": {k: config[k] for k in (required + optional) if k in config}}


def validate_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [validate_source(s) for s in sources]
