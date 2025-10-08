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
import base64
import pickle


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
            # Create secure agent structure
            self._create_secure_agent_structure(agent_temp_dir)

            # Create configuration file
            self._create_agent_config(agent_temp_dir, scan_config, user_info)

            # Create secure main script with embedded rule engine
            self._create_secure_main_script(agent_temp_dir, scan_config)

            # Create installation script
            self._create_install_script(agent_temp_dir)

            # Create README file
            self._create_readme_file(agent_temp_dir, scan_config, user_info)

            # Create ZIP file
            zip_path = self._create_zip_file(agent_temp_dir, scan_id)

            return zip_path

        except Exception as e:
            # Cleanup on error
            if agent_temp_dir.exists():
                shutil.rmtree(agent_temp_dir)
            raise e

    def _create_secure_agent_structure(self, target_dir: Path):
        """Create a secure agent structure without exposing source code"""
        # Create necessary directories
        (target_dir / "config").mkdir()
        (target_dir / "output").mkdir()
        (target_dir / "cache").mkdir()

        # Create minimal requirements - only public dependencies
        requirements = """requests>=2.28.0
pyyaml>=6.0
jsonschema>=4.17.0
python-dotenv>=1.0.0
click>=8.1.0
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
            "custom_checks": scan_config.get("custom_checks", []),
            "output_format": scan_config.get("output_format", ["json"]),
            "saas_base_url": os.getenv("SAAS_BASE_URL", "https://api.complisense.ai"),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "license_key": user_info.get("license_key", ""),
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
        }

        config_path = target_dir / "config" / "agent_config.json"
        config_path.write_text(json.dumps(config, indent=2))

    def _compile_rules_to_bytecode(self, scan_config: Dict[str, Any]) -> bytes:
        """
        Compile rules to bytecode to protect IP
        This would interface with your rule compilation service
        """
        # This is where you'd compile your rules to a secure format
        # For now, we'll create a minimal rule structure
        compiled_rules = {
            "version": scan_config["rulepack_version"],
            "rules": scan_config.get("custom_checks", []),
            "compiled_at": datetime.datetime.utcnow().isoformat(),
            "checksum": "secure_hash_here"  # Add actual checksum
        }

        # Serialize and optionally encrypt
        rule_data = pickle.dumps(compiled_rules)
        return base64.b64encode(rule_data).decode('utf-8')

    def _create_secure_main_script(self, target_dir: Path, scan_config: Dict[str, Any]):
        """Create secure main script with embedded rule engine"""

        # Compile rules to protected format
        compiled_rules_b64 = self._compile_rules_to_bytecode(scan_config)

        main_script = f'''#!/usr/bin/env python3
"""
CompliSense-AI Secure Local Agent
Customized for: {scan_config["scan_name"]}
Scan ID: {scan_config["id"]}

This agent contains compiled rule definitions and communicates
with CompliSense-AI cloud services for processing.
"""

import os
import sys
import json
import argparse
import base64
import pickle
import hashlib
from pathlib import Path
import requests
import yaml
import jsonschema
from datetime import datetime

class SecureRuleEngine:
    """Secure rule engine that validates and executes compiled rules"""

    def __init__(self, compiled_rules_b64):
        self.rules = self._load_compiled_rules(compiled_rules_b64)
        self.validation_schema = {{
            "type": "object",
            "properties": {{
                "files": {{"type": "array"}},
                "dependencies": {{"type": "array"}},
                "config": {{"type": "object"}}
            }}
        }}

    def _load_compiled_rules(self, rules_b64):
        """Load and validate compiled rules"""
        try:
            rules_data = base64.b64decode(rules_b64)
            rules = pickle.loads(rules_data)

            # Validate rules structure
            if not isinstance(rules, dict) or 'rules' not in rules:
                raise ValueError("Invalid compiled rules format")

            return rules
        except Exception as e:
            raise RuntimeError(f"Failed to load rules: {{str(e)}}")

    def scan_file(self, file_path, content):
        """Scan a single file using compiled rules"""
        findings = []

        for rule in self.rules.get('rules', []):
            try:
                # Apply rule logic (this would be your actual rule processing)
                if self._check_rule(rule, file_path, content):
                    findings.append({{
                        "rule_id": rule.get('id'),
                        "file": str(file_path),
                        "line": 0,
                        "severity": rule.get('severity', 'medium'),
                        "message": rule.get('description', ''),
                        "category": rule.get('category', 'security')
                    }})
            except Exception as e:
                # Log but continue with other rules
                print(f"Rule {{rule.get('id')}} failed: {{str(e)}}")

        return findings

    def _check_rule(self, rule, file_path, content):
        """Check a single rule against file content"""
        # This is where your rule logic would execute
        # For demo purposes, we'll do simple checks
        rule_type = rule.get('type', 'content')

        if rule_type == 'content':
            pattern = rule.get('pattern', '')
            if pattern and pattern in content:
                return True

        elif rule_type == 'file_extension':
            extensions = rule.get('extensions', [])
            if any(file_path.suffix == ext for ext in extensions):
                return True

        return False

class ProjectScanner:
    """Scans ML project directory"""

    def __init__(self, rule_engine):
        self.rule_engine = rule_engine
        self.supported_extensions = ['.py', '.yaml', '.yml', '.json', '.md', '.txt']

    def scan_project(self, project_path):
        """Scan entire project directory"""
        project_path = Path(project_path)
        all_findings = []
        scanned_files = 0

        for ext in self.supported_extensions:
            for file_path in project_path.rglob(f'*{{ext}}'):
                if self._should_scan_file(file_path):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        findings = self.rule_engine.scan_file(file_path, content)
                        all_findings.extend(findings)
                        scanned_files += 1
                    except Exception as e:
                        print(f"Failed to scan {{file_path}}: {{str(e)}}")

        return {{
            "summary": {{
                "scanned_files": scanned_files,
                "total_findings": len(all_findings),
                "timestamp": datetime.utcnow().isoformat()
            }},
            "findings": all_findings
        }}

    def _should_scan_file(self, file_path):
        """Check if file should be scanned"""
        # Skip virtual environments, cache directories, etc.
        exclude_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 
            'node_modules', '.pytest_cache', '.mypy_cache'
        ]

        return not any(pattern in str(file_path) for pattern in exclude_patterns)

def load_config():
    """Load agent configuration"""
    config_path = Path(__file__).parent / "config" / "agent_config.json"
    with open(config_path) as f:
        return json.load(f)

def validate_license(config):
    """Validate agent license"""
    try:
        # Check expiration
        expires_at = datetime.fromisoformat(config['expires_at'])
        if datetime.utcnow() > expires_at:
            return False, "License expired"

        # Here you would validate with your SaaS platform
        return True, "Valid"
    except:
        return False, "Invalid license"

def send_heartbeat(config, status, message=""):
    """Send heartbeat to SaaS platform"""
    try:
        requests.post(
            f"{{config['saas_base_url']}}/api/agent/heartbeat",
            json={{
                "scan_id": config["scan_id"],
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }},
            timeout=10
        )
    except Exception as e:
        print(f"⚠️  Heartbeat failed: {{str(e)}}")

def main():
    config = load_config()

    # Validate license
    is_valid, license_msg = validate_license(config)
    if not is_valid:
        print(f"❌ License validation failed: {{license_msg}}")
        return 1

    print("🧠 CompliSense-AI Secure Local Agent")
    print("=" * 50)
    print(f"Scan: {{config['scan_name']}}")
    print(f"Rulepack: {{config['rulepack_version']}}")
    print(f"License: {{license_msg}}")
    print("=" * 50)

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
            send_heartbeat(config, "failed", "Project path does not exist")
            return 1

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Project: {{project_path}}")
        print(f"📊 Output: {{output_dir}}")
        print()

        # Send running heartbeat
        send_heartbeat(config, "running")

        # Initialize secure rule engine with compiled rules
        print("🔒 Initializing secure rule engine...")
        rule_engine = SecureRuleEngine("{compiled_rules_b64}")
        scanner = ProjectScanner(rule_engine)

        print("🔍 Scanning project...")
        results = scanner.scan_project(project_path)

        # Generate reports
        print("📄 Generating reports...")

        # JSON output
        json_path = output_dir / "compliance_findings.json"
        json_path.write_text(json.dumps(results, indent=2))
        print(f"✅ JSON report: {{json_path}}")

        # Summary output
        summary = results.get("summary", {{}})
        findings_count = len(results.get("findings", []))

        print(f"📈 Scan completed: {{summary.get('scanned_files', 0)}} files scanned, {{findings_count}} findings")

        # Send completion results to SaaS
        try:
            requests.post(
                f"{{config['saas_base_url']}}/api/agent/results",
                json={{
                    "scan_id": config["scan_id"],
                    "status": "completed",
                    "summary": summary,
                    "findings_count": findings_count,
                    "timestamp": datetime.utcnow().isoformat()
                }},
                timeout=30
            )
            print("✅ Results synced with CompliSense-AI platform")
        except Exception as e:
            print(f"⚠️  Could not sync results: {{str(e)}}")

        send_heartbeat(config, "completed")
        print("🎉 Scan completed successfully!")

    except KeyboardInterrupt:
        print("\\n⏹️  Scan cancelled by user")
        send_heartbeat(config, "cancelled")
        return 1
    except Exception as e:
        print(f"❌ Scan failed: {{str(e)}}")
        send_heartbeat(config, "failed", str(e))
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
echo "🧠 CompliSense-AI Secure Agent Setup"
echo "====================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Using Python $PYTHON_VERSION"

# Create virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv complisense_env
source complisense_env/bin/activate

# Upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip

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
echo "For help:"
echo "  python run_scan.py --help"
'''

        install_path = target_dir / "setup_agent.sh"
        install_path.write_text(install_script)

        # Create Windows batch file
        batch_script = '''@echo off
echo 🧠 CompliSense-AI Secure Agent Setup
echo =====================================

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

:: Upgrade pip
echo 📥 Upgrading pip...
pip install --upgrade pip

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
echo For help:
echo   python run_scan.py --help
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

        # Cleanup temporary directory
        shutil.rmtree(agent_dir)

        return zip_path

    def _create_readme_file(self, target_dir: Path, scan_config: Dict[str, Any], user_info: Dict[str, Any]):
        """Create README file with instructions"""

        # Calculate expiration date (30 days from now)
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        generated_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        readme_content = f"""# CompliSense-AI Local Agent

    Welcome to your CompliSense-AI Local Agent! This agent allows you to scan your ML projects for compliance and security issues locally while maintaining privacy.

    ## 🚀 Quick Start

    ### Step 1: Extract the Agent
    Unzip the downloaded file to your preferred location:
    unzip complisense_agent_{scan_config['id']}.zip -d complisense_agent
    cd complisense_agent

    Step 2: Set Up the Environment
    On Linux/macOS:

    # Make the setup script executable
    chmod +x setup_agent.sh
    
    # Run the setup script
    ./setup_agent.sh
    On Windows:
    Double-click setup_agent.bat or run it from Command Prompt.
    
    Step 3: Activate the Environment
    On Linux/macOS:
    
    source complisense_env/bin/activate
    On Windows:
    cmd
    complisense_env\\Scripts\\activate.bat
    Step 4: Run Your First Scan
    bash
    python run_scan.py --project-path /path/to/your/ml/project --output-dir ./scan_results
    📋 Detailed Instructions
    Prerequisites
    Python 3.8 or higher
    
    500 MB free disk space
    
    Internet connection (for initial setup and reporting)
    
    Command Line Options
    bash
    # Basic scan
    python run_scan.py --project-path /path/to/project
    
    # Custom output directory
    python run_scan.py --project-path /path/to/project --output-dir ./my_results
    
    # Get help
    python run_scan.py --help
    🔒 Security & Privacy
    How It Works
    Local Scanning: All code analysis happens on your machine
    
    Secure Reporting: Only scan metadata and summaries are sent to CompliSense-AI
    
    No Code Upload: Your source code never leaves your environment
    
    🛠️ Troubleshooting
    Common Issues
    "Python not found" error
    
    Ensure Python 3.8+ is installed and in your PATH
    
    Virtual environment issues
    
    Delete the complisense_env directory and rerun setup
    
    Scan fails with permission errors
    
    Ensure you have read access to the project directory
    
    Getting Help
    Check the logs: Look for error messages in the console output
    
    Contact Support:
    
    Include your Scan ID: {scan_config['id']}
    
    Describe the issue and steps to reproduce
    
    Need Help?
    📧 Email: support@complisense.ai
    
    🌐 Website: https://complisense.ai
    
    Scan ID: {scan_config['id']}
    Generated on: {generated_date}
    Expires on: {expires_at}
    """
        readme_path = target_dir / "README.md"
        readme_path.write_text(readme_content)

# Singleton instance
agent_generator = AgentGenerator(Path("../../agent"))