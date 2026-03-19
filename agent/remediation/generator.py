from agent.remediation.rules import REMEDIATIONS


def generate_remediation(rule_id: str, confidence: int):
    """
    Generate remediation suggestions based on rule ID and confidence.
    
    Args:
        rule_id: Full rule ID (e.g., "EUAI-ART11-TECHDOC-001")
        confidence: Confidence score (0-100)
    
    Returns:
        List of remediation suggestions (more for low confidence)
    """
    if not rule_id:
        return []
    
    # Try full rule ID prefix (e.g., "EUAI-ART11-TECHDOC")
    prefix_parts = rule_id.split("-")
    if len(prefix_parts) >= 3:
        prefix = "-".join(prefix_parts[:3])
        if prefix in REMEDIATIONS:
            base = REMEDIATIONS[prefix]
        else:
            # Try article prefix (e.g., "EUAI-ART11")
            article_prefix = "-".join(prefix_parts[:2])
            base = REMEDIATIONS.get(article_prefix, [])
    else:
        # Fallback to article prefix
        article_prefix = "-".join(prefix_parts[:2]) if len(prefix_parts) >= 2 else prefix_parts[0]
        base = REMEDIATIONS.get(article_prefix, [])
    
    if not base:
        # Generic remediation if no specific rule found
        return [
            "Review the rule requirements in the EU AI Act",
            "Create the required documentation artifacts",
            "Ensure all required fields are present and valid"
        ]
    
    # Return more suggestions for lower confidence (more severe issues)
    if confidence < 30:
        return base  # All suggestions
    elif confidence < 50:
        return base[:3] if len(base) > 3 else base  # Top 3
    else:
        return base[:2] if len(base) > 2 else base  # Top 2
