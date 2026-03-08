"""
Evaluation and metrics for spoilage prediction model.

Generates:
    - Per-target regression metrics (MAE, RMSE, R², MAPE)
    - Risk classification report (accuracy, precision, recall, F1)
    - Per-crop accuracy breakdown
    - Confusion matrix
    - Feature importance analysis
    - Error distribution analysis

Usage:
    python evaluate.py                                      # evaluate on test set
    python evaluate.py --data data/spoilage_test.csv        # custom test data
    python evaluate.py --model_dir models/ --detailed       # full report
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

import numpy as np
import pandas as pd

from dataset import (
    FEATURE_COLUMNS,
    TARGET_COLUMNS,
    CROP_NAMES,
    CROP_PROFILES,
    RISK_LEVELS,
    IDX_TO_CROP,
)
from model import SpoilageModel


class ModelEvaluator:
    """Comprehensive evaluation of spoilage prediction model."""

    def __init__(self, model: SpoilageModel):
        self.model = model

    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, Any]:
        """Run full evaluation and return all metrics."""
        preds = self.model.predict(test_df)

        y_shelf = test_df["remaining_shelf_life_days"].values
        y_prob = test_df["spoilage_probability"].values
        y_risk = test_df["risk_level"].values

        results = {
            "n_samples": len(test_df),
            "shelf_life_metrics": self._regression_metrics(
                y_shelf, preds["remaining_shelf_life_days"], "shelf_life"
            ),
            "probability_metrics": self._regression_metrics(
                y_prob, preds["spoilage_probability"], "probability"
            ),
            "risk_metrics": self._classification_metrics(
                y_risk, preds["risk_level"], preds["risk_probabilities"]
            ),
            "per_crop_metrics": self._per_crop_metrics(test_df, preds),
            "error_analysis": self._error_analysis(test_df, preds),
        }

        return results

    def _regression_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray, name: str
    ) -> Dict[str, float]:
        """Compute regression metrics."""
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # MAPE (avoid division by zero)
        mask = y_true > 0.01
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = 0.0

        # Median absolute error
        medae = np.median(np.abs(y_true - y_pred))

        return {
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "r2": round(float(r2), 4),
            "mape": round(float(mape), 2),
            "median_ae": round(float(medae), 4),
            "max_error": round(float(np.max(np.abs(y_true - y_pred))), 4),
        }

    def _classification_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
    ) -> Dict[str, Any]:
        """Compute classification metrics for risk level."""
        accuracy = np.mean(y_true == y_pred)
        adjacent_accuracy = np.mean(np.abs(y_true - y_pred) <= 1)

        # Per-class metrics
        classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
        per_class = {}
        for cls in classes:
            tp = np.sum((y_pred == cls) & (y_true == cls))
            fp = np.sum((y_pred == cls) & (y_true != cls))
            fn = np.sum((y_pred != cls) & (y_true == cls))
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            support = int(np.sum(y_true == cls))

            per_class[RISK_LEVELS.get(int(cls), str(cls))] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": support,
            }

        # Confusion matrix
        n_classes = max(4, max(classes) + 1)
        confusion = np.zeros((n_classes, n_classes), dtype=int)
        for true, pred in zip(y_true, y_pred):
            confusion[int(true)][int(pred)] += 1

        # Weighted F1
        total_support = sum(c["support"] for c in per_class.values())
        weighted_f1 = sum(
            c["f1"] * c["support"] / total_support
            for c in per_class.values()
        ) if total_support > 0 else 0.0

        return {
            "accuracy": round(float(accuracy), 4),
            "adjacent_accuracy": round(float(adjacent_accuracy), 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "per_class": per_class,
            "confusion_matrix": confusion.tolist(),
        }

    def _per_crop_metrics(
        self, test_df: pd.DataFrame, preds: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, float]]:
        """Compute metrics broken down by crop type."""
        crop_metrics = {}

        for crop_name in CROP_NAMES:
            mask = test_df["crop_type"].values == crop_name
            if mask.sum() == 0:
                continue

            y_shelf = test_df["remaining_shelf_life_days"].values[mask]
            p_shelf = preds["remaining_shelf_life_days"][mask]

            y_prob = test_df["spoilage_probability"].values[mask]
            p_prob = preds["spoilage_probability"][mask]

            y_risk = test_df["risk_level"].values[mask]
            p_risk = preds["risk_level"][mask]

            crop_metrics[crop_name] = {
                "n_samples": int(mask.sum()),
                "shelf_life_mae": round(float(np.mean(np.abs(y_shelf - p_shelf))), 2),
                "probability_mae": round(float(np.mean(np.abs(y_prob - p_prob))), 4),
                "risk_accuracy": round(float(np.mean(y_risk == p_risk)), 4),
                "hindi": CROP_PROFILES[crop_name]["hindi"],
                "category": CROP_PROFILES[crop_name]["category"],
            }

        return crop_metrics

    def _error_analysis(
        self, test_df: pd.DataFrame, preds: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Analyze error patterns."""
        y_shelf = test_df["remaining_shelf_life_days"].values
        p_shelf = preds["remaining_shelf_life_days"]
        errors = p_shelf - y_shelf  # positive = overestimate

        y_risk = test_df["risk_level"].values
        p_risk = preds["risk_level"]
        risk_errors = p_risk.astype(int) - y_risk.astype(int)

        return {
            "shelf_life": {
                "mean_error": round(float(np.mean(errors)), 3),
                "std_error": round(float(np.std(errors)), 3),
                "overestimates_pct": round(float(np.mean(errors > 0) * 100), 1),
                "underestimates_pct": round(float(np.mean(errors < 0) * 100), 1),
                "exact_pct": round(float(np.mean(np.abs(errors) < 0.5) * 100), 1),
                "within_1_day_pct": round(float(np.mean(np.abs(errors) <= 1) * 100), 1),
                "within_3_days_pct": round(float(np.mean(np.abs(errors) <= 3) * 100), 1),
            },
            "risk_level": {
                "overestimates_pct": round(float(np.mean(risk_errors > 0) * 100), 1),
                "underestimates_pct": round(float(np.mean(risk_errors < 0) * 100), 1),
                "off_by_2_or_more_pct": round(float(np.mean(np.abs(risk_errors) >= 2) * 100), 1),
            },
        }

    def print_report(self, results: Dict[str, Any], detailed: bool = False):
        """Print formatted evaluation report."""
        print("\n" + "=" * 70)
        print("  SPOILAGE PREDICTION MODEL — EVALUATION REPORT")
        print("=" * 70)
        print(f"\n  Test samples: {results['n_samples']:,}")

        # Shelf life
        sl = results["shelf_life_metrics"]
        print("\n── Shelf Life Prediction (Regression) ──")
        print(f"  MAE:        {sl['mae']:.2f} days")
        print(f"  RMSE:       {sl['rmse']:.2f} days")
        print(f"  R²:         {sl['r2']:.4f}")
        print(f"  MAPE:       {sl['mape']:.1f}%")
        print(f"  Median AE:  {sl['median_ae']:.2f} days")
        print(f"  Max Error:  {sl['max_error']:.2f} days")

        # Probability
        pr = results["probability_metrics"]
        print("\n── Spoilage Probability (Regression) ──")
        print(f"  MAE:        {pr['mae']:.4f}")
        print(f"  RMSE:       {pr['rmse']:.4f}")
        print(f"  R²:         {pr['r2']:.4f}")

        # Risk classification
        rc = results["risk_metrics"]
        print("\n── Risk Level Classification ──")
        print(f"  Accuracy:          {rc['accuracy']:.1%}")
        print(f"  Adjacent Accuracy: {rc['adjacent_accuracy']:.1%}")
        print(f"  Weighted F1:       {rc['weighted_f1']:.4f}")

        print(f"\n  {'Class':12s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'Support':>8s}")
        print(f"  {'-'*44}")
        for cls_name, m in rc["per_class"].items():
            print(f"  {cls_name:12s} {m['precision']:8.4f} {m['recall']:8.4f} "
                  f"{m['f1']:8.4f} {m['support']:8d}")

        # Confusion matrix
        print(f"\n  Confusion Matrix (rows=true, cols=predicted):")
        labels = [RISK_LEVELS.get(i, str(i))[:6] for i in range(4)]
        print(f"  {'':10s} " + " ".join(f"{l:>8s}" for l in labels))
        for i, row in enumerate(rc["confusion_matrix"]):
            print(f"  {RISK_LEVELS.get(i, str(i)):10s} " +
                  " ".join(f"{v:8d}" for v in row[:4]))

        # Error analysis
        ea = results["error_analysis"]
        print("\n── Error Analysis ──")
        sl_ea = ea["shelf_life"]
        print(f"  Shelf life within 1 day: {sl_ea['within_1_day_pct']:.1f}%")
        print(f"  Shelf life within 3 days: {sl_ea['within_3_days_pct']:.1f}%")
        print(f"  Over-estimates: {sl_ea['overestimates_pct']:.1f}%")
        print(f"  Under-estimates: {sl_ea['underestimates_pct']:.1f}%")
        rl_ea = ea["risk_level"]
        print(f"  Risk off by ≥2 levels: {rl_ea['off_by_2_or_more_pct']:.1f}%")

        if detailed:
            # Per-crop breakdown
            print("\n── Per-Crop Accuracy ──")
            print(f"  {'Crop':16s} {'Hindi':12s} {'Cat':10s} {'N':>6s} "
                  f"{'SL MAE':>8s} {'Prob MAE':>9s} {'Risk Acc':>9s}")
            print(f"  {'-'*70}")
            for crop_name, m in sorted(results["per_crop_metrics"].items()):
                print(f"  {crop_name:16s} {m['hindi']:12s} {m['category']:10s} "
                      f"{m['n_samples']:6d} {m['shelf_life_mae']:8.2f} "
                      f"{m['probability_mae']:9.4f} {m['risk_accuracy']:9.1%}")

        print("\n" + "=" * 70)


def save_results(results: Dict[str, Any], output_path: str):
    """Save evaluation results to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {output_path}")


# ── CLI entry point ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate spoilage prediction model")
    parser.add_argument("--data", type=str, default="data/spoilage_test.csv",
                        help="Test dataset CSV path")
    parser.add_argument("--model_dir", type=str, default="models",
                        help="Model directory")
    parser.add_argument("--prefix", type=str, default="spoilage_v1",
                        help="Model file prefix")
    parser.add_argument("--output", type=str, default=None,
                        help="Save results JSON to this path")
    parser.add_argument("--detailed", action="store_true",
                        help="Show detailed per-crop breakdown")

    args = parser.parse_args()

    # Load test data
    print(f"Loading test data from {args.data}...")
    test_df = pd.read_csv(args.data)
    print(f"  {len(test_df):,} samples loaded")

    # Load model
    model = SpoilageModel.load(model_dir=args.model_dir, prefix=args.prefix)

    # Evaluate
    evaluator = ModelEvaluator(model)
    results = evaluator.evaluate(test_df)
    evaluator.print_report(results, detailed=args.detailed)

    # Save
    if args.output:
        save_results(results, args.output)
    else:
        output_path = Path(args.model_dir) / f"{args.prefix}_eval_results.json"
        save_results(results, str(output_path))


if __name__ == "__main__":
    main()
