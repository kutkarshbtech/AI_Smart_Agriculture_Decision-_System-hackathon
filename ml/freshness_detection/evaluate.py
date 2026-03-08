"""
Model evaluation and metrics for fruit freshness classification.

Generates:
    - Per-class precision, recall, F1
    - Confusion matrix
    - Classification report
    - Per-crop accuracy breakdown (fresh vs rotten for each fruit)
    - Confidence distribution analysis
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader

from dataset import (
    FreshnessDataset,
    get_val_transforms,
    NUM_CLASSES,
    CLASS_NAMES,
    IDX_TO_CLASS,
    FRUIT_CLASSES,
)
from model import FreshnessClassifier, build_model


class ModelEvaluator:
    """Comprehensive model evaluation with agriculture-relevant metrics."""

    def __init__(self, model: FreshnessClassifier, device: torch.device):
        self.model = model.to(device)
        self.model.eval()
        self.device = device

    @torch.no_grad()
    def evaluate(self, data_loader: DataLoader) -> Dict:
        """
        Run full evaluation on a dataset.

        Returns dict with:
            - overall_accuracy
            - per_class metrics (precision, recall, f1)
            - confusion_matrix
            - per_crop accuracy (e.g., accuracy for apple: fresh vs rotten)
            - confidence stats
        """
        all_preds = []
        all_labels = []
        all_probs = []

        for images, labels in data_loader:
            images = images.to(self.device)
            outputs = self.model(images)
            probs = torch.softmax(outputs, dim=1)
            preds = torch.argmax(probs, dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        all_probs = np.array(all_probs)

        results = {}

        # Overall accuracy
        results["overall_accuracy"] = float(np.mean(all_preds == all_labels) * 100)
        results["total_samples"] = len(all_labels)

        # Per-class metrics
        results["per_class"] = self._per_class_metrics(all_preds, all_labels)

        # Confusion matrix
        results["confusion_matrix"] = self._confusion_matrix(all_preds, all_labels)

        # Per-crop freshness accuracy (the key metric for our use case)
        results["per_crop_freshness"] = self._per_crop_freshness_accuracy(all_preds, all_labels)

        # Binary freshness accuracy (fresh vs rotten, ignoring specific fruit)
        results["binary_freshness"] = self._binary_freshness_accuracy(all_preds, all_labels)

        # Confidence analysis
        results["confidence_stats"] = self._confidence_analysis(all_preds, all_labels, all_probs)

        # Misclassification analysis (most common errors)
        results["top_misclassifications"] = self._misclassification_analysis(all_preds, all_labels)

        return results

    def _per_class_metrics(self, preds: np.ndarray, labels: np.ndarray) -> Dict:
        """Compute precision, recall, F1 for each class."""
        metrics = {}

        for idx, class_name in IDX_TO_CLASS.items():
            tp = np.sum((preds == idx) & (labels == idx))
            fp = np.sum((preds == idx) & (labels != idx))
            fn = np.sum((preds != idx) & (labels == idx))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            support = int(np.sum(labels == idx))

            metrics[class_name] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "support": support,
            }

        # Macro averages
        precisions = [m["precision"] for m in metrics.values() if m["support"] > 0]
        recalls = [m["recall"] for m in metrics.values() if m["support"] > 0]
        f1s = [m["f1_score"] for m in metrics.values() if m["support"] > 0]

        metrics["macro_avg"] = {
            "precision": round(np.mean(precisions), 4),
            "recall": round(np.mean(recalls), 4),
            "f1_score": round(np.mean(f1s), 4),
        }

        return metrics

    def _confusion_matrix(self, preds: np.ndarray, labels: np.ndarray) -> Dict:
        """Build confusion matrix."""
        matrix = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=int)
        for true, pred in zip(labels, preds):
            matrix[true][pred] += 1

        return {
            "matrix": matrix.tolist(),
            "class_names": CLASS_NAMES,
        }

    def _per_crop_freshness_accuracy(
        self, preds: np.ndarray, labels: np.ndarray
    ) -> Dict:
        """
        For each crop (apple, banana, etc.), compute accuracy of
        distinguishing fresh vs rotten. This is the key farmer-facing metric.
        """
        crops = set()
        for class_name, info in FRUIT_CLASSES.items():
            crops.add(info["crop"])

        crop_metrics = {}

        for crop in sorted(crops):
            fresh_class = f"fresh_{crop}"
            rotten_class = f"rotten_{crop}"

            if fresh_class not in CLASS_NAMES or rotten_class not in CLASS_NAMES:
                continue

            fresh_idx = CLASS_NAMES.index(fresh_class)
            rotten_idx = CLASS_NAMES.index(rotten_class)

            # Filter samples for this crop
            crop_mask = (labels == fresh_idx) | (labels == rotten_idx)
            crop_preds = preds[crop_mask]
            crop_labels = labels[crop_mask]

            if len(crop_labels) == 0:
                continue

            # Binary accuracy: did we correctly classify as fresh or rotten?
            crop_correct = np.sum(crop_preds == crop_labels)
            crop_total = len(crop_labels)

            # False freshness rate (said fresh when actually rotten — dangerous!)
            false_fresh = np.sum((crop_preds == fresh_idx) & (crop_labels == rotten_idx))
            # False rotten rate (said rotten when actually fresh — wasteful)
            false_rotten = np.sum((crop_preds == rotten_idx) & (crop_labels == fresh_idx))

            crop_metrics[crop] = {
                "accuracy": round(100.0 * crop_correct / crop_total, 2),
                "total_samples": int(crop_total),
                "false_fresh_rate": round(100.0 * false_fresh / crop_total, 2),
                "false_rotten_rate": round(100.0 * false_rotten / crop_total, 2),
                "hindi_name": FRUIT_CLASSES.get(fresh_class, {}).get("hindi", ""),
            }

        return crop_metrics

    def _binary_freshness_accuracy(
        self, preds: np.ndarray, labels: np.ndarray
    ) -> Dict:
        """
        Binary classification: fresh vs rotten (ignoring specific fruit type).
        This tells us if the model can reliably detect spoilage.
        """
        # Map each class to "fresh" or "rotten"
        pred_fresh = np.array([
            FRUIT_CLASSES[IDX_TO_CLASS[p]]["freshness"] == "fresh"
            for p in preds
        ])
        label_fresh = np.array([
            FRUIT_CLASSES[IDX_TO_CLASS[l]]["freshness"] == "fresh"
            for l in labels
        ])

        tp = np.sum(pred_fresh & label_fresh)  # Correctly identified fresh
        tn = np.sum(~pred_fresh & ~label_fresh)  # Correctly identified rotten
        fp = np.sum(pred_fresh & ~label_fresh)  # Said fresh but was rotten
        fn = np.sum(~pred_fresh & label_fresh)  # Said rotten but was fresh

        total = len(labels)
        accuracy = (tp + tn) / total * 100

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "accuracy": round(accuracy, 2),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives_dangerous": int(fp),  # Said fresh when rotten!
            "false_negatives_wasteful": int(fn),    # Said rotten when fresh
        }

    def _confidence_analysis(
        self, preds: np.ndarray, labels: np.ndarray, probs: np.ndarray
    ) -> Dict:
        """Analyze prediction confidence distribution."""
        # Confidence of predicted class
        pred_confidences = np.array([probs[i][p] for i, p in enumerate(preds)])

        correct_mask = preds == labels
        correct_conf = pred_confidences[correct_mask]
        incorrect_conf = pred_confidences[~correct_mask]

        return {
            "mean_confidence": round(float(np.mean(pred_confidences)), 4),
            "median_confidence": round(float(np.median(pred_confidences)), 4),
            "correct_mean_conf": round(float(np.mean(correct_conf)), 4) if len(correct_conf) > 0 else 0,
            "incorrect_mean_conf": round(float(np.mean(incorrect_conf)), 4) if len(incorrect_conf) > 0 else 0,
            "low_confidence_samples": int(np.sum(pred_confidences < 0.5)),
            "high_confidence_errors": int(np.sum((pred_confidences > 0.8) & ~correct_mask)),
        }

    def _misclassification_analysis(
        self, preds: np.ndarray, labels: np.ndarray, top_k: int = 5
    ) -> List[Dict]:
        """Find the most common misclassification pairs."""
        errors = defaultdict(int)
        for true, pred in zip(labels, preds):
            if true != pred:
                errors[(IDX_TO_CLASS[int(true)], IDX_TO_CLASS[int(pred)])] += 1

        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "true_class": true_cls,
                "predicted_class": pred_cls,
                "count": count,
            }
            for (true_cls, pred_cls), count in sorted_errors[:top_k]
        ]


def print_report(results: Dict) -> None:
    """Pretty-print evaluation results."""

    print(f"\n{'='*70}")
    print(f"  FRESHNESS DETECTION MODEL — EVALUATION REPORT")
    print(f"{'='*70}")

    print(f"\n📊 Overall Accuracy: {results['overall_accuracy']:.2f}%")
    print(f"   Total samples evaluated: {results['total_samples']}")

    # Binary freshness
    bf = results["binary_freshness"]
    print(f"\n🔬 Binary Freshness Detection (Fresh vs Rotten):")
    print(f"   Accuracy:  {bf['accuracy']:.2f}%")
    print(f"   Precision: {bf['precision']:.4f}")
    print(f"   Recall:    {bf['recall']:.4f}")
    print(f"   F1 Score:  {bf['f1_score']:.4f}")
    print(f"   ⚠️  False Fresh (dangerous): {bf['false_positives_dangerous']} cases")
    print(f"   ♻️  False Rotten (wasteful):  {bf['false_negatives_wasteful']} cases")

    # Per-crop
    print(f"\n🍎 Per-Crop Freshness Accuracy:")
    print(f"   {'Crop':<15} {'Accuracy':>10} {'False Fresh':>14} {'False Rotten':>14} {'Samples':>10}")
    print(f"   {'-'*63}")
    for crop, m in sorted(results["per_crop_freshness"].items()):
        print(
            f"   {crop:<15} {m['accuracy']:>9.1f}% "
            f"{m['false_fresh_rate']:>12.1f}% "
            f"{m['false_rotten_rate']:>12.1f}% "
            f"{m['total_samples']:>10}"
        )

    # Per-class
    print(f"\n📋 Per-Class Metrics:")
    print(f"   {'Class':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print(f"   {'-'*60}")
    for class_name in CLASS_NAMES:
        m = results["per_class"].get(class_name, {})
        if m.get("support", 0) > 0:
            print(
                f"   {class_name:<20} {m['precision']:>10.4f} "
                f"{m['recall']:>10.4f} {m['f1_score']:>10.4f} {m['support']:>10}"
            )

    macro = results["per_class"].get("macro_avg", {})
    print(f"   {'─'*60}")
    print(
        f"   {'Macro Average':<20} {macro.get('precision',0):>10.4f} "
        f"{macro.get('recall',0):>10.4f} {macro.get('f1_score',0):>10.4f}"
    )

    # Confidence
    conf = results["confidence_stats"]
    print(f"\n🔮 Confidence Analysis:")
    print(f"   Mean confidence:        {conf['mean_confidence']:.4f}")
    print(f"   Correct predictions:    {conf['correct_mean_conf']:.4f}")
    print(f"   Incorrect predictions:  {conf['incorrect_mean_conf']:.4f}")
    print(f"   Low confidence (<50%):  {conf['low_confidence_samples']}")
    print(f"   High-conf errors (>80%): {conf['high_confidence_errors']}")

    # Top misclassifications
    print(f"\n❌ Top Misclassifications:")
    for err in results["top_misclassifications"]:
        print(f"   {err['true_class']} → {err['predicted_class']}: {err['count']} times")

    print(f"\n{'='*70}")


def evaluate_model(
    model_path: str,
    data_dir: str,
    split: str = "test",
    batch_size: int = 32,
    output_path: str = None,
):
    """
    Load a trained model and evaluate it.

    Supports two layouts:
    - Pre-split: data_dir/test/ or data_dir/val/ directories exist
    - ULNN single-pool: data_dir/Fresh/ + data_dir/Rotten/ (re-creates the
      same deterministic train/val/test split used during training)

    Args:
        model_path: Path to .pth checkpoint
        data_dir: Dataset root directory
        split: "test" or "val"
        batch_size: Evaluation batch size
        output_path: Optional JSON path to save results
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model
    model = build_model(pretrained=False, freeze_backbone=False)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    print(f"Loaded model from: {model_path}")
    print(f"  Checkpoint val acc: {checkpoint.get('val_acc', 'N/A')}")

    # Load dataset — check if pre-split dir exists, otherwise use ULNN layout
    eval_dir = os.path.join(data_dir, split)
    fresh_dir = os.path.join(data_dir, "Fresh")
    rotten_dir = os.path.join(data_dir, "Rotten")

    if os.path.exists(eval_dir):
        # Pre-split layout
        dataset = FreshnessDataset(eval_dir, transform=get_val_transforms())
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    elif os.path.exists(fresh_dir) and os.path.exists(rotten_dir):
        # ULNN single-pool layout — recreate the same split with seed 42
        from dataset import create_data_loaders
        print(f"ULNN layout detected — recreating deterministic {split} split...")
        train_loader, val_loader, test_loader = create_data_loaders(
            data_dir, batch_size=batch_size, num_workers=4
        )
        if split == "test" and test_loader is not None:
            loader = test_loader
        elif split == "val":
            loader = val_loader
        else:
            print(f"No {split} split available. Using val split instead.")
            loader = val_loader
    else:
        print(f"Could not find dataset at: {data_dir}")
        return

    # Evaluate
    evaluator = ModelEvaluator(model, device)
    results = evaluator.evaluate(loader)

    # Print report
    print_report(results)

    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate freshness model")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to model checkpoint (.pth)")
    parser.add_argument("--data_dir", type=str, default="data/",
                        help="Dataset root directory")
    parser.add_argument("--split", type=str, default="test",
                        choices=["test", "val", "train"])
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--output", type=str, default=None,
                        help="Save results JSON to this path")
    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        data_dir=args.data_dir,
        split=args.split,
        batch_size=args.batch_size,
        output_path=args.output,
    )
