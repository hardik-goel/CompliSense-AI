from pathlib import Path
import shutil
import logging

try:
    import imgkit
except ImportError:
    imgkit = None


def export_dashboard_images(html_path: Path, out_dir: Path):
    """
    Exports dashboard screenshots if wkhtmltoimage is available.
    Safe to call in packaged apps.
    """

    if imgkit is None:
        logging.warning("imgkit not available, skipping dashboard screenshots")
        return None, None

    wkhtml = shutil.which("wkhtmltoimage")

    if not wkhtml:
        logging.warning(
            "wkhtmltoimage not found. "
            "Skipping dashboard image export."
        )
        return None, None

    png = out_dir / "dashboard.png"

    try:
        imgkit.from_file(
            str(html_path),
            str(png),
            config=imgkit.config(wkhtmltoimage=wkhtml)
        )
        return png, None

    except Exception as e:
        logging.warning(f"Dashboard image export failed: {e}")
        return None, None
