"""Collect orchestrator: fetch candidates from a source → classify → stage matches + manifest.

Runs entirely on the client machine. Files are copied into an output folder the local agent can
then scan; nothing is uploaded by this step. Sources: local | s3 | gcs | azure_blob | github |
notion | gdrive | sharepoint. CLI examples:

    python -m agent.collectors.collect --source local  --source-path ./my_repo --out ./collected
    python -m agent.collectors.collect --source s3     --bucket my-bkt --prefix docs/ --out ./collected
    python -m agent.collectors.collect --source github --repo org/name --path docs --out ./collected
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, List, Optional

from agent.collectors.base import DEFAULT_MIN_CONFIDENCE, Candidate, stage_candidates
from agent.collectors.classifier import AnthropicClassifier
from agent.collectors.local_folder import crawl


def collect_local(source_path: str, out_dir: str, llm: Optional[Any] = None,
                  min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> dict:
    """Crawl a local folder and stage matched artefacts."""
    return stage_candidates(crawl(source_path), out_dir, llm=llm,
                            min_confidence=min_confidence, source_label="local")


def collect_candidates(candidates: List[Candidate], out_dir: str, llm: Optional[Any] = None,
                       min_confidence: float = DEFAULT_MIN_CONFIDENCE, source_label: str = "") -> dict:
    """Stage an already-fetched candidate list (used by the cloud/doc-store collectors)."""
    return stage_candidates(candidates, out_dir, llm=llm,
                            min_confidence=min_confidence, source_label=source_label)


def _resolve_llm(no_llm: bool):
    if no_llm:
        return None
    llm = AnthropicClassifier()
    if not llm.available():
        print("No ANTHROPIC_API_KEY — using the deterministic classifier (filename + keywords).")
        return None
    return llm


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect compliance artefacts from a source")
    ap.add_argument("--source", default="local",
                    choices=["local", "s3", "gcs", "azure_blob", "github", "notion", "gdrive", "sharepoint"])
    ap.add_argument("--out", default="./collected_artefacts")
    ap.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE)
    ap.add_argument("--no-llm", action="store_true", help="Use the deterministic classifier only")
    # local
    ap.add_argument("--source-path", help="local: folder to crawl")
    # object stores
    ap.add_argument("--bucket", help="s3/gcs/azure_blob: bucket/container name")
    ap.add_argument("--prefix", default="", help="s3/gcs/azure_blob: key prefix")
    ap.add_argument("--region", help="s3: region")
    ap.add_argument("--account-url", help="azure_blob: https://<account>.blob.core.windows.net")
    # github
    ap.add_argument("--repo", help="github: owner/name")
    ap.add_argument("--path", default="", help="github/gdrive: path/folder within the source")
    ap.add_argument("--ref", default=None, help="github: branch/tag/sha")
    ap.add_argument("--token", default=None, help="github/notion/gdrive/sharepoint: access token (or use env)")
    # doc stores
    ap.add_argument("--database-id", help="notion: database id")
    ap.add_argument("--site", help="sharepoint: site id/path")
    args = ap.parse_args()

    llm = _resolve_llm(args.no_llm)
    src = args.source

    if src == "local":
        if not args.source_path or not Path(args.source_path).is_dir():
            print(f"Error: --source-path is not a folder: {args.source_path}"); return 1
        m = collect_local(args.source_path, args.out, llm=llm, min_confidence=args.min_confidence)
    else:
        cands = _fetch(src, args)
        m = collect_candidates(cands, args.out, llm=llm,
                               min_confidence=args.min_confidence, source_label=src)

    print(f"[{src}] scanned {m['scanned']}, collected {m['collected']} -> {m['output_path']}")
    print(f"Review {m['output_path']}/COLLECTION_MANIFEST.json before scanning.")
    return 0


def _fetch(src: str, args) -> List[Candidate]:
    """Lazy-import the right source collector and return candidates."""
    if src == "s3":
        from agent.collectors.s3 import collect_s3_candidates
        return collect_s3_candidates(args.bucket, prefix=args.prefix, region=args.region)
    if src == "gcs":
        from agent.collectors.gcs import collect_gcs_candidates
        return collect_gcs_candidates(args.bucket, prefix=args.prefix)
    if src == "azure_blob":
        from agent.collectors.azure_blob import collect_azure_candidates
        return collect_azure_candidates(args.account_url, args.bucket, prefix=args.prefix)
    if src == "github":
        from agent.collectors.github import collect_github_candidates
        return collect_github_candidates(args.repo, path=args.path, ref=args.ref, token=args.token)
    if src in ("notion", "gdrive", "sharepoint"):
        from agent.collectors.docstores import collect_docstore_candidates
        return collect_docstore_candidates(src, args)
    return []


if __name__ == "__main__":
    raise SystemExit(main())
