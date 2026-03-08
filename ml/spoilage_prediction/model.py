"""
Spoilage prediction model — XGBoost ensemble.

Architecture:
    - XGBRegressor for remaining_shelf_life_days (regression)
    - XGBRegressor for spoilage_probability (regression, 0-1)
    - XGBClassifier for risk_level (multiclass: low/medium/high/critical)

Why XGBoost:
    - Handles tabular data with mixed feature types
    - Built-in feature importance for explainability
    - Fast training and inference on CPU
    - Small model size for deployment (< 5 MB)
    - Handles the non-linear relationships in spoilage science

Usage:
    from model import SpoilageModel
    model = SpoilageModel()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
"""

import json
import joblib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from xgboost import XGBRegressor, XGBClassifier

from dataset import FEATURE_COLUMNS, TARGET_COLUMNS, RISK_LEVELS, NUM_CROPS


class SpoilageModel:
    """
    Multi-output spoilage prediction model.

    Three sub-models:
        1. shelf_life_model  — Predicts remaining shelf life (days)
        2. probability_model — Predicts spoilage probability (0-1)
        3. risk_model        — Classifies risk level (0-3)
    """

    def __init__(
        self,
        # Shared hyperparameters
        n_estimators: int = 500,
        max_depth: int = 8,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        min_child_weight: int = 5,
        reg_alpha: float = 0.1,
        reg_lambda: float = 1.0,
        random_state: int = 42,
        # Override per sub-model
        shelf_life_params: Optional[Dict] = None,
        probability_params: Optional[Dict] = None,
        risk_params: Optional[Dict] = None,
    ):
        base_params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "min_child_weight": min_child_weight,
            "reg_alpha": reg_alpha,
            "reg_lambda": reg_lambda,
            "random_state": random_state,
            "n_jobs": -1,
            "verbosity": 0,
        }

        # Shelf life regressor
        sl_params = {**base_params}
        sl_params["objective"] = "reg:squarederror"
        if shelf_life_params:
            sl_params.update(shelf_life_params)
        self.shelf_life_model = XGBRegressor(**sl_params)

        # Probability regressor (bounded 0-1)
        prob_params = {**base_params}
        prob_params["objective"] = "reg:logistic"  # sigmoid output
        if probability_params:
            prob_params.update(probability_params)
        self.probability_model = XGBRegressor(**prob_params)

        # Risk classifier
        risk_params_final = {**base_params}
        risk_params_final["objective"] = "multi:softprob"
        risk_params_final["num_class"] = 4
        risk_params_final["eval_metric"] = "mlogloss"
        if risk_params:
            risk_params_final.update(risk_params)
        self.risk_model = XGBClassifier(**risk_params_final)

        self.feature_columns = FEATURE_COLUMNS
        self.is_fitted = False
        self.training_metadata: Dict[str, Any] = {}

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract and validate feature columns from dataframe."""
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")
        return df[self.feature_columns].values.astype(np.float32)

    def _prepare_targets(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract target columns."""
        y_shelf = df["remaining_shelf_life_days"].values.astype(np.float32)
        y_prob = df["spoilage_probability"].values.astype(np.float32)
        y_risk = df["risk_level"].values.astype(np.int32)
        return y_shelf, y_prob, y_risk

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        early_stopping_rounds: int = 30,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Train all three sub-models.

        Args:
            train_df: Training data with feature and target columns.
            val_df: Validation data for early stopping.
            early_stopping_rounds: Patience for early stopping.
            verbose: Print training progress.

        Returns:
            Training metrics dict.
        """
        X_train = self._prepare_features(train_df)
        y_shelf_train, y_prob_train, y_risk_train = self._prepare_targets(train_df)

        fit_params = {}
        if val_df is not None:
            X_val = self._prepare_features(val_df)
            y_shelf_val, y_prob_val, y_risk_val = self._prepare_targets(val_df)
            fit_params["eval_set"] = None  # set per model below

        metrics = {}

        # 1. Train shelf life model
        if verbose:
            print("Training shelf life regressor...")
        sl_fit = {}
        if val_df is not None:
            sl_fit["eval_set"] = [(X_val, y_shelf_val)]
        self.shelf_life_model.fit(X_train, y_shelf_train, **sl_fit)
        metrics["shelf_life"] = {"trained": True}

        # 2. Train probability model
        if verbose:
            print("Training spoilage probability regressor...")
        prob_fit = {}
        if val_df is not None:
            prob_fit["eval_set"] = [(X_val, y_prob_val)]
        self.probability_model.fit(X_train, y_prob_train, **prob_fit)
        metrics["probability"] = {"trained": True}

        # 3. Train risk classifier
        if verbose:
            print("Training risk level classifier...")
        risk_fit = {}
        if val_df is not None:
            risk_fit["eval_set"] = [(X_val, y_risk_val)]
        self.risk_model.fit(X_train, y_risk_train, **risk_fit)
        metrics["risk"] = {"trained": True}

        self.is_fitted = True

        # Store metadata
        self.training_metadata = {
            "n_train_samples": len(train_df),
            "n_val_samples": len(val_df) if val_df is not None else 0,
            "feature_columns": self.feature_columns,
            "n_features": len(self.feature_columns),
        }

        if verbose:
            print(f"All models trained on {len(train_df):,} samples.")

        return metrics

    def predict(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Predict spoilage metrics for input data.

        Returns:
            Dict with:
                - remaining_shelf_life_days: np.ndarray (float)
                - spoilage_probability: np.ndarray (float, 0-1)
                - risk_level: np.ndarray (int, 0-3)
                - risk_probabilities: np.ndarray (float, shape: [n, 4])
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X = self._prepare_features(df)

        # Predict
        shelf_life = self.shelf_life_model.predict(X)
        shelf_life = np.maximum(shelf_life, 0)  # can't be negative

        spoilage_prob = self.probability_model.predict(X)
        spoilage_prob = np.clip(spoilage_prob, 0.01, 0.99)

        risk_level = self.risk_model.predict(X).astype(int)
        risk_probs = self.risk_model.predict_proba(X)

        return {
            "remaining_shelf_life_days": np.round(shelf_life, 1),
            "spoilage_probability": np.round(spoilage_prob, 4),
            "risk_level": risk_level,
            "risk_probabilities": np.round(risk_probs, 4),
        }

    def predict_single(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict for a single sample from a features dict.

        Args:
            features: Dict with keys matching FEATURE_COLUMNS.

        Returns:
            Dict with prediction results.
        """
        row = {col: features.get(col, 0.0) for col in self.feature_columns}
        df = pd.DataFrame([row])
        preds = self.predict(df)

        risk_idx = int(preds["risk_level"][0])
        return {
            "remaining_shelf_life_days": float(preds["remaining_shelf_life_days"][0]),
            "spoilage_probability": float(preds["spoilage_probability"][0]),
            "risk_level": risk_idx,
            "risk_label": RISK_LEVELS[risk_idx],
            "risk_probabilities": {
                RISK_LEVELS[i]: float(preds["risk_probabilities"][0][i])
                for i in range(4)
            },
        }

    def get_feature_importance(self, importance_type: str = "gain") -> Dict[str, Dict[str, float]]:
        """
        Get feature importance from all three models.

        Args:
            importance_type: "gain", "weight", or "cover".

        Returns:
            Dict with importance scores per model per feature.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")

        result = {}
        for name, model in [
            ("shelf_life", self.shelf_life_model),
            ("probability", self.probability_model),
            ("risk", self.risk_model),
        ]:
            importances = model.get_booster().get_score(importance_type=importance_type)
            # Map f0,f1,... to feature names
            named = {}
            for feat_key, score in importances.items():
                idx = int(feat_key.replace("f", ""))
                if idx < len(self.feature_columns):
                    named[self.feature_columns[idx]] = round(score, 4)
            # Sort by importance
            named = dict(sorted(named.items(), key=lambda x: x[1], reverse=True))
            result[name] = named

        return result

    def save(self, output_dir: str = "models", prefix: str = "spoilage_v1"):
        """Save all three models + metadata."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save models
        joblib.dump(self.shelf_life_model, output_path / f"{prefix}_shelf_life.joblib")
        joblib.dump(self.probability_model, output_path / f"{prefix}_probability.joblib")
        joblib.dump(self.risk_model, output_path / f"{prefix}_risk.joblib")

        # Save metadata
        meta = {
            **self.training_metadata,
            "model_prefix": prefix,
            "feature_columns": self.feature_columns,
            "risk_levels": RISK_LEVELS,
        }
        with open(output_path / f"{prefix}_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        # Save feature importance
        importance = self.get_feature_importance()
        with open(output_path / f"{prefix}_feature_importance.json", "w") as f:
            json.dump(importance, f, indent=2)

        total_size = sum(
            (output_path / f"{prefix}_{name}.joblib").stat().st_size
            for name in ["shelf_life", "probability", "risk"]
        )
        print(f"Models saved to {output_path}/ ({total_size / 1024 / 1024:.1f} MB total)")

    @classmethod
    def load(cls, model_dir: str = "models", prefix: str = "spoilage_v1") -> "SpoilageModel":
        """Load a saved model."""
        model_path = Path(model_dir)

        instance = cls()
        instance.shelf_life_model = joblib.load(model_path / f"{prefix}_shelf_life.joblib")
        instance.probability_model = joblib.load(model_path / f"{prefix}_probability.joblib")
        instance.risk_model = joblib.load(model_path / f"{prefix}_risk.joblib")

        # Load metadata
        meta_path = model_path / f"{prefix}_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                instance.training_metadata = json.load(f)
            instance.feature_columns = instance.training_metadata.get(
                "feature_columns", FEATURE_COLUMNS
            )

        instance.is_fitted = True
        print(f"Models loaded from {model_path}/")
        return instance


# ── Hyperparameter presets ──────────────────────────────────────────

PRESETS = {
    "fast": {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.1,
    },
    "balanced": {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
    },
    "accurate": {
        "n_estimators": 1000,
        "max_depth": 10,
        "learning_rate": 0.02,
        "subsample": 0.7,
        "colsample_bytree": 0.7,
    },
}


def build_model(preset: str = "balanced", **kwargs) -> SpoilageModel:
    """
    Factory function to create a SpoilageModel with a preset.

    Args:
        preset: One of "fast", "balanced", "accurate".
        **kwargs: Override any preset parameter.

    Returns:
        Configured SpoilageModel instance.
    """
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {list(PRESETS.keys())}")

    params = {**PRESETS[preset], **kwargs}
    return SpoilageModel(**params)
