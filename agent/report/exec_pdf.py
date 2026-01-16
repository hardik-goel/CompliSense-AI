from pathlib import Path
from weasyprint import HTML


def export_exec_pdf(dashboard_html: Path, out_dir: Path):
    """
    Generates a one-page executive PDF from dashboard HTML.
    """
    pdf_path = out_dir / "executive_summary.pdf"

    HTML(filename=str(dashboard_html)).write_pdf(
        pdf_path,
        stylesheets=[]
    )

    return pdf_path
