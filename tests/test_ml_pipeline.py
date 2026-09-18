"""Automated tests for Praman ML pipeline and dataset validation."""

import os
import shutil
import tempfile
import unittest
import pandas as pd

from ml.classifier import (
    PRAMAN_CATEGORIES,
    REQUIRED_COLUMNS,
    ComplaintClassifier,
    load_and_validate_dataset,
)
from scripts.generate_data import CATEGORIES, LOCALITIES, generate_complaints_data


class TestPramanDatasetValidation(unittest.TestCase):
    """Tests schema, category, and completeness validation on Praman CSV datasets."""

    def test_train_dataset_loads_and_validates(self):
        train_df = load_and_validate_dataset("data/praman_train.csv")
        self.assertGreater(len(train_df), 7000)
        self.assertTrue(all(col in train_df.columns for col in REQUIRED_COLUMNS))
        self.assertTrue(set(train_df["category"].unique()).issubset(set(PRAMAN_CATEGORIES)))

    def test_test_dataset_loads_and_validates(self):
        test_df = load_and_validate_dataset("data/praman_test.csv")
        self.assertGreater(len(test_df), 1800)
        self.assertTrue(all(col in test_df.columns for col in REQUIRED_COLUMNS))
        self.assertTrue(set(test_df["category"].unique()).issubset(set(PRAMAN_CATEGORIES)))

    def test_validation_rejects_missing_column(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            f.write("complaint_id,category\nC1,Garbage\n")
            temp_path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_and_validate_dataset(temp_path)
            self.assertIn("missing required schema columns", str(ctx.exception))
        finally:
            os.remove(temp_path)

    def test_validation_rejects_invalid_category(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            cols = ",".join(REQUIRED_COLUMNS)
            f.write(f"{cols}\nC1,Noise issue,Noise Pollution,12.9,77.5,Area A,2026-01-01,Open\n")
            temp_path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_and_validate_dataset(temp_path)
            self.assertIn("unauthorized categories", str(ctx.exception))
        finally:
            os.remove(temp_path)


class TestPramanClassifier(unittest.TestCase):
    """Tests training on praman_train.csv and evaluation on praman_test.csv."""

    @classmethod
    def setUpClass(cls):
        cls.train_df = load_and_validate_dataset("data/praman_train.csv")
        cls.test_df = load_and_validate_dataset("data/praman_test.csv")
        cls.classifier = ComplaintClassifier(random_state=42)
        cls.classifier.train(cls.train_df)
        cls.metrics = cls.classifier.evaluate(cls.test_df)
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_real_metrics_computed(self):
        self.assertIn("logistic_regression", self.metrics)
        self.assertIn("linear_svm", self.metrics)

        lr_m = self.metrics["logistic_regression"]
        svm_m = self.metrics["linear_svm"]

        # Ensure real accuracy > 90%
        self.assertGreater(lr_m["accuracy"], 0.90)
        self.assertGreater(svm_m["accuracy"], 0.90)

        # Confusion matrix checks
        self.assertEqual(len(lr_m["confusion_matrix"]), 6)
        self.assertEqual(len(lr_m["confusion_matrix"][0]), 6)
        self.assertEqual(len(svm_m["confusion_matrix"]), 6)

        # Ensure all 6 categories are in per_class metrics
        for cat in PRAMAN_CATEGORIES:
            self.assertIn(cat, lr_m["per_class"])
            self.assertIn(cat, svm_m["per_class"])

    def test_predictions_and_confidence(self):
        samples = [
            "Heavy water leakage from underground municipal pipe.",
            "Street light not working in dark residential street.",
        ]
        preds = self.classifier.predict(samples, model="logistic_regression")
        self.assertEqual(len(preds), 2)
        self.assertEqual(preds[0]["predicted_category"], "Water Leakage")
        self.assertEqual(preds[1]["predicted_category"], "Streetlight")
        self.assertGreaterEqual(preds[0]["confidence"], 0.0)
        self.assertLessEqual(preds[0]["confidence"], 1.0)

    def test_predict_dataframe(self):
        sample_df = pd.DataFrame({
            "complaint_text": ["Sewage drain overflowing with foul smell.", "Deep pothole on highway."]
        })
        enriched = self.classifier.predict_dataframe(sample_df, model="logistic_regression")
        self.assertIn("predicted_category", enriched.columns)
        self.assertIn("confidence", enriched.columns)
        self.assertEqual(enriched.iloc[0]["predicted_category"], "Sewage")
        self.assertEqual(enriched.iloc[1]["predicted_category"], "Pothole")

    def test_save_and_load_artifacts(self):
        saved = self.classifier.save(
            model_dir=self.temp_dir,
            model_filename="model.pkl",
            vectorizer_filename="vectorizer.pkl",
        )
        self.assertTrue(os.path.exists(saved["model"]))
        self.assertTrue(os.path.exists(saved["vectorizer"]))

        loaded_clf = ComplaintClassifier()
        loaded_clf.load(
            model_path=saved["model"],
            vectorizer_path=saved["vectorizer"],
            svm_path=saved["svm_model"],
        )
        res = loaded_clf.predict("Pile of rotting garbage on the road.", model="logistic_regression")
        self.assertEqual(res[0]["predicted_category"], "Garbage")
        self.assertGreaterEqual(res[0]["confidence"], 0.50)


if __name__ == "__main__":
    unittest.main()
