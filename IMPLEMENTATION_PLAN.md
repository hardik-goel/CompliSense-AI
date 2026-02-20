# Implementation Plan - MVP Enhancements

## ✅ Completed
1. Fixed CLI bug
2. Created enhanced scanner with error handling

## 🔄 In Progress

### 1. Remove Redundant Code
**Files to delete:**
- `agent/api.py` (duplicate, use api_handlers.py)
- `server/saas_api.py` (duplicate, use saas/app/main.py)
- `server/auth.py` (duplicate, use saas/app/auth.py)

**Action:**
```bash
rm agent/api.py server/saas_api.py server/auth.py
```

### 2. Enhanced Error Handling
**Files to update:**
- `agent/scanner.py` - Add try/catch, better error messages
- `agent/evaluators/file_presence.py` - Better file not found messages
- `agent/evaluators/schema_validate.py` - Better schema validation errors

**Key improvements:**
- User-friendly error messages
- Logging for debugging
- Graceful degradation (continue scan even if one rule fails)

### 3. Unit Tests
**Files to create/update:**
- `tests/test_scanner.py` - Expand existing tests
- `tests/test_evaluators.py` - New file for evaluator tests
- `tests/test_error_handling.py` - Test error scenarios

**Test coverage:**
- Missing files
- Invalid rule expressions
- Evaluator errors
- Edge cases

### 4. UI Enhancements
**File to update:** `agent/agent_ui.py`

**Improvements:**
- Real-time progress bar with percentage
- Rule-by-rule status updates
- Better error display (color-coded)
- Results summary card
- Open results button
- Cancel button improvements

### 5. Agent Zip Usage Guide
**File to create:** `AGENT_ZIP_USAGE.md`

**Contents:**
- Step-by-step instructions
- Troubleshooting
- Platform-specific notes

### 6. Hosting Guide
**File to create:** `HOSTING_GUIDE.md`

**Options:**
- Railway.app (cheapest, easiest)
- Render.com (free tier)
- Fly.io (good for Python)
- DigitalOcean App Platform
- AWS/GCP (more complex)

## Next Steps

1. Replace scanner.py with enhanced version
2. Update evaluators with better error handling
3. Expand test suite
4. Enhance UI
5. Create documentation
