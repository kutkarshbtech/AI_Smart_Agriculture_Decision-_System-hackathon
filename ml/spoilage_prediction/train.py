"""
Training pipeline for spoilage prediction model.

Handles:
    - Dataset generation or loading
    - Model training with validation
    - Hyperparameter presets
    - Model checkpointing
    - Training history logging
    - Post-training evaluation summary

Usage:
    python train.py                                # default: balanced preset, 50k samples
    python train.py --preset fast --samples 10000  # quick training run
    python train.py --preset accurate --samples 100000  # full training
    python train.py --data_dir data/               # use existing dataset
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

from dataset import (
    generate_dataset,
    split_dataset,
    save_dataset,
    print_dataset_summary,
    FEATURE_COLUMNS,
    TARGET_COLUMNS,
    CROP_NAMES,
    RISK_LEVELS,
)
from model import SpoilageModel, build_model, PRESETS


class Trainer:
    """Orchestrates training pipeline for spoilage prediction."""

    def __init__(
        self,
        preset: str = "balanced",
        output_dir: str = "models",
        data_dir: str = "data",
        model_prefix: str = "spoilage_v1",
        **model_kwargs,
    ):
        self.preset = preset
        self.output_dir = Path(output_dir)
        self.data_dir = Path(data_dir)
        self.model_prefix = model_prefix
        self.model = build_model(preset=preset, **model_kwargs)
        self.history: Dict[str, Any] = {}

    def prepare_data(
        self,
        n_samples: int = 50000,
        seed: int = 42,
        force_regenerate: bool = False,
    ) -> tuple:
        """
        Load existing dataset or generate a new one.

        Returns:
            (train_df, val_df, test_df)
        """
        train_path = self.data_dir / "spoilage_train.csv"
        val_path = self.data_dir / "spoilage_val.csv"
        test_path = self.data_dir / "spoilage_test.csv"

        if not force_regenerate and all(p.exists() for p in [train_path, val_path, test_path]):
            print(f"Loading existing dataset from {self.data_dir}/")
            train_df = pd.read_csv(train_path)
            val_df = pd.read_csv(val_path)
            test_df = pd.read_csv(test_path)
            print(f"  Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}")
        else:
            print(f"Generating {n_samples:,} synthetic samples...")
            df = generate_dataset(n_samples=n_samples, seed=seed)
            print_dataset_summary(df)
            train_df, val_df, test_df = save_dataset(df, output_dir=str(self.data_dir))

        return train_df, val_df, test_df

    def train(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Train the model and return metrics."""
        print("\n" + "=" * 60)
        print(f"TRAINING — Preset: {self.preset}")
        print(f"  Estimators: {self.model.shelf_life_model.n_estimators}")
        print(f"  Max depth:  {self.model.shelf_life_model.max_depth}")
        print(f"  LR:         {self.model.shelf_life_model.learning_rate}")
        print("=" * 60)

        start_time = time.time()

        metrics = self.model.fit(
            train_df=train_df,
            val_df=val_df,
            verbose=verbose,
        )

        elapsed = time.time() - start_time

        # Quick evaluation on validation set
        val_metrics = self._evaluate_quick(val_df, label="Validation")

        self.history = {
            "preset": self.preset,
            "training_time_seconds": round(elapsed, 2),
            "n_train_samples": len(train_df),
            "n_val_samples": len(val_df),
            "training_metrics": metrics,
            "validation_metrics": val_metrics,
            "timestamp": datetime.now().isoformat(),
        }

        if verbose:
            print(f"\nTraining completed in {elapsed:.1f}s")
            self._print_validation_summary(val_metrics)

        return self.history

    def _evaluate_quick(self, df: pd.DataFrame, label: str = "Eval") -> Dict[str, float]:
        """Quick evaluation metrics on a dataset."""
        preds = self.model.predict(df)

        y_shelf = df["remaining_shelf_life_days"].values
        y_prob = df["spoilage_probability"].values
        y_risk = df["risk_level"].values

        # Shelf life metrics
        shelf_mae = np.mean(np.abs(preds["remaining_shelf_life_days"] - y_shelf))
        shelf_rmse = np.sqrt(np.mean((preds["remaining_shelf_life_days"] - y_shelf) ** 2))
        shelf_r2 = 1 - (
            np.sum((y_shelf - preds["remaining_shelf_life_days"]) ** 2) /
            np.sum((y_shelf - np.mean(y_shelf)) ** 2)
        )

        # Probability metrics
        prob_mae = np.mean(np.abs(preds["spoilage_probability"] - y_prob))
        prob_rmse = np.sqrt(np.mean((preds["spoilage_probability"] - y_prob) ** 2))

        # Risk classification
        risk_accuracy = np.mean(preds["risk_level"] == y_risk)

        # Adjacent accuracy (off by at most 1 level)
        risk_adjacent = np.mean(np.abs(preds["risk_level"] - y_risk) <= 1)

        return {
            "shelf_life_mae": round(float(shelf_mae), 3),
            "shelf_life_rmse": round(float(shelf_rmse), 3),
            "shelf_life_r2": round(float(shelf_r2), 4),
            "probability_mae": round(float(prob_mae), 4),
            "probability_rmse": round(float(prob_rmse), 4),
            "risk_accuracy": round(float(risk_accuracy), 4),
            "risk_adjacent_accuracy": round(float(risk_adjacent), 4),
        }

    def _print_validation_summary(self, metrics: Dict[str, float]):
        """Pretty-print validation results."""
        print("\n── Validation Results ──")
        print(f"  Shelf Life  — MAE: {metrics['shelf_life_mae']:.2f} days, "
              f"RMSE: {metrics['shelf_life_rmse']:.2f} days, "
              f"R²: {metrics['shelf_life_r2']:.4f}")
        print(f"  Probability — MAE: {metrics['probability_mae']:.4f}, "
              f"RMSE: {metrics['probability_rmse']:.4f}")
        print(f"  Risk Level  — Accuracy: {metrics['risk_accuracy']:.1%}, "
              f"Adjacent: {metrics['risk_adjacent_accuracy']:.1%}")

    def save_model(self):
        """Save model, history, and feature importance."""
        self.model.save(output_dir=str(self.output_dir), prefix=self.model_prefix)

        # Save training history
        history_path = self.output_dir / f"{self.model_prefix}_history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)
        print(f"Training history saved to {history_path}")

    def run(
        self,
        n_samples: int = 50000,
        seed: int = 42,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        """Full training pipeline: data → train → evaluate → save."""
        # 1. Prepare data
        train_df, val_df, test_df = self.prepare_data(
            n_samples=n_samples,
            seed=seed,
            force_regenerate=force_regenerate,
        )

        # 2. Train
        history = self.train(train_df, val_df)

        # 3. Test set evaluation
        print("\n── Test Set Evaluation ──")
        test_metrics = self._evaluate_quick(test_df, label="Test")
        self._print_validation_summary(test_metrics)
        history["test_metrics"] = test_metrics

        # 4. Feature importance
        importance = self.model.get_feature_importance()
        print("\n── Top Feature Importance (by gain) ──")
        for model_name in ["shelf_life", "probability", "risk"]:
            top_features = list(importance[model_name].items())[:5]
            print(f"  {model_name}:")
            for feat, score in top_features:
                print(f"    {feat:30s} {score:.4f}")

        # 5. Save
        self.save_model()

        return history


# ── CLI entry point ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Train spoilage prediction model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python train.py                                 # balanced preset
    python train.py --preset fast --samples 10000   # quick test
    python train.py --preset accurate --samples 100000  # best quality
    python train.py --data_dir data/ --no-regenerate    # reuse existing data
        """,
    )
    parser.add_argument("--preset", type=str, default="balanced",
                        choices=list(PRESETS.keys()),
                        help="Model complexity preset")
    parser.add_argument("--samples", type=int, default=50000,
                        help="Number of synthetic training samples")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--data_dir", type=str, default="data",
                        help="Data directory")
    parser.add_argument("--output_dir", type=str, default="models",
                        help="Model output directory")
    parser.add_argument("--prefix", type=str, default="spoilage_v1",
                        help="Model file prefix")
    parser.add_argument("--regenerate", action="store_true",
                        help="Force regenerate dataset even if exists")

    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  SwadeshAI — Spoilage Prediction Model   ║")
    print("╚══════════════════════════════════════════╝")
    print()

    trainer = Trainer(
        preset=args.preset,
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        model_prefix=args.prefix,
    )

    history = trainer.run(
        n_samples=args.samples,
        seed=args.seed,
        force_regenerate=args.regenerate,
    )

    print("\n✓ Training complete!")
    print(f"  Model saved to: {args.output_dir}/{args.prefix}_*.joblib")
    print(f"  History saved to: {args.output_dir}/{args.prefix}_history.json")


if __name__ == "__main__":
    main()
