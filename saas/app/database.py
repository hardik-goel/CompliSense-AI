from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from saas.app.config import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri, uuidRepresentation="standard")
    return _client


def get_database() -> Database:
    return get_client()[settings.mongo_db]


def get_collection(name: str) -> Collection:
    return get_database()[name]


def ensure_indexes() -> None:
    users = get_collection("users")
    projects = get_collection("projects")
    scans = get_collection("scans")
    audit_logs = get_collection("audit_logs")

    users.create_index([("email", ASCENDING)], unique=True, name="uniq_user_email")
    users.create_index([("id", ASCENDING)], unique=True, name="uniq_user_id")

    projects.create_index([("id", ASCENDING)], unique=True, name="uniq_project_id")
    projects.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="projects_by_user")

    scans.create_index([("id", ASCENDING)], unique=True, name="uniq_scan_id")
    scans.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)], name="scans_by_project")
    scans.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="scans_by_user")

    audit_logs.create_index([("audit_id", ASCENDING)], unique=True, name="uniq_audit_id")
    audit_logs.create_index([("timestamp", DESCENDING)], name="audit_by_time")
    audit_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="audit_by_user")

    logger.info("MongoDB indexes ensured for users, projects, scans, and audit_logs")


def ping_database() -> None:
    get_client().admin.command("ping")


def serialize_document(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_document(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_document(item) for key, item in value.items() if key != "_id"}
    return value

