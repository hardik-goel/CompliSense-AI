# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs

# collect_all returns a TUPLE in PyInstaller 6.x

a = Analysis(
    ['agent/agent_ui.py'],
    pathex=[],
    binaries=collect_dynamic_libs('_tkinter'),
    datas=[
        ('/usr/local/Cellar/tcl-tk@8/8.6.17/lib/tcl8.6', 'tcl'),
        ('/usr/local/Cellar/tcl-tk@8/8.6.17/lib/tk8.6', 'tk'),
        ('rulepacks/euai_core_v1.yaml', 'rulepacks'),
        ('agent/report/templates', 'agent/report/templates'),
        ('agent/artefacts/required_artifacts.yaml', 'agent/artefacts'),
    ],
    hiddenimports=[
        '_tkinter',
        'tkinter',
        'jinja2',
        'weasyprint',
        'pydyf',
        'tinycss2',
        'cssselect2'
    ],
    runtime_hooks=['hooks/runtime_tk_fix.py'],
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
    name='CompliSenseAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='CompliSenseAgent.app',
    icon=None,
    bundle_identifier=None,
)
