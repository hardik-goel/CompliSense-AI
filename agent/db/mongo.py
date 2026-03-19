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
    if coll_name == "findings":
        coll.create_indexes(
            [
                IndexModel([("run_id", ASCENDING)], unique=True, name="uniq_run_id"),
                IndexModel([("created_at", ASCENDING)], name="created_at_idx"),
                IndexModel([("summary.failed", ASCENDING)], name="failed_count_idx"),
            ]
        )
    elif coll_name == "audit_logs":
        coll.create_indexes(
            [
                IndexModel([("audit_id", ASCENDING)], unique=True, name="uniq_audit_id"),
                IndexModel([("timestamp", ASCENDING)], name="ts_idx"),
                IndexModel([("user_id", ASCENDING)], name="user_idx"),
                IndexModel([("scan_id", ASCENDING)], name="scan_idx"),
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


def insert_audit_log(
    event: Dict[str, Any],
    *,
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
    coll_name: str = "audit_logs",
) -> str:
    """
    Insert an audit log entry capturing who ran what, when, and with which rules.

    Expected event keys (all optional but recommended):
      - user_id
      - project_id
      - scan_id
      - rulepack_version
      - status
      - source ("agent_results", "agent_heartbeat", etc.)
      - metadata (dict with summary counts only)
    """
    audit_id = event.get("audit_id") or str(uuid4())
    doc = {
        "audit_id": audit_id,
        "timestamp": event.get("timestamp") or datetime.utcnow(),
        "user_id": event.get("user_id"),
        "project_id": event.get("project_id"),
        "scan_id": event.get("scan_id"),
        "rulepack_version": event.get("rulepack_version"),
        "status": event.get("status"),
        "source": event.get("source"),
        "metadata": event.get("metadata", {}),
    }

    coll = get_collection(client=client, db_name=db_name, coll_name=coll_name)
    coll.insert_one(doc)
    return audit_id


def list_audit_logs(
    *,
    user_id: Optional[str] = None,
    limit: int = 100,
    client: Optional[MongoClient] = None,
    db_name: Optional[str] = None,
    coll_name: str = "audit_logs",
) -> list:
    """
    List audit log entries, optionally filtered by user_id.
    Returns most recent first.
    """
    coll = get_collection(client=client, db_name=db_name, coll_name=coll_name)
    query = {}
    if user_id is not None:
        query["user_id"] = user_id
    cursor = coll.find(query).sort("timestamp", -1).limit(limit)
    docs = list(cursor)
    # Convert ObjectId and datetime for JSON
    out = []
    for d in docs:
        d.pop("_id", None)
        ts = d.get("timestamp")
        if hasattr(ts, "isoformat"):
            d["timestamp"] = ts.isoformat()
        out.append(d)
    return out
