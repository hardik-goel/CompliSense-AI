def classify_risk(confidence: int, severity: str = "unknown") -> str:
    """
    Classify risk level based on confidence score and rule severity.
    
    Risk calculation:
    - Confidence >= 80: LOW risk (compliance likely)
    - Confidence 50-79: MEDIUM risk (partial compliance)
    - Confidence < 50: HIGH risk (non-compliance)
    
    Severity adjustment:
    - Critical severity failures always HIGH risk
    - Major severity failures boost risk by one level
    """
    # Base risk from confidence
    if confidence >= 80:
        base_risk = "LOW"
    elif confidence >= 50:
        base_risk = "MEDIUM"
    else:
        base_risk = "HIGH"
    
    # Adjust based on severity for failures
    if confidence < 80 and severity == "Critical":
        return "HIGH"
    elif confidence < 50 and severity == "Major":
        return "HIGH"
    
    return base_risk
