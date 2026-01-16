def infer(signals):
    return {
        "likely_use": "classification",
        "possible_risks": ["bias", "data leakage"],
        "recommended_docs": ["model card", "data card"]
    }
