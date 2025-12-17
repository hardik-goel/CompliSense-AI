#!/bin/bash
# build_macos_app.sh - Build CompliSense Agent for macOS

set -e

echo "🔨 Building CompliSense Agent for macOS..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "agent_gui.py" ]; then
    echo "❌ Error: agent_gui.py not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec

# Create the spec file (you can also use the artifact I created above)
echo "📝 Generating PyInstaller spec..."
cat > CompliSenseAgent.spec << 'EOF'
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
EOF

# Build the app
echo "🔧 Building macOS app bundle..."
pyinstaller CompliSenseAgent.spec

# Check if build was successful
if [ -d "dist/CompliSenseAgent.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "=========================================="
    echo "App location: dist/CompliSenseAgent.app"
    echo ""
    echo "To test the app:"
    echo "  1. Remove quarantine: xattr -dr com.apple.quarantine dist/CompliSenseAgent.app"
    echo "  2. Double-click: open dist/CompliSenseAgent.app"
    echo ""
    echo "To create a distributable ZIP:"
    echo "  cd dist && zip -r CompliSenseAgent-macos.zip CompliSenseAgent.app"
    echo ""
else
    echo "❌ Build failed!"
    exit 1
fi