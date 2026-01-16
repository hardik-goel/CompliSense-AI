def compute_confidence(signals: dict, weights: dict) -> int:
    """
    signals: {"model_found": True, "docs_present": False}
    weights: {"model_found": 30, "docs_present": 40}
    """
    score = 0
    max_score = sum(weights.values())

    for key, weight in weights.items():
        if signals.get(key):
            score += weight

    return int((score / max_score) * 100)
