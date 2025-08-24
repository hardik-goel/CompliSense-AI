from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from datetime import datetime
from pathlib import Path
import json

def render_pdf(results: dict, out_path: Path):
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape()
    )
    tpl = env.get_template("audit_report.html.j2")
    html = tpl.render(now=datetime.utcnow().isoformat() + "Z", **results)
    HTML(string=html).write_pdf(str(out_path))
