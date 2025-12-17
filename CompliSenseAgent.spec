# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

project_root = Path(SPECPATH).resolve()
agent_dir = project_root / "agent"
rulepacks_dir = project_root / "rulepacks"
artefacts_dir = project_root / "artefacts"

block_cipher = None

datas = [
    (str(rulepacks_dir), 'rulepacks'),
    (str(artefacts_dir), 'artefacts'),
]

hiddenimports = [
    'agent',
    'agent.rules',
    'agent.rules.loader',
    'agent.rules.evaluators',
    'agent.scanner',
    'agent.report',
    'agent.report.render',
    'agent.db',
    'agent.db.mongo',
    'rule_engine',
    'pydantic',
    'yaml',
    'jinja2',
    'weasyprint',
    'jsonschema',
    'pymongo',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'tkinter.ttk',
]

a = Analysis(
    ['agent_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'pytest', 'setuptools'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CompliSenseAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CompliSenseAgent',
)

app = BUNDLE(
    coll,
    name='CompliSenseAgent.app',
    icon=None,
    bundle_identifier='com.complisense.agent',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleDisplayName': 'CompliSense AI',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 CompliSense AI',
        'LSMinimumSystemVersion': '10.13.0',
    },
)
