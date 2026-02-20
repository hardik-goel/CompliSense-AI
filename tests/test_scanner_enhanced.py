"""
Enhanced tests for scanner.py with error handling coverage.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from agent.scanner import run_scan, scan_required_artifacts, _run_evaluator


def test_scan_required_artifacts_missing_manifest(tmp_path):
    """Test handling of missing manifest file."""
    with patch('agent.scanner.resource_path', return_value=str(tmp_path / "nonexistent.yaml")):
        result = scan_required_artifacts(tmp_path)
        assert "error" in result
        assert result["compliance_pct"] == 0.0


def test_scan_required_artifacts_invalid_yaml(tmp_path):
    """Test handling of invalid YAML in manifest."""
    manifest = tmp_path / "required_artifacts.yaml"
    manifest.write_text("invalid: yaml: content: [")
    
    with patch('agent.scanner.resource_path', return_value=str(manifest)):
        result = scan_required_artifacts(tmp_path)
        # Should handle gracefully
        assert isinstance(result, dict)


def test_run_scan_missing_root():
    """Test error when root directory doesn't exist."""
    with pytest.raises(FileNotFoundError):
        run_scan(Path("/nonexistent/path"), [])


def test_run_scan_no_rules(tmp_path):
    """Test scan with no rules."""
    result = run_scan(tmp_path, [])
    assert result["summary"]["passed"] == 0
    assert result["summary"]["failed"] == 0
    assert "error" in result or len(result["results"]) == 0


def test_run_scan_invalid_evaluator(tmp_path):
    """Test handling of invalid evaluator name."""
    rules = [{
        "id": "R1",
        "evaluator": "nonexistent_evaluator",
        "inputs": {},
        "expression": "True"
    }]
    
    result = run_scan(tmp_path, rules)
    assert len(result["results"]) == 1
    assert "engine_error" in result["results"][0]["context"]


def test_run_scan_missing_evaluator_field(tmp_path):
    """Test handling of rule missing evaluator field."""
    rules = [{
        "id": "R1",
        "inputs": {},
        "expression": "True"
    }]
    
    result = run_scan(tmp_path, rules)
    assert len(result["results"]) == 1
    assert "engine_error" in result["results"][0]["context"]


def test_run_scan_invalid_expression(tmp_path):
    """Test handling of invalid rule expression."""
    def mock_evaluator(root, inputs):
        return {"exists": True}
    
    with patch('agent.scanner._run_evaluator', return_value=mock_evaluator(tmp_path, {})):
        rules = [{
            "id": "R1",
            "evaluator": "file_presence",
            "inputs": {},
            "expression": "invalid syntax !!!"
        }]
        
        result = run_scan(tmp_path, rules)
        assert len(result["results"]) == 1
        assert "expression_error" in result["results"][0]["context"]


def test_run_scan_cancel_event(tmp_path):
    """Test scan cancellation."""
    cancel_event = MagicMock()
    cancel_event.is_set.return_value = True
    
    rules = [{"id": "R1", "evaluator": "file_presence", "inputs": {}, "expression": "True"}]
    
    progress_calls = []
    def progress_callback(payload):
        progress_calls.append(payload)
    
    result = run_scan(tmp_path, rules, cancel_event=cancel_event, progress_callback=progress_callback)
    
    # Should have cancelled event
    assert any("SCAN_CANCELLED" in str(call) for call in progress_calls)


def test_run_evaluator_import_error():
    """Test handling of evaluator import error."""
    result = _run_evaluator(Path("/tmp"), "nonexistent_module", {})
    assert "engine_error" in result
    assert "not found" in result["engine_error"].lower()


def test_run_evaluator_missing_run_function():
    """Test handling of evaluator missing run function."""
    with patch('agent.scanner.import_module') as mock_import:
        mock_mod = MagicMock()
        del mock_mod.run  # Remove run function
        mock_import.return_value = mock_mod
        
        result = _run_evaluator(Path("/tmp"), "test_evaluator", {})
        assert "engine_error" in result


def test_run_scan_progress_callback(tmp_path):
    """Test progress callback is called correctly."""
    progress_calls = []
    
    def progress_callback(payload):
        progress_calls.append(payload)
    
    rules = [
        {"id": "R1", "evaluator": "file_presence", "inputs": {"file": "test.json"}, "expression": "exists"},
        {"id": "R2", "evaluator": "file_presence", "inputs": {"file": "test2.json"}, "expression": "exists"}
    ]
    
    run_scan(tmp_path, rules, progress_callback=progress_callback)
    
    # Should have progress events
    assert len(progress_calls) > 0
    assert any("RULE_START" in str(call) for call in progress_calls)
    assert any("SCAN_COMPLETE" in str(call) for call in progress_calls)


def test_run_scan_with_thresholds(tmp_path):
    """Test scan with threshold-based rules."""
    def mock_evaluator(root, inputs):
        return {"coverage_score": 0.85}
    
    with patch('agent.scanner._run_evaluator', return_value=mock_evaluator(tmp_path, {})):
        rules = [{
            "id": "R1",
            "evaluator": "techdoc_coverage",
            "inputs": {},
            "thresholds": {"pass": 0.8, "partial": 0.5},
            "expression": "coverage_score >= 0.7"
        }]
        
        result = run_scan(tmp_path, rules)
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "PASS"


def test_run_scan_with_missing_fields_threshold(tmp_path):
    """Test scan with missing_fields threshold."""
    def mock_evaluator(root, inputs):
        return {"missing_fields": 1}
    
    with patch('agent.scanner._run_evaluator', return_value=mock_evaluator(tmp_path, {})):
        rules = [{
            "id": "R1",
            "evaluator": "file_presence",
            "inputs": {},
            "thresholds": {"pass": 0.0, "partial": 2.0},
            "expression": "exists"
        }]
        
        result = run_scan(tmp_path, rules)
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "PARTIAL"
