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
from typing import Dict, Any
import shutil
import datetime

from compliance.registry import DEFAULT_RULEPACK_ID

class AgentGenerator:
    def __init__(self, base_agent_path: Path):
        self.base_agent_path = base_agent_path
        self.cli_binary = self.base_agent_path / "dist" / "CompliSenseCLI"
        self.agent_source_dir = self.base_agent_path / "agent"
        self.rulepacks_dir = self.base_agent_path / "rulepacks"
        self.temp_dir = Path(tempfile.gettempdir()) / "complisense_agents"
        self.temp_dir.mkdir(exist_ok=True)

    def create_custom_agent(
        self,
        scan_config: Dict[str, Any],
        user_info: Dict[str, Any],
        saas_base_url: str,
    ) -> Path:
        """
        Create a customized agent for a specific scan configuration

        Returns path to the generated agent ZIP file.
        Caches zip for 1 hour to avoid slow regeneration on repeated downloads.
        """
        scan_id = scan_config["id"]
        project_id = scan_config["project_id"]
        zip_path = self.temp_dir / f"complisense_agent_{scan_id}.zip"

        # Return cached zip if it exists and is recent (< 1 hour)
        if zip_path.exists():
            mtime = zip_path.stat().st_mtime
            age_seconds = datetime.datetime.now().timestamp() - mtime
            if age_seconds < 3600:  # 1 hour
                return zip_path

        # Create temporary directory for this agent
        agent_temp_dir = self.temp_dir / f"agent_{scan_id}"
        if agent_temp_dir.exists():
            shutil.rmtree(agent_temp_dir)
        agent_temp_dir.mkdir(parents=True)

        try:
            # Copy base agent files
            bundle_mode = self._copy_agent_files(agent_temp_dir)

            # Create configuration file
            self._create_agent_config(agent_temp_dir, scan_config, user_info, saas_base_url, bundle_mode)

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

    def _copy_agent_files(self, target_dir: Path) -> str:
        """
        Copy the agent files needed for the downloadable bundle.

        Prefer a compiled CLI when present, otherwise fall back to a portable
        source bundle so Render can still generate an agent package.
        """
        if self.cli_binary.exists():
            shutil.copy2(self.cli_binary, target_dir / "CompliSenseCLI")
            (target_dir / "requirements.txt").write_text("requests\n", encoding="utf-8")
            return "compiled"

        if not self.agent_source_dir.exists():
            raise RuntimeError(f"Agent source directory not found at {self.agent_source_dir}")
        if not self.rulepacks_dir.exists():
            raise RuntimeError(f"Rulepacks directory not found at {self.rulepacks_dir}")

        shutil.copytree(self.agent_source_dir, target_dir / "agent", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(self.rulepacks_dir, target_dir / "rulepacks", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        readme = """CompliSense-AI Portable Agent

This bundle was generated without a precompiled native CLI, so it runs from Python source.
Setup:
1. Install Python 3.10 or 3.11
2. Run ./setup_agent.sh on macOS/Linux or setup_agent.bat on Windows
3. Run python run_scan.py --project-path /path/to/project --output-dir ./output
"""
        (target_dir / "README.txt").write_text(readme, encoding="utf-8")

        requirements = """click==8.1.8
Jinja2==3.1.6
jsonschema==4.25.1
PyYAML==6.0.3
requests==2.32.5
rule-engine==4.5.3
weasyprint==66.0
"""
        (target_dir / "requirements.txt").write_text(requirements, encoding="utf-8")
        return "source"

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

    def _create_agent_config(
        self,
        target_dir: Path,
        scan_config: Dict[str, Any],
        user_info: Dict[str, Any],
        saas_base_url: str,
        bundle_mode: str,
    ):
        """Create agent configuration file"""
        config = {
            "scan_id": scan_config["id"],
            "project_id": scan_config["project_id"],
            "user_id": user_info["id"],
            "scan_name": scan_config["scan_name"],
            "rulepack_version": scan_config["rulepack_version"],
            "custom_checks": scan_config["custom_checks"],
            "output_format": scan_config["output_format"],
            "saas_base_url": saas_base_url,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "bundle_mode": bundle_mode,
        }

        config_path = target_dir / "agent_config.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

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

# Add agent directory to path (so `agent` package is importable)
agent_dir = Path(__file__).resolve().parent
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
        project_path_str = args.project_path
        if project_path_str.startswith("./") and (project_path_str[2:8] == "Users/" or project_path_str[2:].startswith("/")):
            project_path_str = "/" + project_path_str.lstrip("./")

        out_dir_str = args.output_dir
        if out_dir_str.startswith("./") and (out_dir_str[2:8] == "Users/" or out_dir_str[2:].startswith("/")):
            out_dir_str = "/" + out_dir_str.lstrip("./")

        project_path = Path(project_path_str).resolve()
        output_dir = Path(out_dir_str).resolve()

        if not project_path.exists():
            print(f"❌ Error: Project path does not exist: {{project_path}}")
            return 1

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Project: {{project_path}}")
        print(f"📊 Output: {{output_dir}}")
        print()

        # Send running heartbeat
        send_heartbeat(config, "running")

        try:
            cli_path = agent_dir / "CompliSenseCLI"
            results = None

            # If compiled CLI exists, use it only (no agent package import)
            if cli_path.exists():
                import subprocess
                # Clear macOS quarantine so Gatekeeper doesn't kill the binary (exit -9)
                if sys.platform == "darwin":
                    try:
                        subprocess.run(
                            ["xattr", "-d", "com.apple.quarantine", str(cli_path)],
                            capture_output=True, timeout=5
                        )
                    except Exception:
                        pass  # Ignore if xattr fails (e.g. no quarantine)

                    print("🔍 Running compliance scan via compiled CLI...")
                    rulepack_id = config.get("rulepack_version") or DEFAULT_RULEPACK_ID
                    cmd = [
                        str(cli_path),
                        "scan",
                        "--root",
                        str(project_path),
                        "--out",
                        str(output_dir),
                        "--pack-id",
                        rulepack_id,
                    ]
                    result = subprocess.run(cmd, check=False, cwd=str(agent_dir))

                if result.returncode != 0:
                    raise RuntimeError("CLI scan failed with exit code " + str(result.returncode))
                json_path = output_dir / "findings.json"
                if not json_path.exists():
                    json_path = output_dir / "compliance_findings.json"
                if not json_path.exists():
                    raise RuntimeError("CLI did not produce findings.json or compliance_findings.json")
                raw = json.loads(json_path.read_text())
                rule_list = raw.get("results", raw.get("findings", []))
                summary = raw.get("summary", {{}})
                if not summary and rule_list:
                    passed = sum(1 for r in rule_list if r.get("status") == "PASS")
                    summary = {{"passed": passed, "failed": len(rule_list) - passed}}
                results = {{"results": rule_list, "summary": summary, "artifacts": raw.get("artifacts", {{}})}}
            else:
                # Source-based: import agent and run
                from agent.rules.loader import load_rulepack, iter_rules
                from agent.scanner import run_scan
                from agent.report.render import render_pdf
                from agent.scoring.overall import compute_overall_compliance, verdict_from_score
                rulepack_name = (config.get("rulepack_version") or DEFAULT_RULEPACK_ID) + ".yaml"
                rulepack_path = agent_dir / "rulepacks" / rulepack_name
                if not rulepack_path.exists():
                    rulepack_path = agent_dir / "rulepacks" / f"{DEFAULT_RULEPACK_ID}.yaml"
                if not rulepack_path.exists():
                    raise RuntimeError("No rulepack found in downloaded agent bundle")
                print("🔍 Running compliance scan...")
                rp = load_rulepack(rulepack_path)
                results = run_scan(project_path, iter_rules(rp))

            # Common: build assessment (minimal for CLI-only)
            artifacts = results.get("artifacts", {{}})
            rule_results = results.get("results", [])
            avg_rule_confidence = (
                sum(r.get("confidence", 0) for r in rule_results) / len(rule_results)
                if rule_results else 0
            )
            if not cli_path.exists():
                overall_compliance = compute_overall_compliance(
                    artifacts_pct=artifacts.get("compliance_pct", 0),
                    avg_rule_confidence=avg_rule_confidence
                )
                verdict = verdict_from_score(overall_compliance)
            else:
                overall_compliance = avg_rule_confidence * 100.0 if rule_results else 0
                verdict = "PASS" if overall_compliance >= 70 else "FAIL"
            assessment = {{
                "verdict": verdict,
                "overall_compliance_pct": overall_compliance,
                "artifact_compliance_pct": artifacts.get("compliance_pct", 0),
                "avg_rule_confidence": round(avg_rule_confidence, 2),
                "why_not_compliant": {{
                    "missing_artifacts": [a.get("name", a.get("id", "unknown")) for a in artifacts.get("missing", [])],
                    "failed_rules": [r.get("title", "") for r in rule_results if r.get("status") == "FAIL"]
                }},
                "tier": "FREE"
            }}

            print("📄 Generating reports...")
            if "json" in config.get("output_format", ["json"]):
                out_json = output_dir / "compliance_findings.json"
                out_json.write_text(json.dumps(results, indent=2))
                print(f"✅ JSON report: {{out_json}}")
            if "pdf" in config.get("output_format", []) and not cli_path.exists():
                pdf_path = output_dir / "compliance_report.pdf"
                render_pdf(results, assessment, pdf_path)
                print(f"✅ PDF report: {{pdf_path}}")

            summary = results.get("summary", {{}})
            try:
                requests.post(
                    f"{{config['saas_base_url']}}/agent/results",
                    json={{
                        "scan_id": config["scan_id"],
                        "status": "completed",
                        "summary": summary,
                        "findings_json": results,
                        "results_count": len(results.get("results", [])),
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
                    }}
                )
            except Exception:
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
python -m pip install --upgrade pip
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
        
        # Make executable on Unix-like systems
        try:
            import stat
            install_path.chmod(install_path.stat().st_mode | stat.S_IEXEC)
        except Exception:
            # Fallback: try os.chmod
            try:
                import os
                os.chmod(str(install_path), 0o755)
            except Exception:
                pass  # If both fail, user can chmod manually

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
python -m pip install --upgrade pip
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

        launcher_script = '''#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "complisense_env" ]; then
  echo "Python environment not found. Running setup first..."
  bash setup_agent.sh
fi

source complisense_env/bin/activate
python run_scan.py "$@"
'''
        launcher_path = target_dir / "run_agent.sh"
        launcher_path.write_text(launcher_script)
        try:
            launcher_path.chmod(0o755)
        except Exception:
            pass

        batch_launcher = '''@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if not exist complisense_env (
  echo Python environment not found. Running setup first...
  call setup_agent.bat
)

call complisense_env\\Scripts\\activate.bat
python run_scan.py %*
'''
        launcher_bat_path = target_dir / "run_agent.bat"
        launcher_bat_path.write_text(batch_launcher)

    def _create_zip_file(self, agent_dir: Path, scan_id: str) -> Path:
        """Create ZIP file of the agent"""
        zip_path = self.temp_dir / f"complisense_agent_{scan_id}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in agent_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(agent_dir)
                    zipf.write(file_path, arcname)

        return zip_path


# Singleton instance - base path is project root
agent_generator = AgentGenerator(Path(__file__).resolve().parents[2])
