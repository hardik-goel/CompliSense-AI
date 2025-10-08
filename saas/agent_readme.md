# CompliSense-AI Local Agent

Welcome to your CompliSense-AI Local Agent! This agent allows you to scan your ML projects for compliance and security issues locally while maintaining privacy.

## 🚀 Quick Start

### Step 1: Extract the Agent
Unzip the downloaded file to your preferred location:
```bash
unzip complisense_agent_[SCAN_ID].zip -d complisense_agent
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

complisense_env\Scripts\activate.bat
Step 4: Run Your First Scan


python run_scan.py --project-path /path/to/your/ml/project --output-dir ./scan_results

📋 Detailed Instructions
Prerequisites
Python 3.8 or higher

CLI options

# Basic scan
python run_scan.py --project-path /path/to/project

# Custom output directory
python run_scan.py --project-path /path/to/project --output-dir ./my_results

# Get help
python run_scan.py --help

What Gets Scanned
Python files (.py)

Configuration files (.yaml, .yml, .json)

Documentation files (.md, .txt)

Model files and configurations

Dependency specifications

Excluded Directories
The agent automatically excludes:

Virtual environments (.venv, venv, env)

Git directories (.git)

Cache directories (pycache, .pytest_cache)

Node modules (node_modules)

Other common development directories

📊 Understanding Results
Output Files
After each scan, you'll find:

compliance_findings.json - Detailed findings in JSON format

Scan summary in the console

JSON Report Structure

{
  "summary": {
    "scanned_files": 42,
    "total_findings": 5,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "findings": [
    {
      "rule_id": "SEC-001",
      "file": "src/model.py",
      "line": 23,
      "severity": "high",
      "message": "Hardcoded API key detected",
      "category": "security"
    }
  ]
}

Severity Levels
🔴 High - Critical issues that require immediate attention

🟡 Medium - Important issues that should be addressed

🔵 Low - Best practice recommendations

🔒 Security & Privacy
How It Works
Local Scanning: All code analysis happens on your machine

Secure Reporting: Only scan metadata and summaries are sent to CompliSense-AI

No Code Upload: Your source code never leaves your environment

Encrypted Communication: All external communication uses HTTPS

Data Sent to CompliSense-AI
Scan metadata (scan ID, project name)

Summary statistics (files scanned, findings count)

Rule validation and license checks

Performance metrics (anonymized)

Data Kept Local
Your source code

Detailed scan results

File contents and structure

Personal or sensitive information

🛠️ Troubleshooting
Common Issues
"Python not found" error

Ensure Python 3.8+ is installed and in your PATH

Verify with: python3 --version or python --version

Virtual environment issues

Delete the complisense_env directory and rerun setup

On Windows, try: rmdir /s complisense_env

Scan fails with permission errors

Ensure you have read access to the project directory

Try running from a different location

Network connectivity issues

The agent requires internet for initial setup and reporting

Check your firewall settings for outgoing HTTPS connections

Getting Help
Check the logs: Look for error messages in the console output

Verify configuration: Check config/agent_config.json

Contact Support:

Include your Scan ID: [SCAN_ID]

Describe the issue and steps to reproduce

Share the console output (excluding sensitive information)

📝 License & Terms
This agent is licensed for use on a single project

License expires on: [EXPIRATION_DATE]

Usage subject to CompliSense-AI Terms of Service

Unauthorized distribution prohibited

🔄 Updates
This agent will automatically:

Check for rulepack updates

Validate license status

Receive security patches

Manual updates may be required for major version changes.

Need Help?
📧 Email: support@complisense.ai

🌐 Website: https://complisense.ai

📚 Docs: https://docs.complisense.ai

Scan ID: [SCAN_ID]
Generated on: [GENERATION_DATE]
Expires on: [EXPIRATION_DATE]




