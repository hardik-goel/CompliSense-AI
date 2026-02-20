# How to Use the Downloaded Agent Zip

## Quick Start

You've downloaded `complisense_agent_scan_02070f3e.zip` from the SaaS dashboard. Here's how to use it:

## Step 1: Extract the Zip

```bash
# Extract the agent
unzip complisense_agent_scan_02070f3e.zip -d complisense_agent
cd complisense_agent
```

## Step 2: Set Up Environment

### On macOS/Linux:
```bash
chmod +x setup_agent.sh
./setup_agent.sh
```

### On Windows:
Double-click `setup_agent.bat` or run:
```cmd
setup_agent.bat
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Set up the agent configuration

## Step 3: Activate Environment

### macOS/Linux:
```bash
source complisense_env/bin/activate
```

### Windows:
```cmd
complisense_env\Scripts\activate.bat
```

## Step 4: Run the Scan

### Option A: Using the GUI (Recommended for non-technical users)
```bash
python3 run_scan.py --gui
# Or on Windows:
python run_scan.py --gui
```

### Option B: Using Command Line
```bash
python3 run_scan.py \
  --project-path /path/to/your/ml/project \
  --output-dir ./scan_results
```

**Example:**
```bash
python3 run_scan.py \
  --project-path /Users/hardikgoel/Downloads/my_ml_model \
  --output-dir ./results
```

### Option C: Using the Custom Script (if provided)
The agent zip may include a custom script like `run_scan_custom.py`:
```bash
python3 run_scan_custom.py
```

## Step 5: View Results

After scanning, check the output directory (default: `./complisense_output` or your specified `--output-dir`):

### Files Generated:
1. **`compliance_findings.json`** - Detailed JSON results
2. **`audit_report.pdf`** - PDF audit report
3. **`dashboard.html`** - Interactive HTML dashboard
4. **`scan_summary.txt`** - Text summary

### View Results:

**Open Dashboard:**
```bash
# macOS
open dashboard.html

# Linux
xdg-open dashboard.html

# Windows
start dashboard.html
```

**Or open in browser:**
- Navigate to the output directory
- Double-click `dashboard.html`

## Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.9+ from python.org

### Issue: "Permission denied" on setup script
**Solution:**
```bash
chmod +x setup_agent.sh
```

### Issue: "Module not found" errors
**Solution:** Make sure virtual environment is activated:
```bash
source complisense_env/bin/activate  # macOS/Linux
complisense_env\Scripts\activate.bat  # Windows
```

### Issue: "File not found" errors
**Solution:** 
- Check that your project path is correct
- Ensure the path contains your ML model files
- Use absolute paths if relative paths don't work

### Issue: Scan takes too long
**Solution:**
- Large projects may take several minutes
- Check the progress indicator
- Ensure you have sufficient disk space

## What Gets Scanned?

The agent looks for:
- **Model files**: `.pkl`, `.onnx`, `.h5`, `.pt`, `.pth`
- **Documentation**: `model_card.json`, `dataset_card.json`
- **Compliance artifacts**: `risk_register.yaml`, compliance docs
- **Training code**: Python scripts, notebooks
- **Configuration files**: YAML, JSON configs

## Privacy & Security

✅ **All scanning happens locally** - No data leaves your computer
✅ **No internet required** - Works offline
✅ **Optional upload** - Only summary metadata (if enabled)

## Next Steps

1. Review the dashboard for compliance status
2. Address any FAILED rules
3. Re-run scan after fixes
4. Upload results to SaaS dashboard (optional)

## Support

If you encounter issues:
1. Check `complisense_agent.log` for error details
2. Verify Python version: `python3 --version` (should be 3.9+)
3. Ensure all dependencies installed: `pip list`
4. Contact support with scan ID: `scan_02070f3e`
