from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader

def render_dashboard(findings: dict, out_dir: Path):
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates")
    )
    tpl = env.get_template("dashboard.html.j2")
    html = tpl.render(**findings)
    out_path = out_dir / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
