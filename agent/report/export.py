from pathlib import Path
import subprocess


def export_dashboard(html_path: Path, out_dir: Path):
    pdf = out_dir / "dashboard.pdf"
    png = out_dir / "dashboard.png"

    subprocess.run([
        "npx", "playwright", "pdf",
        str(html_path),
        str(pdf)
    ], check=False)

    subprocess.run([
        "npx", "playwright", "screenshot",
        str(html_path),
        str(png),
        "--full-page"
    ], check=False)

    return pdf, png
