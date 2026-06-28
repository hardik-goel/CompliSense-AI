"""Shared collector primitives: the Candidate type + the classify→stage pipeline.

Every source collector (local folder, S3, GCS, Azure Blob, GitHub, doc stores) produces a list
of Candidate objects; stage_candidates() then classifies each (LLM or deterministic) and copies
the matches into the output folder with a manifest. Keeping this common means sources only have
to fetch bytes — classification, staging, naming, and the manifest are written once.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from agent.collectors.artefact_types import TITLES
from agent.collectors.classifier import classify

DEFAULT_MIN_CONFIDENCE = 0.6


@dataclass
class Candidate:
    """A file fetched from some source, ready to classify."""
    source: str            # "local" | "s3" | "gcs" | "azure_blob" | "github" | "notion" | ...
    ref: str               # human-readable origin (path / key / url)
    filename: str          # basename used for classification + staging
    sample: str            # extracted text sample
    data: Optional[bytes] = field(default=None, repr=False)  # raw bytes to stage (None = sample-only)


def _unique(name: str, used: set) -> str:
    if name not in used:
        used.add(name)
        return name
    stem, dot, ext = name.partition(".")
    i = 2
    while f"{stem}_{i}{dot}{ext}" in used:
        i += 1
    final = f"{stem}_{i}{dot}{ext}"
    used.add(final)
    return final


def stage_candidates(candidates: List[Candidate], out_dir: str, llm: Optional[Any] = None,
                     min_confidence: float = DEFAULT_MIN_CONFIDENCE,
                     source_label: str = "") -> dict:
    """Classify each candidate; stage matches (>= min_confidence) into out_dir + write manifest."""
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    matched: List[dict] = []
    skipped: List[dict] = []
    used: set = set()

    for c in candidates:
        result = classify(c.filename, c.sample, llm=llm)
        row = {"ref": c.ref, "source": c.source, "artefact_id": result.artefact_id,
               "title": TITLES.get(result.artefact_id), "confidence": result.confidence,
               "reason": result.reason, "method": result.method}
        if result.artefact_id and result.confidence >= min_confidence and c.data is not None:
            dest = _unique(c.filename, used)
            (out / dest).write_bytes(c.data)
            row["staged_as"] = dest
            matched.append(row)
        else:
            if result.artefact_id and result.confidence >= min_confidence and c.data is None:
                row["note"] = "matched but no bytes to stage (sample-only)"
            skipped.append(row)

    classifier = "llm" if (llm is not None and getattr(llm, "available", lambda: True)()) else "deterministic"
    manifest = {
        "source": source_label or (candidates[0].source if candidates else "unknown"),
        "output_path": str(out),
        "scanned": len(candidates),
        "collected": len(matched),
        "skipped": len(skipped),
        "min_confidence": min_confidence,
        "classifier": classifier,
        "matched": matched,
        "skipped_files": skipped,
    }
    (out / "COLLECTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "READ_ME_FIRST.txt").write_text(_readme(manifest), encoding="utf-8")
    return manifest


def _readme(m: dict) -> str:
    lines = [f"  - {x['staged_as']}  ->  {x['title']} ({x['confidence']})" for x in m["matched"]]
    return (
        "CompliSense-AI — collected artefacts\n"
        "====================================\n\n"
        f"Source: {m['source']}\n"
        f"Scanned {m['scanned']} files, collected {m['collected']} "
        f"(classifier: {m['classifier']}).\n\n"
        "These were AUTO-CLASSIFIED. Review COLLECTION_MANIFEST.json and remove anything wrong\n"
        "before scanning. Then run the agent on this folder:\n"
        "  python run_scan.py --project-path . --output-dir ./output\n\n"
        "Collected files:\n" + ("\n".join(lines) if lines else "  (none matched)") + "\n"
    )
