"""
Module for rendering audit results into PDF format using Jinja2 and WeasyPrint.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape, ChainableUndefined
from weasyprint import HTML
from datetime import datetime
from pathlib import Path


def render_pdf(results: dict, assessment=None, out_path: Path = None):
    """
    Render a PDF audit report from scan results.

    Supports two call forms for backward compatibility:
      - render_pdf(results, assessment, out_path)   # full form
      - render_pdf(results, out_path)               # legacy 2-arg form (assessment omitted)

    Args:
        results (dict): Scan results, including summary and detailed rule outcomes.
        assessment (dict | None): Optional readiness assessment block.
        out_path (Path): Destination path where the PDF will be written.
    """
    # Legacy 2-arg form: the second positional was actually the output path.
    if out_path is None:
        out_path, assessment = assessment, None

    # The template references several assessment fields. When a caller omits the
    # assessment (legacy 2-arg form), synthesize a safe, honest default so rendering
    # never breaks and no fabricated numbers are shown.
    assessment = _with_assessment_defaults(assessment)

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(),
        # Optional/absent result fields (e.g. evidence on NOT_APPLICABLE rows) render
        # blank instead of crashing the whole report.
        undefined=ChainableUndefined,
    )
    tpl = env.get_template("audit_report.html.j2")

    html = tpl.render(now=datetime.utcnow().isoformat() + "Z", assessment=assessment, **results)
    HTML(string=html).write_pdf(str(out_path))


def _with_assessment_defaults(assessment) -> dict:
    """Fill in the assessment fields the template needs, without inventing scores.

    Missing numeric fields render as "N/A" rather than a fabricated number.
    """
    a = dict(assessment or {})
    a.setdefault("verdict", "NOT ASSESSED")
    a.setdefault("overall_compliance_pct", "N/A")
    a.setdefault("avg_rule_confidence", "N/A")
    wnc = dict(a.get("why_not_compliant") or {})
    wnc.setdefault("missing_artifacts", [])
    wnc.setdefault("failed_rules", [])
    a["why_not_compliant"] = wnc
    return a
