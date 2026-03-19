"""
Module for rendering audit results into PDF format using Jinja2 and WeasyPrint.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from datetime import datetime
from pathlib import Path


def render_pdf(results: dict, assessment: dict, out_path: Path):
    """
    Render a PDF audit report from scan results.

    Args:
        results (dict): Scan results, including summary and detailed rule outcomes.
        out_path (Path): Destination path where the PDF will be written.
    """
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape()
    )
    tpl = env.get_template("audit_report.html.j2")

    html = tpl.render(now=datetime.utcnow().isoformat() + "Z",assessment=assessment, **results)
    HTML(string=html).write_pdf(str(out_path))
