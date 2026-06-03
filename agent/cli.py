"""
CLI entrypoint for the local compliance agent.
Provides commands to run audits against a given project using rulepacks.
"""

import json
import os
import sys
import click
import yaml
from pathlib import Path

from compliance.registry import DEFAULT_RULEPACK_ID
from compliance.registry import get_rulepack_display_label
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf
from agent.db.mongo import insert_report
from agent.scoring.overall import compute_overall_compliance, verdict_from_score


def _resource_path(rel_path: str) -> Path:
    """
    Resolve a path to a bundled resource. Works for PyInstaller onefile/onedir.
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel_path


def load_embedded_rulepack(pack_id: str) -> dict:
    """
    Load an embedded rulepack by id.
    The YAML files are bundled by PyInstaller under embedded_rulepacks/.
    """
    p = _resource_path(f"embedded_rulepacks/{pack_id}.yaml")
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8"))

    # Source/dev fallback: allow --pack-id to work from repo without PyInstaller.
    repo_rulepack = Path(__file__).resolve().parents[1] / "rulepacks" / f"{pack_id}.yaml"
    if repo_rulepack.exists():
        return yaml.safe_load(repo_rulepack.read_text(encoding="utf-8"))

    raise click.ClickException(
        "Embedded rulepack not found for pack_id="
        f"{pack_id}. Checked: {p} and {repo_rulepack}"
    )


import threading
import time

_spinner_stop = False
_spinner_thread = None

def _spin(text):
    global _spinner_stop
    chars = "|/-\\"
    idx = 0
    while not _spinner_stop:
        sys.stdout.write(f"\r{text} {chars[idx % len(chars)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)

def _cli_progress(event):
    global _spinner_stop, _spinner_thread
    etype = event.get("event")
    if etype == "RULE_START":
        idx = event.get("index")
        total = event.get("total")
        rule_id = event.get("rule_id")
        text = f"[{idx}/{total}] Running {rule_id}..."
        _spinner_stop = False
        _spinner_thread = threading.Thread(target=_spin, args=(text,))
        _spinner_thread.daemon = True
        _spinner_thread.start()
    elif etype == "RULE_END":
        _spinner_stop = True
        if _spinner_thread:
            _spinner_thread.join()
        status = event.get("status")
        idx = event.get("index")
        total = event.get("total")
        rule_id = event.get("rule_id")
        text = f"[{idx}/{total}] Running {rule_id}..."
        # Clear the spinner line and print final status
        sys.stdout.write(f"\r{text} {status}   \n")
        sys.stdout.flush()
    elif etype == "SCAN_COMPLETE":
        click.echo("Scan complete.")

@click.group()
def cli():
    """
    Root command group for the local compliance agent.
    """

@cli.command()
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="Path to the project root directory containing artefacts.",
)
@click.option(
    "--pack",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Optional path to a rule pack YAML file (dev/testing). If omitted, use embedded pack.",
)
@click.option(
    "--pack-id",
    type=str,
    required=False,
    default=DEFAULT_RULEPACK_ID,
    help="Embedded rulepack id to use when --pack is omitted.",
)
@click.option(
    "--out",
    type=click.Path(file_okay=False),
    default="out",
    help="Directory where output JSON and PDF files will be written.",
)
@click.option("--pdf/--no-pdf", default=True,
              help="Toggle PDF rendering of the audit report.")
@click.option("--mongo/--no-mongo", default=False,
              help="If set, also persist the results into MongoDB.")
@click.option("--mongo-uri", default=None,
              help="Override Mongo URI (else MONGO_URI env or localhost).")
@click.option("--mongo-db", default=None,
              help="Override Mongo DB name (else MONGO_DB env or 'complisense').")
@click.option("--mongo-coll", default=None,
              help="Override Mongo collection (else MONGO_COLLECTION env or 'findings').")
def scan(root, pack, pack_id, out, pdf, mongo, mongo_uri, mongo_db, mongo_coll):
    """
    Run a compliance scan against a project using the given rulepack.
    """
    root = Path(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    if pack:
        # Dev/test: load external YAML
        rp = load_rulepack(Path(pack))
    else:
        # Normal agent: use embedded rulepack selected by id
        rp = load_embedded_rulepack(pack_id or DEFAULT_RULEPACK_ID)

    results = run_scan(
        root,
        iter_rules(rp),
        required_artifacts_manifest=rp.get("required_artifacts_manifest"),
        progress_callback=_cli_progress,
    )

    # Compute assessment (like agent_runner does)
    artifacts = results["artifacts"]
    rule_results = results["results"]
    
    avg_rule_confidence = (
        sum(r["confidence"] for r in rule_results) / len(rule_results)
        if rule_results else 0
    )
    
    overall_compliance = compute_overall_compliance(
        artifacts_pct=artifacts["compliance_pct"],
        avg_rule_confidence=avg_rule_confidence
    )
    
    verdict = verdict_from_score(overall_compliance)
    
    assessment = {
        "verdict": verdict,
        "overall_compliance_pct": overall_compliance,
        "artifact_compliance_pct": artifacts["compliance_pct"],
        "avg_rule_confidence": round(avg_rule_confidence, 2),
        "why_not_compliant": {
            "missing_artifacts": [a.get("name", a.get("id", "unknown")) for a in artifacts.get("missing", [])],
            "failed_rules": [r["title"] for r in rule_results if r["status"] == "FAIL"]
        },
        "tier": "FREE"
    }

    report_context = {
        "rulepack_id": rp.get("pack_id") or (pack_id or DEFAULT_RULEPACK_ID),
        "rulepack_version": rp.get("version"),
        "program_label": get_rulepack_display_label(rp.get("pack_id") or (pack_id or DEFAULT_RULEPACK_ID)),
    }
    results["report_context"] = report_context

    # Save JSON report
    json_path = out / "findings.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    click.echo(f"Wrote {json_path}")

    # Optionally save PDF report
    if pdf:
        pdf_path = out / "audit_report.pdf"
        render_pdf(results, assessment, pdf_path)  # Fixed: now passes assessment
        click.echo(f"Wrote {pdf_path}")

    # Optionally persist to Mongo
    if mongo:
        # lightweight metadata for queryability
        metadata = {
            "pack_id": rp.get("pack_id"),
            "pack_version": rp.get("version"),
            "project_root": str(root),
        }
        # allow one-off override without changing env
        if mongo_uri:
            os.environ["MONGO_URI"] = mongo_uri
        if mongo_db:
            os.environ["MONGO_DB"] = mongo_db
        if mongo_coll:
            os.environ["MONGO_COLLECTION"] = mongo_coll

        run_id = insert_report(results, metadata)
        click.echo(f"Inserted into Mongo with run_id={run_id}")


if __name__ == "__main__":
    cli()
