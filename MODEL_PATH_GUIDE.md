# What is `/path/to/model`? - Model Path Guide

## Quick Answer

The `--project-path` (or `/path/to/model`) should point to the **folder/directory** containing your ML project, **NOT** a specific `.pkl` file.

## What Should Be in This Folder?

The scanner looks for **compliance artifacts** in your project folder. It doesn't need the actual model file (`.pkl`, `.onnx`, etc.) - it needs **documentation** about your model.

### Required/Expected Files:

```
your_ml_project/
├── model/
│   └── model_card.json          ← Model documentation (Art. 11)
├── data/
│   └── dataset_card.json        ← Dataset documentation (Art. 10)
├── compliance/
│   └── risk_register.yaml       ← Risk management (Art. 9)
└── (optional) your_model.pkl    ← Actual model file (not scanned)
```

## Examples

### Example 1: Simple Project
```bash
# Your project structure:
~/my_ml_project/
├── model_card.json
├── dataset_card.json
└── risk_register.yaml

# Run scan:
python3 run_scan.py --project-path ~/my_ml_project --output-dir ./results
```

### Example 2: Organized Project
```bash
# Your project structure:
~/ml_models/customer_service_bot/
├── model/
│   ├── model_card.json
│   └── bot_model.pkl
├── data/
│   ├── dataset_card.json
│   └── training_data.csv
└── compliance/
    └── risk_register.yaml

# Run scan:
python3 run_scan.py \
  --project-path ~/ml_models/customer_service_bot \
  --output-dir ./results
```

### Example 3: Using Current Directory
```bash
# If you're already in the project folder:
cd ~/my_ml_project
python3 run_scan.py --project-path . --output-dir ./results
```

## What Gets Scanned?

The scanner looks for:

1. **Model Documentation** (`model_card.json` or `model/model_card.json`)
   - Intended purpose
   - Architecture details
   - Training data references
   - Evaluation metrics
   - Known limitations

2. **Dataset Documentation** (`dataset_card.json` or `data/dataset_card.json`)
   - Data provenance
   - Collection methods
   - Licensing
   - Known biases
   - Preprocessing steps

3. **Risk Management** (`risk_register.yaml` or `compliance/risk_register.yaml`)
   - Identified risks
   - Mitigation strategies
   - Risk status

## What Doesn't Get Scanned?

- ❌ Actual model files (`.pkl`, `.onnx`, `.h5`, `.pt`) - not needed
- ❌ Training code (`.py` files) - optional, not required
- ❌ Raw datasets - not scanned (privacy)
- ❌ Source code - not analyzed

## If You Don't Have Documentation Yet

If your project doesn't have these files yet, the scanner will:
- ✅ Still run successfully
- ✅ Report what's missing
- ✅ Provide remediation guidance
- ✅ Show you what needs to be created

## Common Mistakes

### ❌ Wrong: Pointing to a file
```bash
python3 run_scan.py --project-path ~/my_model.pkl  # WRONG!
```

### ✅ Correct: Pointing to a folder
```bash
python3 run_scan.py --project-path ~/my_ml_project  # CORRECT!
```

### ❌ Wrong: Using relative path incorrectly
```bash
cd ~/some_other_folder
python3 run_scan.py --project-path my_ml_project  # Might not work
```

### ✅ Correct: Use absolute path or be in the right directory
```bash
python3 run_scan.py --project-path ~/my_ml_project  # Absolute path
# OR
cd ~/my_ml_project
python3 run_scan.py --project-path .  # Current directory
```

## For Your Specific Case

Based on your codebase, if you have a project like:

```
~/Downloads/my_model/
├── model.pkl
├── train.py
└── (no documentation yet)
```

Run:
```bash
python3 run_scan.py \
  --project-path ~/Downloads/my_model \
  --output-dir ./scan_results
```

The scanner will:
1. Scan the folder
2. Report missing documentation
3. Tell you what to create
4. Generate a compliance report

## Summary

- **Path = Folder/Directory**, not a file
- **Scanner looks for documentation**, not model files
- **Use absolute paths** or be in the project directory
- **Missing files are OK** - scanner will tell you what's needed
