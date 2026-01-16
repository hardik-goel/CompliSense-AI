# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['agent/agent_ui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('rulepacks/euai_core_v1.yaml', 'rulepacks'),
        ('agent/report/templates', 'agent/report/templates'),
    ],
    hiddenimports=[
        'jinja2',
        'weasyprint',
        'pydyf',
        'tinycss2',
        'cssselect2'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
