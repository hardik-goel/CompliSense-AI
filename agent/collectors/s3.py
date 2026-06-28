"""AWS S3 artefact collector — read objects under a prefix (agent-side; bytes stay local).

Needs read-object permission on the bucket/prefix (broader than the metadata connector's
describe-only policy). Least-privilege read policy:

    {
      "Version": "2012-10-17",
      "Statement": [
        {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::BUCKET",
         "Condition": {"StringLike": {"s3:prefix": ["PREFIX*"]}}},
        {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::BUCKET/PREFIX*"}
      ]
    }
"""

from __future__ import annotations

import posixpath
from typing import Any, List, Optional

from agent.collectors.base import Candidate
from agent.collectors.extract import SUPPORTED_EXTS, extract_text

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_FILES = 200


def _ext_ok(key: str) -> bool:
    i = key.rfind(".")
    return i >= 0 and key[i:].lower() in SUPPORTED_EXTS


def collect_s3_candidates(bucket: str, prefix: str = "", region: Optional[str] = None,
                          client: Any = None, max_files: int = DEFAULT_MAX_FILES,
                          max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    """List objects under prefix, fetch supported text/PDF/DOCX, return candidates.

    `client` is an injectable boto3-style S3 client (for tests). Default lazy-imports boto3.
    """
    if not bucket:
        raise ValueError("bucket is required for the S3 collector")
    if client is None:
        import boto3  # lazy
        client = boto3.client("s3", region_name=region) if region else boto3.client("s3")

    out: List[Candidate] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            if len(out) >= max_files:
                return out
            key = obj.get("Key", "")
            size = obj.get("Size", 0)
            if key.endswith("/") or not _ext_ok(key) or size == 0 or size > max_bytes:
                continue
            body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
            sample = extract_text(body, posixpath.basename(key))
            if not sample.strip():
                continue
            out.append(Candidate(source="s3", ref=f"s3://{bucket}/{key}",
                                 filename=posixpath.basename(key), sample=sample, data=body))
    return out
