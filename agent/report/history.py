import json
from pathlib import Path


def load_runs(base_dir: Path):
    """
    Loads historical runs from:
    <out_dir>/run_*/findings.json
    """
    runs = []

    for run_dir in sorted(base_dir.glob("run_*")):
        findings_path = run_dir / "findings.json"

        if not findings_path.exists():
            continue

        data = json.loads(findings_path.read_text())

        runs.append({
            "run_id": run_dir.name,
            "summary": data.get("summary", {}),
            "results": data.get("results", [])
        })

    return runs


def compare_runs(old, new):
    def normalize(results):
        if isinstance(results, dict):
            return results.get("results", [])
        if isinstance(results, list):
            return results
        return []

    old_results = normalize(old.get("results"))
    new_results = normalize(new.get("results"))

    old_status = {r["rule_id"]: r["status"] for r in old_results}
    new_status = {r["rule_id"]: r["status"] for r in new_results}

    regressions = []
    improvements = []

    for rule_id, status in new_status.items():
        if rule_id not in old_status:
            continue

        if old_status[rule_id] == "PASS" and status == "FAIL":
            regressions.append(rule_id)
        elif old_status[rule_id] == "FAIL" and status == "PASS":
            improvements.append(rule_id)

    return {
        "regressions": regressions,
        "improvements": improvements
    }
