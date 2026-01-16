def classify_risk(confidence: int) -> str:
    if confidence >= 80:
        return "LOW"
    elif confidence >= 50:
        return "MEDIUM"
    return "HIGH"
