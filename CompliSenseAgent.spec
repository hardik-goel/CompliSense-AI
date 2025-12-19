# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['agent/agent_ui.py'],
    pathex=['.'],
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
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CompliSenseAgent',
    console=False,
)

app = BUNDLE(
    exe,
    name='CompliSenseAgent.app',
    bundle_identifier='ai.complisense.agent',
)
