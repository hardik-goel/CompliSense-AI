# cli.py
"""
CLI entrypoint for the EU AI Act local compliance agent.
Provides commands to run audits against a given project using rulepacks.
"""

import json
import os
import click
from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf
from agent.db.mongo import insert_report


@click.group()
def cli():
    """
    Root command group for the EU AI Act local agent.
    """


@cli.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False), required=True,
              help="Path to the project root directory containing artefacts.")
@click.option("--pack", type=click.Path(exists=True, dir_okay=False), required=True,
              help="Path to the rule pack YAML file to be loaded.")
@click.option("--out", type=click.Path(file_okay=False), default="out",
              help="Directory where output JSON and PDF files will be written.")
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
def scan(root, pack, out, pdf, mongo, mongo_uri, mongo_db, mongo_coll):
    """
    Run a compliance scan against a project using the given rulepack.
    """
    root = Path(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    rp = load_rulepack(Path(pack))
    results = run_scan(root, iter_rules(rp))

    # Save JSON report
    json_path = out / "findings.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    click.echo(f"Wrote {json_path}")

    # Optionally save PDF report
    if pdf:
        pdf_path = out / "audit_report.pdf"
        render_pdf(results, pdf_path)
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
