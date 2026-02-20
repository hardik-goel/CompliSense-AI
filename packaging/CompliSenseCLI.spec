# PyInstaller spec file for the compiled CLI agent used in client distributions.
#
# This bundles the `agent` package, rulepacks, and report templates into a
# single executable suitable for shipping to clients. It is complementary to
# the ZIP-based agent and is intended for production packaging to protect
# rule logic from casual inspection.

from PyInstaller.utils.hooks import collect_dynamic_libs
from pathlib import Path

# When PyInstaller executes this spec, __file__ is not defined.
# Assume this spec is run from the project root directory.
project_root = Path(".").resolve()

a = Analysis(
    [str(project_root / "agent" / "cli.py")],
    pathex=[str(project_root)],
    binaries=collect_dynamic_libs('_tkinter'),
    datas=[
        (str(project_root / "rulepacks"), "rulepacks"),
        (str(project_root / "agent" / "report" / "templates"), "agent/report/templates"),
        (str(project_root / "agent" / "artefacts"), "agent/artefacts"),
    ],
    hiddenimports=[
        "agent",
        "agent.rules.loader",
        "agent.scanner",
        "agent.report.render",
        "jinja2",
        "weasyprint",
        "pydyf",
        "tinycss2",
        "cssselect2",
    ],
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CompliSenseCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

