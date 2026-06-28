from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import certifi
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
        client_kwargs: dict[str, Any] = {"uuidRepresentation": "standard"}
        if settings.mongo_uri.startswith("mongodb+srv://") or "tls=true" in settings.mongo_uri.lower():
            client_kwargs["tlsCAFile"] = certifi.where()
        _client = MongoClient(settings.mongo_uri, **client_kwargs)
    return _client


def get_database() -> Database:
    return get_client()[settings.mongo_db]


def get_collection(name: str) -> Collection:
    return get_database()[name]


def ensure_indexes() -> None:
    users = get_collection("users")
    projects = get_collection("projects")
    scans = get_collection("scans")
    scan_runs = get_collection("scan_runs")
    monitor_alerts = get_collection("monitor_alerts")
    connector_discoveries = get_collection("connector_discoveries")
    pii_inferences = get_collection("pii_inferences")
    regulatory_snapshots = get_collection("regulatory_snapshots")
    regulatory_changes = get_collection("regulatory_changes")
    teams = get_collection("teams")
    team_members = get_collection("team_members")
    audit_logs = get_collection("audit_logs")

    users.create_index([("email", ASCENDING)], unique=True, name="uniq_user_email")
    users.create_index([("id", ASCENDING)], unique=True, name="uniq_user_id")

    projects.create_index([("id", ASCENDING)], unique=True, name="uniq_project_id")
    projects.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="projects_by_user")

    scans.create_index([("id", ASCENDING)], unique=True, name="uniq_scan_id")
    scans.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)], name="scans_by_project")
    scans.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="scans_by_user")

    scan_runs.create_index([("run_id", ASCENDING)], unique=True, name="uniq_run_id")
    scan_runs.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)], name="runs_by_project")
    scan_runs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="runs_by_user")

    monitor_alerts.create_index([("alert_id", ASCENDING)], unique=True, name="uniq_alert_id")
    monitor_alerts.create_index([("project_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="alerts_by_project")
    monitor_alerts.create_index([("dedupe_key", ASCENDING), ("status", ASCENDING)], name="alerts_dedupe")

    connector_discoveries.create_index([("discovery_id", ASCENDING)], unique=True, name="uniq_discovery_id")
    connector_discoveries.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)], name="discoveries_by_project")

    pii_inferences.create_index([("inference_id", ASCENDING)], unique=True, name="uniq_inference_id")
    pii_inferences.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)], name="pii_by_project")

    regulatory_snapshots.create_index([("url", ASCENDING), ("fetched_at", DESCENDING)], name="snapshots_by_url")
    regulatory_changes.create_index([("change_id", ASCENDING)], unique=True, name="uniq_change_id")
    regulatory_changes.create_index([("status", ASCENDING), ("detected_at", DESCENDING)], name="changes_by_status")

    teams.create_index([("id", ASCENDING)], unique=True, name="uniq_team_id")
    team_members.create_index([("team_id", ASCENDING), ("user_id", ASCENDING)], name="member_by_team_user")
    team_members.create_index([("user_id", ASCENDING)], name="members_by_user")

    audit_logs.create_index([("audit_id", ASCENDING)], unique=True, name="uniq_audit_id")
    audit_logs.create_index([("timestamp", DESCENDING)], name="audit_by_time")
    audit_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="audit_by_user")

    logger.info("MongoDB indexes ensured for users, projects, scans, scan_runs, monitor_alerts, connector_discoveries, pii_inferences, regulatory_snapshots/changes, teams/team_members, and audit_logs")


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
