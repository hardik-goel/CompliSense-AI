from pathlib import Path
import pickle

def run(root: Path, inputs: dict):
    """
    Attempts to infer basic metadata from serialized ML models.
    """
    model_files = list(root.rglob("*.pkl"))
    if not model_files:
        return {
            "model_found": False,
            "framework": None,
            "signals": {}
        }

    model_path = model_files[0]
    signals = {}

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        signals["model_type"] = type(model).__name__
        signals["module"] = type(model).__module__
        signals["has_predict"] = hasattr(model, "predict")
        signals["has_fit"] = hasattr(model, "fit")

        framework = "sklearn" if "sklearn" in signals["module"] else "unknown"

        return {
            "model_found": True,
            "framework": framework,
            "signals": signals
        }

    except Exception as e:
        return {
            "model_found": True,
            "error": str(e),
            "signals": {}
        }
