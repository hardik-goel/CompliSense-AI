import json
import click
from pathlib import Path
from agent.rules.loader import load_rulepack, iter_rules
from agent.scanner import run_scan
from agent.report.render import render_pdf

@click.group()
def cli():
    """EU AI Act local agent"""

@cli.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False), required=True, help="Project root")
@click.option("--pack", type=click.Path(exists=True, dir_okay=False), required=True, help="Rule pack YAML")
@click.option("--out", type=click.Path(file_okay=False), default="out", help="Output directory")
@click.option("--pdf/--no-pdf", default=True)
def scan(root, pack, out, pdf):
    root = Path(root); out = Path(out); out.mkdir(parents=True, exist_ok=True)
    rp = load_rulepack(Path(pack))
    results = run_scan(root, iter_rules(rp))
    json_path = out / "findings.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    click.echo(f"Wrote {json_path}")
    if pdf:
        pdf_path = out / "audit_report.pdf"
        render_pdf(results, pdf_path)
        click.echo(f"Wrote {pdf_path}")

if __name__ == "__main__":
    cli()
