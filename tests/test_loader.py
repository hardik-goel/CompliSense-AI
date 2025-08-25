from pathlib import Path
import yaml
from agent.rules.loader import load_rulepack, iter_rules


def test_load_rulepack_and_iter_rules(tmp_path: Path):
    yaml_content = {
        "rules": [{"id": "R1", "expression": "exists"}]
    }
    rule_file = tmp_path / "rules.yaml"
    rule_file.write_text(yaml.safe_dump(yaml_content), encoding="utf-8")

    pack = load_rulepack(rule_file)
    assert "rules" in pack

    rules = iter_rules(pack)
    assert isinstance(rules, list)
    assert rules[0]["id"] == "R1"
