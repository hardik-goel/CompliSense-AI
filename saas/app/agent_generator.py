# [file name]: saas/app/agent_generator.py
"""
Agent generation service for CompliSense-AI
Creates customized agents for specific projects and scans
"""

import os
import zipfile
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import datetime


class AgentGenerator:
    def __init__(self, base_agent_path: Path):
        self.base_agent_path = base_agent_path
        self.temp_dir = Path(tempfile.gettempdir()) / "complisense_agents"
        self.temp_dir.mkdir(exist_ok=True)

    def create_custom_agent(self, scan_config: Dict[str, Any], user_info: Dict[str, Any]) -> Path:
        """
        Create a customized agent for a specific scan configuration

        Returns path to the generated agent ZIP file
        """
        scan_id = scan_config["id"]
        project_id = scan_config["project_id"]

        # Create temporary directory for this agent
        agent_temp_dir = self.temp_dir / f"agent_{scan_id}"
        if agent_temp_dir.exists():
            shutil.rmtree(agent_temp_dir)
        agent_temp_dir.mkdir(parents=True)

        try:
            # Copy base agent files
            self._copy_agent_files(agent_temp_dir)

            # Create configuration file
            self._create_agent_config(agent_temp_dir, scan_config, user_info)

            # Create customized main script
            self._create_custom_main_script(agent_temp_dir, scan_config)

            # Create installation script
            self._create_install_script(agent_temp_dir)

            # Create ZIP file
            zip_path = self._create_zip_file(agent_temp_dir, scan_id)

            return zip_path

        except Exception as e:
            # Cleanup on error
            if agent_temp_dir.exists():
                shutil.rmtree(agent_temp_dir)
            raise e

    def _copy_agent_files(self, target_dir: Path):
        """Copy the base agent files to target directory"""
        # Copy the entire agent directory structure
        # This would copy your existing TruthModule
        if self.base_agent_path.exists():
            # Copy main agent files
            for item in self.base_agent_path.iterdir():
                if item.name in ['.git', '__pycache__', 'tests']:
                    continue
                dest = target_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            # Create a minimal agent structure if base path doesn't exist
            self._create_minimal_agent(target_dir)

    def _create_minimal_agent(self, target_dir: Path):
        """Create a minimal agent structure for testing"""
        # Create basic directory structure
        (target_dir / "agent").mkdir()
        (target_dir / "rulepacks").mkdir()
        (target_dir / "artefacts").mkdir()

        # Create basic requirements
        requirements = """rule-engine
pydantic
pyyaml
jsonschema
click
fastapi
uvicorn
jinja2
weasyprint
pymongo
python-dotenv
requests
"""
        (target_dir / "requirements.txt").write_text(requirements)

    def _create_agent_config(self, target_dir: Path, scan_config: Dict[str, Any], user_info: Dict[str, Any]):
        """Create agent configuration file"""
        config = {
            "scan_id": scan_config["id"],
            "project_id": scan_config["project_id"],
            "user_id": user_info["id"],
            "scan_name": scan_config["scan_name"],
            "rulepack_version": scan_config["rulepack_version"],
            "custom_checks": scan_config["custom_checks"],
            "output_format": scan_config["output_format"],
            "saas_base_url": "http://localhost:8000",  # Should be configurable
            "created_at": datetime.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

        config_path = target_dir / "agent_config.json"
        config_path.write_text(json.dumps(config, indent=2))

    def _create_custom_main_script(self, target_dir: Path, scan_config: Dict[str, Any]):
        """Create customized main script for the agent"""
        main_script = f'''#!/usr/bin/env python3
"""
CompliSense-AI Local Agent
Customized for: {scan_config["scan_name"]}
Scan ID: {scan_config["id"]}
"""

import os
import sys
import json
import argparse
from pathlib import Path
import requests

# Add agent directory to path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

def load_config():
    """Load agent configuration"""
    config_path = agent_dir / "agent_config.json"
    with open(config_path) as f:
        return json.load(f)

def send_heartbeat(config, status):
    """Send heartbeat to SaaS platform"""
    try:
        requests.post(
            f"{{config['saas_base_url']}}/api/agent/heartbeat",
            json={{
                "scan_id": config["scan_id"],
                "status": status,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat()
            }}
        )
    except:
        pass  # Silently fail if SaaS is unreachable

def main():
    config = load_config()

    print("🧠 CompliSense-AI Local Agent")
    print("=" * 40)
    print(f"Scan: {{config['scan_name']}}")
    print(f"Rulepack: {{config['rulepack_version']}}")
    print("=" * 40)

    # Send starting heartbeat
    send_heartbeat(config, "starting")

    try:
        # Get project path from user
        parser = argparse.ArgumentParser(description='CompliSense-AI Compliance Scanner')
        parser.add_argument('--project-path', required=True, 
                          help='Path to your ML project directory')
        parser.add_argument('--output-dir', default='./complisense_output',
                          help='Output directory for reports')

        args = parser.parse_args()

        # Validate paths
        project_path = Path(args.project_path)
        output_dir = Path(args.output_dir)

        if not project_path.exists():
            print(f"❌ Error: Project path does not exist: {{project_path}}")
            return 1

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Project: {{project_path}}")
        print(f"📊 Output: {{output_dir}}")
        print()

        # Send running heartbeat
        send_heartbeat(config, "running")

        # Import and run the compliance scan
        try:
            from agent.rules.loader import load_rulepack, iter_rules
            from agent.scanner import run_scan
            from agent.report.render import render_pdf

            # Load rulepack
            rulepack_path = agent_dir / "rulepacks" / "euai_core_v1.yaml"
            if not rulepack_path.exists():
                # Use default rulepack
                rulepack_path = agent_dir / "rulepacks" / "default_rules.yaml"

            print("🔍 Running compliance scan...")
            rp = load_rulepack(rulepack_path)
            results = run_scan(project_path, iter_rules(rp))

            # Generate reports
            print("📄 Generating reports...")

            if "json" in config["output_format"]:
                json_path = output_dir / "compliance_findings.json"
                json_path.write_text(json.dumps(results, indent=2))
                print(f"✅ JSON report: {{json_path}}")

            if "pdf" in config["output_format"]:
                pdf_path = output_dir / "compliance_report.pdf"
                render_pdf(results, pdf_path)
                print(f"✅ PDF report: {{pdf_path}}")

            # Send completion results to SaaS
            try:
                summary = results.get("summary", {{}})
                requests.post(
                    f"{{config['saas_base_url']}}/api/agent/results",
                    json={{
                        "scan_id": config["scan_id"],
                        "status": "completed",
                        "summary": summary,
                        "results_count": len(results.get("results", [])),
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
                    }}
                )
            except:
                print("⚠️  Could not sync results with SaaS platform")

            print()
            print("🎉 Scan completed successfully!")
            print(f"📈 Results: {{summary.get('passed', 0)}} passed, {{summary.get('failed', 0)}} failed")

            send_heartbeat(config, "completed")

        except Exception as e:
            print(f"❌ Scan failed: {{str(e)}}")
            send_heartbeat(config, "failed")
            return 1

    except KeyboardInterrupt:
        print("\\n⏹️  Scan cancelled by user")
        send_heartbeat(config, "cancelled")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {{str(e)}}")
        send_heartbeat(config, "error")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

        main_path = target_dir / "run_scan.py"
        main_path.write_text(main_script)

        # Make executable on Unix-like systems
        try:
            os.chmod(main_path, 0o755)
        except:
            pass

    def _create_install_script(self, target_dir: Path):
        """Create installation script"""
        install_script = '''#!/bin/bash
echo "🧠 CompliSense-AI Agent Setup"
echo "=============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv complisense_env
source complisense_env/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "To run a compliance scan:"
echo "  source complisense_env/bin/activate"
echo "  python run_scan.py --project-path /path/to/your/ml/project --output-dir ./output"
echo ""
'''

        install_path = target_dir / "setup_agent.sh"
        install_path.write_text(install_script)

        # Create Windows batch file
        batch_script = '''@echo off
echo 🧠 CompliSense-AI Agent Setup
echo ==============================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed. Please install Python 3.8 or higher.
    exit /b 1
)

:: Create virtual environment
echo 📦 Setting up Python environment...
python -m venv complisense_env
call complisense_env\\Scripts\\activate.bat

:: Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Setup completed successfully!
echo.
echo To run a compliance scan:
echo   complisense_env\Scripts\activate.bat
echo   python run_scan.py --project-path "C:\path\to\your\ml\project" --output-dir "./output"
echo.
pause
'''

        batch_path = target_dir / "setup_agent.bat"
        batch_path.write_text(batch_script)

    def _create_zip_file(self, agent_dir: Path, scan_id: str) -> Path:
        """Create ZIP file of the agent"""
        zip_path = self.temp_dir / f"complisense_agent_{scan_id}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in agent_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(agent_dir)
                    zipf.write(file_path, arcname)

        return zip_path


# Singleton instance
# At the end of agent_generator.py

# Determine agent path dynamically
if os.getenv("AGENT_BASE_PATH"):
    base_path = Path(os.getenv("AGENT_BASE_PATH"))
else:
    # Try to find agent directory relative to this file
    current_dir = Path(__file__).parent
    base_path = current_dir.parent.parent / "agent"

    # If not found, use current directory
    if not base_path.exists():
        base_path = current_dir

agent_generator = AgentGenerator(base_path)