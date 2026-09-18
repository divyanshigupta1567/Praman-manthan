"""Test Script for Praman ML Civic Incident Classifier.

Allows testing trained models (Logistic Regression & Linear SVM) with:
1. Preset challenging test complaints across all 6 categories
2. Single custom complaint via CLI (--text "...")
3. Interactive REPL mode (--interactive)
4. Evaluation on holdout test set (--eval or --sample N)
"""

import argparse
import os
import pickle
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to sys.path to allow imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.classifier import PRAMAN_CATEGORIES, ComplaintClassifier, load_and_validate_dataset


DEFAULT_TEST_CASES = [
    {
        "expected": "Pothole",
        "text": "Huge deep crater on the main cross road causing two-wheelers to slip and damage tires.",
    },
    {
        "expected": "Garbage",
        "text": "Open dump yard near school gate. Vegetable waste and plastic bottles rotting with bad odor.",
    },
    {
        "expected": "Water Leakage",
        "text": "Underground BWSSB drinking water pipeline burst open and thousands of liters wasted on footpath.",
    },
    {
        "expected": "Streetlight",
        "text": "Street lights in 5th main road have not been functional for 10 days, area is pitch dark at night.",
    },
    {
        "expected": "Sewage",
        "text": "Drainage manhole blocked and dirty black sewage overflowing directly into residential building gates.",
    },
    {
        "expected": "Traffic Hazard",
        "text": "Fallen tree branches and illegal barrier blocking half the arterial carriageway causing heavy traffic jam.",
    },
    {
        "expected": "Pothole",
        "text": "Road has completely vanished after recent rain, filled with dangerous sharp depressions.",
    },
    {
        "expected": "Garbage",
        "text": "Garbage auto has not visited our street for one week. Unattended plastic waste piled everywhere.",
    },
]


def load_artifacts(
    model_dir: str = "ml",
    use_svm: bool = False,
) -> Tuple[Any, Any, np.ndarray]:
    """Loads vectorizer, model, and class labels."""
    vec_path = os.path.join(model_dir, "vectorizer.pkl")
    model_file = "svm_model.pkl" if use_svm else "model.pkl"
    model_path = os.path.join(model_dir, model_file)

    if not os.path.exists(vec_path):
        # Fallback to models/ directory if not found in ml/
        model_dir = "models"
        vec_path = os.path.join(model_dir, "vectorizer.pkl")
        model_path = os.path.join(model_dir, model_file)

    if not os.path.exists(vec_path) or not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model artifacts not found in '{model_dir}'. Run 'python ml/classifier.py' first to generate them."
        )

    with open(vec_path, "rb") as f:
        vectorizer = pickle.load(f)

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    classes = getattr(model, "classes_", np.array(PRAMAN_CATEGORIES))
    return vectorizer, model, classes


def predict_single(
    text: str,
    vectorizer: Any,
    model: Any,
    classes: np.ndarray,
) -> Dict[str, Any]:
    """Runs inference on a single complaint text and returns detailed class probabilities."""
    start_time = time.perf_counter()
    vec = vectorizer.transform([text])
    probas = model.predict_proba(vec)[0]
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    best_idx = int(np.argmax(probas))
    pred_category = str(classes[best_idx])
    confidence = float(probas[best_idx])

    # Rank all classes by probability
    ranked = sorted(
        [{"category": str(c), "probability": float(p)} for c, p in zip(classes, probas)],
        key=lambda x: x["probability"],
        reverse=True,
    )

    return {
        "complaint_text": text,
        "predicted_category": pred_category,
        "confidence": confidence,
        "elapsed_ms": elapsed_ms,
        "distribution": ranked,
    }


def print_prediction_card(res: Dict[str, Any], expected: Optional[str] = None):
    """Prints a styled card showing model prediction, confidence, and distribution."""
    print("\n" + "-" * 75)
    print(f"Complaint: \"{res['complaint_text']}\"")
    
    match_str = ""
    if expected:
        is_match = res["predicted_category"].lower() == expected.lower()
        match_str = f" [Expected: {expected} | {'MATCH' if is_match else 'MISMATCH'}]"

    print(f"Predicted Category : {res['predicted_category']}{match_str}")
    print(f"Confidence Score   : {res['confidence'] * 100:.2f}%  ({res['confidence']:.4f})")
    print(f"Inference Latency  : {res['elapsed_ms']:.2f} ms")
    print("Class Probability Distribution:")
    for item in res["distribution"]:
        bar_len = int(item["probability"] * 30)
        bar = "#" * bar_len + "-" * (30 - bar_len)
        print(f"  - {item['category']:<16} : [{bar}] {item['probability'] * 100:5.1f}%")
    print("-" * 75)


def run_preset_tests(vectorizer: Any, model: Any, classes: np.ndarray):
    """Runs tests across preset challenging civic complaint examples."""
    print("\n" + "=" * 75)
    print("           RUNNING PRESET TEST CASES ACROSS ALL 6 CATEGORIES")
    print("=" * 75)

    correct = 0
    total = len(DEFAULT_TEST_CASES)

    for i, item in enumerate(DEFAULT_TEST_CASES, 1):
        res = predict_single(item["text"], vectorizer, model, classes)
        is_match = res["predicted_category"].lower() == item["expected"].lower()
        if is_match:
            correct += 1
        print(f"\n[Test Case {i}/{total}]")
        print_prediction_card(res, expected=item["expected"])

    accuracy = (correct / total) * 100
    print("\n" + "=" * 75)
    print(f"Preset Tests Summary: {correct}/{total} passed ({accuracy:.1f}% accuracy)")
    print("=" * 75)


def run_interactive_mode(vectorizer: Any, model: Any, classes: np.ndarray, model_name: str):
    """Interactive loop allowing manual input testing."""
    print("\n" + "=" * 75)
    print(f"   PRAMAN CLASSIFIER INTERACTIVE TESTER (Model: {model_name})")
    print("   Type any civic complaint below to test (or 'exit' / 'q' to quit).")
    print("=" * 75)

    while True:
        try:
            user_input = input("\nEnter complaint > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Exiting interactive test. Goodbye!")
                break
            res = predict_single(user_input, vectorizer, model, classes)
            print_prediction_card(res)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


def run_holdout_evaluation(
    test_csv: str,
    vectorizer: Any,
    model: Any,
    classes: np.ndarray,
    sample_size: Optional[int] = None,
):
    """Runs evaluation on holdout test set with accuracy and latency reporting."""
    print(f"\nLoading holdout test dataset from: {test_csv}")
    df = load_and_validate_dataset(test_csv)
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        print(f"Evaluating on random sample of {sample_size} records...")
    else:
        print(f"Evaluating on full holdout test set ({len(df)} records)...")

    start_t = time.perf_counter()
    X_vec = vectorizer.transform(df["complaint_text"].astype(str))
    probas = model.predict_proba(X_vec)
    total_time_ms = (time.perf_counter() - start_t) * 1000

    pred_indices = np.argmax(probas, axis=1)
    y_pred = classes[pred_indices]
    y_true = df["category"].astype(str).to_numpy()

    correct = np.sum(y_pred == y_true)
    total = len(df)
    accuracy = (correct / total) * 100
    avg_latency = total_time_ms / total

    print("\n" + "=" * 70)
    print("                  HOLDOUT EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Test Records    : {total}")
    print(f"Correct Predictions   : {correct}")
    print(f"Overall Accuracy      : {accuracy:.2f}%")
    print(f"Total Inference Time  : {total_time_ms:.2f} ms")
    print(f"Avg Latency / Record  : {avg_latency:.3f} ms")
    print("=" * 70)

    # Per-category accuracy breakdown
    print(f"\n{'Category':<18} | {'Support':<8} | {'Correct':<8} | {'Accuracy':<10}")
    print("-" * 52)
    for cat in classes:
        mask = (y_true == cat)
        cat_support = int(np.sum(mask))
        if cat_support > 0:
            cat_correct = int(np.sum((y_pred == cat) & mask))
            cat_acc = (cat_correct / cat_support) * 100
            print(f"{cat:<18} | {cat_support:<8} | {cat_correct:<8} | {cat_acc:6.2f}%")
    print("-" * 52)


def main():
    parser = argparse.ArgumentParser(description="Test Praman Civic Incident Classification Model")
    parser.add_argument("--text", type=str, default=None, help="Single complaint text string to classify.")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive REPL mode.")
    parser.add_argument("--eval", action="store_true", help="Evaluate model on data/praman_test.csv.")
    parser.add_argument("--sample", type=int, default=None, help="Evaluate on N random samples from test set.")
    parser.add_argument("--test-data", type=str, default="data/praman_test.csv", help="Path to test CSV.")
    parser.add_argument("--model-dir", type=str, default="ml", help="Directory with vectorizer and model pkl files.")
    parser.add_argument(
        "--model",
        type=str,
        choices=["lr", "svm"],
        default="lr",
        help="Model to test: 'lr' (Logistic Regression, default) or 'svm' (Linear SVM).",
    )
    args = parser.parse_args()

    use_svm = args.model == "svm"
    model_name = "Calibrated Linear SVM" if use_svm else "Logistic Regression"
    print(f"Loading Praman Classifier [{model_name}] from '{args.model_dir}'...")

    vectorizer, model, classes = load_artifacts(model_dir=args.model_dir, use_svm=use_svm)
    print(f"Ready. Classes: {list(classes)}")

    # 1. Single text prediction
    if args.text:
        res = predict_single(args.text, vectorizer, model, classes)
        print_prediction_card(res)
        return

    # 2. Holdout evaluation or sample evaluation
    if args.eval or args.sample is not None:
        run_holdout_evaluation(
            test_csv=args.test_data,
            vectorizer=vectorizer,
            model=model,
            classes=classes,
            sample_size=args.sample,
        )
        return

    # 3. Interactive mode
    if args.interactive:
        run_interactive_mode(vectorizer, model, classes, model_name)
        return

    # 4. Default: run preset test cases across categories
    run_preset_tests(vectorizer, model, classes)
    print("\nTip: Run with --interactive to test your own complaints, or --text 'your complaint' for a quick test.")


if __name__ == "__main__":
    main()
