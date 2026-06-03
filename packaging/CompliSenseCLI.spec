# complisensecli.spec
#
# PyInstaller spec file for the compiled CLI agent used in client distributions.

from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

project_root = Path(".").resolve()

# Collect cryptography's shared libraries (Rust extension) explicitly
crypto_bins = collect_dynamic_libs("cryptography")

a = Analysis(
    [str(project_root / "agent" / "cli.py")],
    pathex=[str(project_root)],
    binaries=crypto_bins,  # no tkinter needed for CLI
    datas=[
        # Embedded rulepacks
        (str(project_root / "rulepacks" / "euai_core_v1.yaml"), "embedded_rulepacks"),
        (str(project_root / "rulepacks" / "euai_extended_v1.yaml"), "embedded_rulepacks"),
        (str(project_root / "rulepacks" / "dpdp_india_core_v1.yaml"), "embedded_rulepacks"),
        (str(project_root / "rulepacks" / "dpdp_india_extended_v1.yaml"), "embedded_rulepacks"),

        # Report templates and artefacts
        (str(project_root / "agent" / "report" / "templates"), "agent/report/templates"),
        (str(project_root / "agent" / "artefacts"), "agent/artefacts"),
    ],
    hiddenimports=[
        "agent",
        "agent.rules.loader",
        "agent.scanner",
        "agent.report.render",
        "agent.db.mongo",
        "agent.scoring.overall",
        "jinja2",
        "weasyprint",
        "pydyf",
        "tinycss2",
        "cssselect2",
        *collect_submodules("agent.evaluators"),
        *collect_submodules("cryptography"),
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
