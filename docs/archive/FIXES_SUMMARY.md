# Fixes Applied - Summary

## Critical Bugs Fixed ✅

### 1. Missing `required_artifacts.yaml` File
**Problem**: Scanner crashed with `FileNotFoundError` on every scan
**Fix**: Created `agent/artefacts/required_artifacts.yaml` with proper artifact definitions for:
- Risk register (Art. 9)
- Dataset card (Art. 10)  
- Model card (Art. 11)

### 2. Scanner Coverage Score Bug
**Problem**: Rules with thresholds never passed because evaluators return `coverage` but scanner checked `coverage_score`
**Fix**: Scanner now checks both `coverage_score` (from techdoc_coverage) and `coverage` (from schema_validate)

### 3. Rules Too Strict
**Problem**: Everything showed FAIL (red) even when partial evidence existed
**Fix**: 
- Added `thresholds` support for partial passes
- Updated rules to allow 1-2 missing fields for PARTIAL status
- Rules now properly evaluate with injected context variables

### 4. Evaluators Missing Signals
**Problem**: Confidence scoring didn't work because evaluators didn't return `signals`
**Fix**: All evaluators now return consistent `signals` dict:
- `file_presence`: `{"file_exists": bool, "all_fields_present": bool}`
- `schema_validate`: `{"file_exists": bool, "schema_valid": bool, "coverage_met": bool}`
- `techdoc_coverage`: `{"explicit_docs": bool, "model_found": bool}`

### 5. Dashboard Compliance Score
**Problem**: Dashboard didn't account for PARTIAL status, only counted FAIL
**Fix**: Updated compliance score calculation to include PARTIAL with 50% penalty

## Rules Updated

### Made Less Strict:
- **EUAI-ART9-RISK-MGMT-001**: Now allows partial coverage (0.5+) for PARTIAL status
- **EUAI-ART10-DATA-GOV-001**: Allows up to 2 missing fields for PARTIAL
- **EUAI-ART11-TECHDOC-001**: Allows up to 2 missing fields for PARTIAL

### Added New Rules:
- **EUAI-ART13-TRANSPARENCY-001**: Transparency and information to users
- **EUAI-ART14-HUMAN-OVERSIGHT-001**: Human oversight measures
- **EUAI-ART15-ACCURACY-001**: Accuracy, robustness and cybersecurity
- **EUAI-ART16-QUALITY-MGMT-001**: Quality management system
- **EUAI-ART18-DATA-GOV-002**: Extended data governance
- **EUAI-ART20-RECORD-KEEPING-001**: Record keeping and logging

## Testing Your Fixes

Run this command to test:

```bash
python3 -m agent.cli scan --root artefacts --pack rulepacks/euai_core_v1.yaml --out out
```

**Expected Results**:
- ✅ Should see GREEN/PASS statuses when artifacts are present
- ✅ Should see PARTIAL status when some fields are missing
- ✅ Should see FAIL only when evidence is truly missing
- ✅ Dashboard should show accurate compliance score

## Next Steps

1. **Test the fixes** - Run scans on your test artifacts
2. **Remove redundant code** - See `ANALYSIS_AND_ROADMAP.md` section on redundant code
3. **Add error handling** - Better messages for missing files
4. **Write tests** - At least for scanner.py

See `ANALYSIS_AND_ROADMAP.md` for complete roadmap to MVP.
