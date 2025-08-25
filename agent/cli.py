"""
CLI entrypoint for the EU AI Act local compliance agent.
Provides commands to run audits against a given project using rulepacks.
"""

import json
import click
from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf

@click.group()
def cli():
    """
    Root command group for the EU AI Act local agent.

    This CLI allows users to run scans against a project directory
    using a rulepack YAML file. The scan produces structured JSON
    results and optionally renders them into a PDF audit report.
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
def scan(root, pack, out, pdf):
    """
    Run a compliance scan against a project using the given rulepack.

    Args:
        root (str): Path to the project artefacts root.
        pack (str): Path to the YAML rulepack file.
        out (str): Path to the output directory (created if not exists).
        pdf (bool): Whether to render a PDF report in addition to JSON.
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


if __name__ == "__main__":
    cli()
