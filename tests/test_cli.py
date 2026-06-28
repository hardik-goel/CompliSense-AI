import json
import pytest
from click.testing import CliRunner

import agent.cli as cli_module


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
            "expression": "exists == true"
        }]
    }
    f = tmp_path / "rules.yaml"
    f.write_text(json.dumps(pack))
    return f


def test_scan_command(monkeypatch, tmp_path, sample_rulepack):
    runner = CliRunner()

    # Mock the evaluator so the rule passes without real artefacts.
    monkeypatch.setattr("agent.scanner._run_evaluator", lambda root, evaluator, inputs: {"exists": True})
    # render_pdf is imported into agent.cli's namespace; patch it there. Accept any arity.
    monkeypatch.setattr("agent.cli.render_pdf", lambda *args, **kwargs: None)

    result = runner.invoke(
        cli_module.cli,
        ["scan", "--root", str(tmp_path), "--pack", str(sample_rulepack), "--out", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "findings.json").exists()
