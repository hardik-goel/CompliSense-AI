# saas/app/scan_manager.py

import uuid
import json
from pathlib import Path
from threading import Event
from saas.app.results import evaluate_rule

ARTEFACTS_DIR = Path("artefacts/compliance")


class ScanManager:
    def __init__(self):
        self.scans = {}

    def create_scan(self, project_id: str, user_id: str):
        scan_id = str(uuid.uuid4())
        self.scans[scan_id] = {
            "scan_id": scan_id,
            "project_id": project_id,
            "user_id": user_id,
            "status": "running",
            "files": [],
            "completed_units": 0,
            "total_units": 0,
            "cancel_event": Event(),
            "dashboard_url": f"/dashboard/{scan_id}"
        }
        return scan_id

    def get_state(self, scan_id):
        return self.scans.get(scan_id)

    def cancel(self, scan_id):
        self.scans[scan_id]["cancel_event"].set()

    def run_scan(self, scan_id):
        state = self.scans[scan_id]

        files = list(ARTEFACTS_DIR.glob("*.json"))
        rules = ["EUAI-ART9", "EUAI-ART10", "EUAI-ART11"]

        state["files"] = [
            {"path": f.name, "rules": {r: "pending" for r in rules}}
            for f in files
        ]

        state["total_units"] = len(files) * len(rules)

        for f in files:
            if state["cancel_event"].is_set():
                state["status"] = "cancelled"
                return

            artefact = json.loads(f.read_text())

            for rule in rules:
                if state["cancel_event"].is_set():
                    state["status"] = "cancelled"
                    return

                result = evaluate_rule(rule, artefact)

                file_entry = next(x for x in state["files"] if x["path"] == f.name)
                file_entry["rules"][rule] = result["status"]

                state["completed_units"] += 1

        state["status"] = "completed"


scan_manager = ScanManager()
