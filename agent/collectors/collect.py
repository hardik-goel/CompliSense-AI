"""Collect orchestrator: crawl a local folder → classify → stage matched artefacts + manifest.

Runs entirely on the client machine. Files are copied into an output folder the local agent can
then scan; nothing is uploaded by this step. CLI:

    python -m agent.collectors.collect --source-path ./my_repo --out ./collected_artefacts
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any, Optional

from agent.collectors.artefact_types import TITLES
from agent.collectors.classifier import AnthropicClassifier, classify
from agent.collectors.local_folder import crawl

DEFAULT_MIN_CONFIDENCE = 0.6


def collect_local(source_path: str, out_dir: str, llm: Optional[Any] = None,
                  min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> dict[str, Any]:
    """Crawl source_path, classify each file, copy matches (>= min_confidence) into out_dir.

    Returns a manifest dict. Also writes COLLECTION_MANIFEST.json + READ_ME_FIRST.txt into out_dir.
    """
    candidates = crawl(source_path)
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    matched: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    used_names: set[str] = set()
    for c in candidates:
        result = classify(c.filename, c.sample, llm=llm)
        row = {"file": c.rel, "artefact_id": result.artefact_id, "title": TITLES.get(result.artefact_id),
               "confidence": result.confidence, "reason": result.reason, "method": result.method}
        if result.artefact_id and result.confidence >= min_confidence:
            dest_name = _unique(c.filename, used_names)
            shutil.copy2(c.path, out / dest_name)
            row["staged_as"] = dest_name
            matched.append(row)
        else:
            skipped.append(row)

    manifest = {
        "source_path": str(Path(source_path).resolve()),
        "output_path": str(out),
        "scanned": len(candidates),
        "collected": len(matched),
        "skipped": len(skipped),
        "min_confidence": min_confidence,
        "classifier": "llm" if (llm is not None and getattr(llm, "available", lambda: True)()) else "deterministic",
        "matched": matched,
        "skipped_files": skipped,
    }
    (out / "COLLECTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "READ_ME_FIRST.txt").write_text(_readme(manifest), encoding="utf-8")
    return manifest


def _unique(name: str, used: set[str]) -> str:
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


def _readme(m: dict[str, Any]) -> str:
    lines = [f"  - {x['staged_as']}  ->  {x['title']} ({x['confidence']})" for x in m["matched"]]
    return (
        "CompliSense-AI — collected artefacts\n"
        "====================================\n\n"
        f"Scanned {m['scanned']} files in {m['source_path']}\n"
        f"Collected {m['collected']} candidate artefacts (classifier: {m['classifier']}).\n\n"
        "These were AUTO-CLASSIFIED. Review COLLECTION_MANIFEST.json and remove anything wrong\n"
        "before scanning. Then run the agent on this folder:\n"
        "  python run_scan.py --project-path . --output-dir ./output\n\n"
        "Collected files:\n" + ("\n".join(lines) if lines else "  (none matched)") + "\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect compliance artefacts from a local folder")
    ap.add_argument("--source-path", required=True, help="Folder to crawl for existing artefacts")
    ap.add_argument("--out", default="./collected_artefacts", help="Where to stage matched files")
    ap.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE)
    ap.add_argument("--no-llm", action="store_true", help="Use the deterministic classifier only")
    args = ap.parse_args()

    src = Path(args.source_path)
    if not src.exists() or not src.is_dir():
        print(f"Error: source path is not a folder: {src}")
        return 1

    llm = None if args.no_llm else AnthropicClassifier()
    if llm is not None and not llm.available():
        print("No ANTHROPIC_API_KEY — using the deterministic classifier (filename + keywords).")
        llm = None
    m = collect_local(args.source_path, args.out, llm=llm, min_confidence=args.min_confidence)
    print(f"Scanned {m['scanned']}, collected {m['collected']} -> {m['output_path']}")
    print(f"Review {m['output_path']}/COLLECTION_MANIFEST.json before scanning.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
