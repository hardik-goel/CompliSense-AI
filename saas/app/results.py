# saas/app/results.py

def evaluate_rule(rule_id: str, artefact: dict):
    """
    Simple evaluator for demonstration & partial pass/fail testing
    """

    try:
        if rule_id == "EUAI-ART9":
            if artefact.get("risk_management_plan"):
                return {"status": "PASS"}
            return {
                "status": "FAIL",
                "explanation": "Risk management plan not found"
            }

        if rule_id == "EUAI-ART10":
            if artefact.get("data_governance"):
                return {"status": "PASS"}
            return {
                "status": "FAIL",
                "explanation": "Data governance controls missing"
            }

        if rule_id == "EUAI-ART11":
            return {
                "status": "ERROR",
                "explanation": "Technical documentation evaluator not configured"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "explanation": str(e)
        }
