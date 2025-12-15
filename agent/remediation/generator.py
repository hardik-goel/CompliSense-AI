from agent.remediation.rules import REMEDIATIONS


def generate_remediation(rule_id: str, confidence: int):
    base = REMEDIATIONS.get(rule_id.split("-")[0], [])
    if confidence < 50:
        return base
    return base[:1]
