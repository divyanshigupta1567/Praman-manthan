import json
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "model_metrics.json")


def get_model_metrics():
    """Retrieve classifier model metrics for baseline and comparison model.
    
    Swap hook: When Member 1 completes classifier training,
    this function will read real evaluation outputs.
    """
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "baseline_model": {
            "model_name": "TF-IDF + Logistic Regression",
            "accuracy": 0.892,
            "precision": 0.887,
            "recall": 0.890,
            "f1": 0.888
        },
        "comparison_model": {
            "model_name": "Linear SVM",
            "accuracy": 0.915,
            "precision": 0.912,
            "recall": 0.914,
            "f1": 0.913
        }
    }
