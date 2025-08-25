import sys
from pathlib import Path
import json
import pytest
from click.testing import CliRunner
import cli

sys.path.append(str(Path(__file__).resolve().parents[1]))

runner_cli = cli.cli

@pytest.fixture
def sample_rulepack(tmp_path):
    pack = {
        "rules": [{
            "id": "R1",
            "clause": "Art.10",
            "title": "Dataset doc",
            "severity": "Critical",
            "evaluator": "file_presence",
            "inputs": {"file": "dummy.json"},
            "expression": "exists == True"
        }]
    }
    f = tmp_path / "rules.yaml"
    f.write_text(json.dumps(pack))
    return f

def test_scan_command(monkeypatch, tmp_path, sample_rulepack):
    runner = CliRunner()

    # Mock evaluators
    monkeypatch.setattr("agent.scanner._run_evaluator", lambda r, e, i: {"exists": True})
    monkeypatch.setattr("agent.report.render.render_pdf", lambda r, p: p.write_text("pdf"))

    result = runner.invoke(cli, ["scan", "--root", str(tmp_path),
                                 "--pack", str(sample_rulepack),
                                 "--out", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "findings.json").exists()
