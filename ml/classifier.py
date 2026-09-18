"""Civic Complaint Category Classifier for Praman Platform.

Trains a TF-IDF + Logistic Regression classifier (primary model) alongside a
Calibrated Linear SVM (comparison model).

Strictly trains on `data/praman_train.csv` and evaluates on `data/praman_test.csv`.
Outputs real performance metrics (Accuracy, Precision, Recall, F1, Confusion Matrix)
and saves model/vectorizer artifacts (`ml/model.pkl`, `ml/vectorizer.pkl`) for backend inference.
"""

import argparse
import json
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.svm import LinearSVC

PRAMAN_CATEGORIES: List[str] = [
    "Pothole",
    "Garbage",
    "Water Leakage",
    "Streetlight",
    "Sewage",
    "Traffic Hazard",
]

REQUIRED_COLUMNS: List[str] = [
    "complaint_id",
    "complaint_text",
    "category",
    "latitude",
    "longitude",
    "locality",
    "timestamp",
    "status",
]


def load_and_validate_dataset(csv_path: str) -> pd.DataFrame:
    """Safely loads and validates a Praman dataset CSV.

    Validates:
    - File exists
    - Required columns exist
    - No missing or empty complaint_text
    - No missing or empty category
    - All category values strictly belong to the six Praman categories

    Returns
    -------
    pd.DataFrame
        Validated clean DataFrame.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found at: '{csv_path}'")

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    # 1. Validate required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset '{csv_path}' missing required schema columns: {missing_cols}. "
            f"Expected schema: {REQUIRED_COLUMNS}"
        )

    # 2. Check for missing complaint_text or category
    initial_len = len(df)
    null_text = df["complaint_text"].isnull() | (df["complaint_text"].astype(str).str.strip() == "")
    null_cat = df["category"].isnull() | (df["category"].astype(str).str.strip() == "")

    if null_text.any() or null_cat.any():
        invalid_count = (null_text | null_cat).sum()
        df = df[~null_text & ~null_cat].copy()
        print(f"Warning: Dropped {invalid_count} row(s) with missing text/category from '{csv_path}'.")

    # 3. Validate category values belong to the 6 Praman categories
    invalid_categories = set(df["category"].unique()) - set(PRAMAN_CATEGORIES)
    if invalid_categories:
        raise ValueError(
            f"Dataset '{csv_path}' contains unauthorized categories: {invalid_categories}. "
            f"Allowed Praman categories: {PRAMAN_CATEGORIES}"
        )

    df["complaint_text"] = df["complaint_text"].astype(str)
    df["category"] = df["category"].astype(str)

    return df.reset_index(drop=True)


class ComplaintClassifier:
    """Praman ML Classifier for civic complaints using TF-IDF + Logistic Regression."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.lr_model: Optional[LogisticRegression] = None
        self.svm_model: Optional[CalibratedClassifierCV] = None
        self.classes_: Optional[np.ndarray] = None
        self.metrics_: Dict[str, Any] = {}

    def train(
        self,
        train_df: pd.DataFrame,
        ngram_range: Tuple[int, int] = (1, 2),
        max_features: int = 10000,
    ) -> "ComplaintClassifier":
        """Trains vectorizer and both classification models exclusively on the training set.

        Parameters
        ----------
        train_df : pd.DataFrame
            The training dataset (from praman_train.csv).
        ngram_range : tuple
            N-gram range for TF-IDF.
        max_features : int
            Max vocabulary features.
        """
        # Feature: Only complaint_text. Target: category.
        # Other fields (complaint_id, coordinates, locality, timestamp, status) are NOT classification features.
        X_text = train_df["complaint_text"].astype(str)
        y_train = train_df["category"].astype(str)

        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,
            stop_words="english",
        )
        X_train_vec = self.vectorizer.fit_transform(X_text)

        # 1. Primary Model: Logistic Regression with balanced class weights
        self.lr_model = LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=self.random_state,
        )
        self.lr_model.fit(X_train_vec, y_train)
        self.classes_ = self.lr_model.classes_

        # 2. Comparison Model: Linear SVM wrapped with CalibratedClassifierCV
        base_svm = LinearSVC(
            C=1.0,
            class_weight="balanced",
            random_state=self.random_state,
            dual="auto",
        )
        self.svm_model = CalibratedClassifierCV(
            estimator=base_svm,
            method="sigmoid",
            cv=3,
        )
        self.svm_model.fit(X_train_vec, y_train)

        return self

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Calculates real evaluation metrics without hardcoding."""
        labels = list(self.classes_)
        report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
            "f1_macro": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
            "precision_weighted": float(precision_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
            "recall_weighted": float(recall_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
            "f1_weighted": float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
            "confusion_matrix": cm,
            "classes": labels,
            "per_class": {
                label: {
                    "precision": float(report[label]["precision"]),
                    "recall": float(report[label]["recall"]),
                    "f1_score": float(report[label]["f1-score"]),
                    "support": int(report[label]["support"]),
                }
                for label in labels
            },
        }

    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, Any]:
        """Evaluates both models strictly on the holdout test dataset (praman_test.csv).

        Computes real Accuracy, Precision, Recall, F1, and Confusion Matrix.
        """
        if self.vectorizer is None or self.lr_model is None or self.svm_model is None:
            raise ValueError("Classifier is not trained. Call train() first.")

        X_test_vec = self.vectorizer.transform(test_df["complaint_text"].astype(str))
        y_test = test_df["category"].astype(str).to_numpy()

        y_pred_lr = self.lr_model.predict(X_test_vec)
        y_pred_svm = self.svm_model.predict(X_test_vec)

        metrics_lr = self._compute_metrics(y_test, y_pred_lr)
        metrics_svm = self._compute_metrics(y_test, y_pred_svm)

        self.metrics_ = {
            "test_sample_count": int(len(test_df)),
            "classes": list(self.classes_),
            "logistic_regression": metrics_lr,
            "linear_svm": metrics_svm,
        }

        return self.metrics_

    def predict(
        self,
        texts: Union[str, List[str], pd.Series],
        model: str = "logistic_regression",
    ) -> List[Dict[str, Any]]:
        """Predicts category and confidence per complaint.

        Parameters
        ----------
        texts : str or list of str or pd.Series
            Complaint text(s) to categorize.
        model : str
            Model to use: 'logistic_regression' (default) or 'linear_svm'.

        Returns
        -------
        List of dicts with 'complaint_text', 'predicted_category', and 'confidence'.
        """
        if self.vectorizer is None:
            raise ValueError("Vectorizer is not trained or loaded.")

        clf = self.lr_model if model == "logistic_regression" else self.svm_model
        if clf is None:
            raise ValueError(f"Model '{model}' is not trained or loaded.")

        if isinstance(texts, str):
            input_list = [texts]
        elif isinstance(texts, pd.Series):
            input_list = texts.tolist()
        else:
            input_list = list(texts)

        X_vec = self.vectorizer.transform(input_list)
        # Use predict_proba() for calibrated confidence scoring
        probas = clf.predict_proba(X_vec)
        pred_indices = np.argmax(probas, axis=1)

        results = []
        for text, prob_row, idx in zip(input_list, probas, pred_indices):
            predicted_category = self.classes_[idx]
            confidence = float(prob_row[idx])
            results.append({
                "complaint_text": text,
                "predicted_category": predicted_category,
                "confidence": round(confidence, 4),
            })

        return results

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "complaint_text",
        model: str = "logistic_regression",
    ) -> pd.DataFrame:
        """Attaches predicted_category and confidence columns to a complaints DataFrame."""
        predictions = self.predict(df[text_col], model=model)
        out_df = df.copy()
        out_df["predicted_category"] = [p["predicted_category"] for p in predictions]
        out_df["confidence"] = [p["confidence"] for p in predictions]
        return out_df

    def save(
        self,
        model_dir: str = "ml",
        model_filename: str = "model.pkl",
        vectorizer_filename: str = "vectorizer.pkl",
    ) -> Dict[str, str]:
        """Saves trained model and vectorizer as .pkl files along with metrics."""
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, model_filename)
        vec_path = os.path.join(model_dir, vectorizer_filename)
        svm_path = os.path.join(model_dir, "svm_model.pkl")
        metrics_path = os.path.join(model_dir, "metrics.json")

        with open(model_path, "wb") as f:
            pickle.dump(self.lr_model, f)

        with open(vec_path, "wb") as f:
            pickle.dump(self.vectorizer, f)

        with open(svm_path, "wb") as f:
            pickle.dump(self.svm_model, f)

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(self.metrics_, f, indent=2)

        return {
            "model": model_path,
            "vectorizer": vec_path,
            "svm_model": svm_path,
            "metrics": metrics_path,
        }

    def load(
        self,
        model_path: str = "ml/model.pkl",
        vectorizer_path: str = "ml/vectorizer.pkl",
        svm_path: Optional[str] = "ml/svm_model.pkl",
    ) -> None:
        """Loads trained model and vectorizer from disk for inference."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Vectorizer file not found: {vectorizer_path}")

        with open(model_path, "rb") as f:
            self.lr_model = pickle.load(f)

        with open(vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)

        self.classes_ = self.lr_model.classes_

        if svm_path and os.path.exists(svm_path):
            with open(svm_path, "rb") as f:
                self.svm_model = pickle.load(f)


def main():
    parser = argparse.ArgumentParser(description="Praman ML Complaint Classifier Training & Evaluation")
    parser.add_argument("--train-data", type=str, default="data/praman_train.csv", help="Path to praman_train.csv")
    parser.add_argument("--test-data", type=str, default="data/praman_test.csv", help="Path to praman_test.csv")
    parser.add_argument("--model-dir", type=str, default="ml", help="Directory to save model artifacts")
    args = parser.parse_args()

    print(f"Loading training dataset from: {args.train_data}")
    train_df = load_and_validate_dataset(args.train_data)
    print(f"Loaded {len(train_df)} validated training records across 6 categories.")

    print(f"\nLoading holdout test dataset from: {args.test_data}")
    test_df = load_and_validate_dataset(args.test_data)
    print(f"Loaded {len(test_df)} validated test records across 6 categories.")

    classifier = ComplaintClassifier(random_state=42)

    print("\nTraining TF-IDF + Logistic Regression (Primary) and Linear SVM (Comparison)...")
    classifier.train(train_df)

    print("Evaluating models strictly on test dataset...")
    metrics = classifier.evaluate(test_df)

    saved_artifacts = classifier.save(model_dir=args.model_dir)
    print(f"\nSaved artifacts: {saved_artifacts}")

    lr_m = metrics["logistic_regression"]
    svm_m = metrics["linear_svm"]

    print("\n" + "=" * 70)
    print("           PRAMAN INCIDENT CLASSIFIER - REAL EVALUATION RESULTS")
    print("=" * 70)
    print(f"{'Metric':<25} | {'Logistic Regression':<19} | {'Linear SVM':<15}")
    print("-" * 70)
    print(f"{'Accuracy':<25} | {lr_m['accuracy']:<19.4f} | {svm_m['accuracy']:<15.4f}")
    print(f"{'Precision (Macro)':<25} | {lr_m['precision_macro']:<19.4f} | {svm_m['precision_macro']:<15.4f}")
    print(f"{'Recall (Macro)':<25} | {lr_m['recall_macro']:<19.4f} | {svm_m['recall_macro']:<15.4f}")
    print(f"{'F1-Score (Macro)':<25} | {lr_m['f1_macro']:<19.4f} | {svm_m['f1_macro']:<15.4f}")
    print(f"{'Precision (Weighted)':<25} | {lr_m['precision_weighted']:<19.4f} | {svm_m['precision_weighted']:<15.4f}")
    print(f"{'Recall (Weighted)':<25} | {lr_m['recall_weighted']:<19.4f} | {svm_m['recall_weighted']:<15.4f}")
    print(f"{'F1-Score (Weighted)':<25} | {lr_m['f1_weighted']:<19.4f} | {svm_m['f1_weighted']:<15.4f}")
    print("=" * 70)

    print("\nConfusion Matrix (Logistic Regression):")
    print(f"Classes: {metrics['classes']}")
    for row in lr_m["confusion_matrix"]:
        print(f"  {row}")

    print("\nConfusion Matrix (Linear SVM):")
    for row in svm_m["confusion_matrix"]:
        print(f"  {row}")

    print("\nSample Backend Inference Test:")
    sample_queries = [
        "Big crater on main road causing bikes to fall and damaging cars.",
        "Garbage pile rotting near the market and not collected for 4 days.",
        "Drinking water main pipe broken and gushing heavily on footpath.",
        "Street light not working in residential lane, completely pitch dark.",
        "Sewage manhole overflowing dirty black water into houses.",
        "Fallen tree blocking the arterial carriageway creating traffic jam.",
    ]
    preds = classifier.predict(sample_queries, model="logistic_regression")
    for p in preds:
        print(f"  - \"{p['complaint_text']}\"")
        print(f"    --> {p['predicted_category']} (confidence: {p['confidence']:.4f})")


if __name__ == "__main__":
    main()
