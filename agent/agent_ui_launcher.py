#!/usr/bin/env python3
"""
Launcher for agent_ui that bypasses macOS version checks.
Run this instead of agent_ui directly if you encounter macOS version errors.
"""
import os
import sys

# Set macOS deployment target to bypass version checks
if sys.platform == 'darwin':
    os.environ['MACOSX_DEPLOYMENT_TARGET'] = '10.15'  # macOS Catalina or later

# Suppress macOS version warnings
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Now import and run the UI
from agent.agent_ui import run

if __name__ == "__main__":
    run()
