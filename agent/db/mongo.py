# agent/db/mongo.py
from __future__ import annotations
import os
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, Optional

from pymongo import MongoClient, ASCENDING, IndexModel
from pymongo.collection import Collection


def get_mongo_client(uri: Optional[str] = None) -> MongoClient:
    """
    Build a MongoClient using env or provided URI.
    Defaults to local Mongo if not set.
    """
    uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri, uuidRepresentation="standard")


def get_collection(
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
    coll_name: Optional[str] = None,
) -> Collection:
    """
    Return a collection handle and ensure basic indexes exist.
    """
    client = client or get_mongo_client()
    db_name = db_name or os.getenv("MONGO_DB", "complisense")
    coll_name = coll_name or os.getenv("MONGO_COLLECTION", "findings")

    coll = client[db_name][coll_name]

    # Idempotent index creation
    coll.create_indexes(
        [
            IndexModel([("run_id", ASCENDING)], unique=True, name="uniq_run_id"),
            IndexModel([("created_at", ASCENDING)], name="created_at_idx"),
            IndexModel([("summary.failed", ASCENDING)], name="failed_count_idx"),
        ]
    )
    return coll


def insert_report(
    results: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    *,
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
    coll_name: Optional[str] = None,
) -> str:
    """
    Insert a scan result into MongoDB, returning the run_id.

    Args:
        results: The dict returned by run_scan (summary + results).
        metadata: Optional dict (e.g., run_id, pack_id, pack_version, project_root).
        client/db_name/coll_name: Optional overrides.

    Returns:
        run_id (str)
    """
    metadata = metadata or {}
    run_id = metadata.get("run_id") or str(uuid4())

    doc = {
        "run_id": run_id,
        "created_at": metadata.get("created_at") or datetime.utcnow(),
        "pack_id": metadata.get("pack_id"),
        "pack_version": metadata.get("pack_version"),
        "project_root": metadata.get("project_root"),
        "summary": results.get("summary", {}),
        "results": results.get("results", []),
        "raw": results,  # keep full payload for traceability
    }

    coll = get_collection(client=client, db_name=db_name, coll_name=coll_name)
    coll.insert_one(doc)
    return run_id
