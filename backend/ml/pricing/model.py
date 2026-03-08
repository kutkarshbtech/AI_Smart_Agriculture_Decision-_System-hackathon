"""
XGBoost-based price prediction model.
Provides:
  - Ideal selling price prediction
  - Confidence interval (min/max recommended range)
  - Seller-protected floor price (MSP or cost-based)
  - Feature importance for explainability
"""
import os
import math
import random
import numpy as np
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

from .features import (
    build_features,
    features_to_vector,
    FEATURE_NAMES,
    MSP_DATA,
    PERISHABILITY_INDEX,
    SHELF_LIFE_DAYS,
    get_season,
    remaining_shelf_life_ratio,
)


# ---------------------------------------------------------------------------
# Market simulation data (same as pricing_service.py for consistency)
# ---------------------------------------------------------------------------
MARKET_PRICE_DATA = {
    "tomato": {"base_price": 25, "volatility": 0.3, "season_factor": {"summer": 1.4, "winter": 0.8, "monsoon": 1.6, "spring": 1.0}},
    "potato": {"base_price": 18, "volatility": 0.15, "season_factor": {"summer": 1.1, "winter": 0.9, "monsoon": 1.0, "spring": 1.0}},
    "onion": {"base_price": 22, "volatility": 0.4, "season_factor": {"summer": 1.5, "winter": 0.7, "monsoon": 1.8, "spring": 1.0}},
    "banana": {"base_price": 30, "volatility": 0.1, "season_factor": {"summer": 1.0, "winter": 1.0, "monsoon": 1.1, "spring": 1.0}},
    "mango": {"base_price": 60, "volatility": 0.25, "season_factor": {"summer": 0.7, "winter": 2.0, "monsoon": 1.3, "spring": 1.5}},
    "apple": {"base_price": 80, "volatility": 0.15, "season_factor": {"summer": 1.3, "winter": 0.9, "monsoon": 1.1, "spring": 1.0}},
    "rice": {"base_price": 35, "volatility": 0.08, "season_factor": {"summer": 1.0, "winter": 1.0, "monsoon": 0.9, "spring": 1.1}},
    "wheat": {"base_price": 25, "volatility": 0.07, "season_factor": {"summer": 1.1, "winter": 1.0, "monsoon": 1.0, "spring": 0.9}},
    "cauliflower": {"base_price": 20, "volatility": 0.35, "season_factor": {"summer": 1.8, "winter": 0.6, "monsoon": 1.5, "spring": 1.0}},
    "spinach": {"base_price": 25, "volatility": 0.25, "season_factor": {"summer": 1.4, "winter": 0.8, "monsoon": 1.3, "spring": 1.0}},
    "capsicum": {"base_price": 40, "volatility": 0.3, "season_factor": {"summer": 1.2, "winter": 0.9, "monsoon": 1.4, "spring": 1.0}},
    "okra": {"base_price": 30, "volatility": 0.25, "season_factor": {"summer": 0.8, "winter": 1.5, "monsoon": 1.0, "spring": 1.0}},
    "brinjal": {"base_price": 20, "volatility": 0.2, "season_factor": {"summer": 1.1, "winter": 0.9, "monsoon": 1.2, "spring": 1.0}},
    "guava": {"base_price": 35, "volatility": 0.2, "season_factor": {"summer": 1.3, "winter": 0.8, "monsoon": 1.1, "spring": 1.0}},
    "grape": {"base_price": 50, "volatility": 0.2, "season_factor": {"summer": 1.5, "winter": 0.8, "monsoon": 1.2, "spring": 0.9}},
    "carrot": {"base_price": 25, "volatility": 0.15, "season_factor": {"summer": 1.2, "winter": 0.8, "monsoon": 1.1, "spring": 1.0}},
}

CROP_LIST = list(MARKET_PRICE_DATA.keys())


class PricePredictionModel:
    """
    XGBoost-based model for predicting ideal crop selling prices.

    Falls back to a rule-based heuristic when the trained model is not available.
    """

    MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
    MODEL_PATH = os.path.join(MODEL_DIR, "price_model.json")
    META_PATH = os.path.join(MODEL_DIR, "price_model_meta.pkl")

    def __init__(self):
        self.model: Optional[Any] = None
        self.is_trained = False
        self._try_load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _try_load(self):
        """Try to load a previously saved model from disk."""
        if not HAS_XGB:
            return
        if os.path.exists(self.MODEL_PATH):
            try:
                self.model = xgb.Booster()
                self.model.load_model(self.MODEL_PATH)
                self.is_trained = True
                print(f"[PricePredictionModel] Loaded model from {self.MODEL_PATH}")
                # Sanity check: test prediction to guard against version mismatch
                if not self._sanity_check():
                    print("[PricePredictionModel] Sanity check FAILED — model will be retrained")
                    self.model = None
                    self.is_trained = False
            except Exception as e:
                print(f"[PricePredictionModel] Failed to load model: {e}")
                self.model = None
                self.is_trained = False

    def _sanity_check(self) -> bool:
        """Verify the loaded model gives reasonable predictions."""
        try:
            from .features import build_features, features_to_vector
            features = build_features(
                crop_name="tomato", quantity_kg=100,
                harvest_date=date.today(),
                market_price_today=25.0,
                market_price_avg_7d=24.0,
                demand_index=0.5,
            )
            vec = features_to_vector(features)
            dmat = xgb.DMatrix(
                np.array([vec], dtype=np.float32), feature_names=FEATURE_NAMES
            )
            pred = float(self.model.predict(dmat)[0])
            # With market_price ~25 ₹/kg, prediction should be >5 ₹/kg
            if pred < 5.0:
                print(f"[PricePredictionModel] Sanity check: tomato@25₹ predicted {pred:.2f} (too low)")
                return False
            print(f"[PricePredictionModel] Sanity check passed: tomato@25₹ → {pred:.2f}₹/kg")
            return True
        except Exception as e:
            print(f"[PricePredictionModel] Sanity check error: {e}")
            return False

    def save(self):
        """Persist the trained model to disk."""
        if self.model is None:
            return
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        self.model.save_model(self.MODEL_PATH)
        print(f"[PricePredictionModel] Model saved to {self.MODEL_PATH}")

    # ------------------------------------------------------------------
    # Training (synthetic data for hackathon; replace with real data)
    # ------------------------------------------------------------------
    def _generate_synthetic_data(self, n_samples: int = 10_000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data."""
        rng = np.random.RandomState(42)
        X_rows: List[List[float]] = []
        y_rows: List[float] = []

        for _ in range(n_samples):
            crop = rng.choice(CROP_LIST)
            crop_data = MARKET_PRICE_DATA[crop]

            # Random date in last 2 years
            days_ago = rng.randint(0, 730)
            ref_date = date.today() - timedelta(days=days_ago)
            harvest_offset = rng.randint(0, SHELF_LIFE_DAYS.get(crop, 7))
            harvest_date = ref_date - timedelta(days=harvest_offset)

            quantity = rng.uniform(5, 5000)
            storage_type = rng.choice(["ambient", "cold", "controlled"])
            quality = rng.choice(["excellent", "good", "average", "poor"])
            spoilage_risk = rng.choice(["low", "medium", "high", "critical"])
            spoilage_prob = {"low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.9}[spoilage_risk]

            season = get_season(ref_date)
            season_mult = crop_data["season_factor"].get(season, 1.0)
            base = crop_data["base_price"] * season_mult

            # Simulate market price
            random.seed(ref_date.toordinal() + hash(crop))
            daily_var = random.gauss(0, crop_data["volatility"])
            market_price = max(base * (1 + daily_var), 1.0)
            avg_7d = base * (1 + rng.uniform(-0.05, 0.05))

            demand_idx = rng.uniform(0.2, 0.9)

            features = build_features(
                crop_name=crop,
                quantity_kg=quantity,
                harvest_date=harvest_date,
                storage_type=storage_type,
                quality_grade=quality,
                spoilage_risk=spoilage_risk,
                spoilage_probability=spoilage_prob,
                market_price_today=market_price,
                market_price_avg_7d=avg_7d,
                demand_index=demand_idx,
            )
            # Override temporal features with ref_date
            features["month"] = ref_date.month
            features["day_of_week"] = ref_date.weekday()
            features["day_of_month"] = ref_date.day
            features["season_code"] = {"summer": 0, "monsoon": 1, "spring": 2, "winter": 3}[season]
            features["is_weekend"] = 1.0 if ref_date.weekday() >= 5 else 0.0

            vec = features_to_vector(features)
            X_rows.append(vec)

            # Target: ideal selling price
            quality_mult = {"excellent": 1.15, "good": 1.0, "average": 0.85, "poor": 0.65}[quality]
            urgency = 1.0
            if spoilage_risk == "critical":
                urgency = 0.75
            elif spoilage_risk == "high":
                urgency = 0.85
            elif spoilage_risk == "medium":
                urgency = 0.95

            ideal = market_price * quality_mult * urgency * (1 + 0.05 * (demand_idx - 0.5))
            # Apply realistic noise
            ideal *= (1 + rng.uniform(-0.03, 0.03))
            y_rows.append(max(ideal, 1.0))

        return np.array(X_rows, dtype=np.float32), np.array(y_rows, dtype=np.float32)

    def train(self, n_samples: int = 10_000):
        """Train the model on synthetic data."""
        if not HAS_XGB:
            print("[PricePredictionModel] XGBoost not installed — skipping training")
            return

        X, y = self._generate_synthetic_data(n_samples)

        dtrain = xgb.DMatrix(X, label=y, feature_names=FEATURE_NAMES)

        params = {
            "objective": "reg:squarederror",
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 5,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "eval_metric": "rmse",
            "seed": 42,
        }

        self.model = xgb.train(
            params, dtrain, num_boost_round=200, verbose_eval=False
        )
        self.is_trained = True
        self.save()
        print(f"[PricePredictionModel] Trained on {n_samples} samples")

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        crop_name: str,
        quantity_kg: float,
        harvest_date: date,
        storage_type: str = "ambient",
        storage_temp: Optional[float] = None,
        storage_humidity: Optional[float] = None,
        quality_grade: Optional[str] = None,
        spoilage_risk: Optional[str] = None,
        spoilage_probability: Optional[float] = None,
        remaining_shelf_life_days: Optional[int] = None,
        farmer_lat: Optional[float] = None,
        farmer_lng: Optional[float] = None,
        market_price_today: Optional[float] = None,
        market_price_avg_7d: Optional[float] = None,
        demand_index: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Predict the ideal selling price for a produce batch.

        Returns:
            ideal_price, min_acceptable_price, max_price, confidence,
            price_range_lower, price_range_upper, factors, recommendation.
        """
        features = build_features(
            crop_name=crop_name,
            quantity_kg=quantity_kg,
            harvest_date=harvest_date,
            storage_type=storage_type,
            storage_temp=storage_temp,
            storage_humidity=storage_humidity,
            quality_grade=quality_grade,
            spoilage_risk=spoilage_risk,
            spoilage_probability=spoilage_probability,
            remaining_shelf_life_days=remaining_shelf_life_days,
            farmer_lat=farmer_lat,
            farmer_lng=farmer_lng,
            market_price_today=market_price_today,
            market_price_avg_7d=market_price_avg_7d,
            demand_index=demand_index,
        )

        vec = features_to_vector(features)

        if self.is_trained and self.model is not None and HAS_XGB:
            predicted = self._ml_predict(vec, features)
        else:
            predicted = self._rule_predict(features, crop_name)

        return self._build_output(predicted, features, crop_name, market_price_today)

    def _ml_predict(self, vec: List[float], features: Dict[str, float]) -> float:
        """Use the trained XGBoost model."""
        dmat = xgb.DMatrix(
            np.array([vec], dtype=np.float32), feature_names=FEATURE_NAMES
        )
        pred = float(self.model.predict(dmat)[0])
        return max(pred, 0.5)

    def _rule_predict(self, features: Dict[str, float], crop_name: str) -> float:
        """Fallback rule-based prediction when model isn't available."""
        market = features["market_price_today"]
        if market <= 0:
            crop_data = MARKET_PRICE_DATA.get(crop_name.lower(), {"base_price": 30})
            market = crop_data["base_price"]

        quality_mult = {3: 1.15, 2: 1.0, 1: 0.85, 0: 0.65}.get(
            int(features["quality_code"]), 1.0
        )

        spoilage = features["spoilage_risk_code"]
        urgency = 1.0 - (spoilage * 0.25)

        shelf_ratio = features["shelf_life_remaining_ratio"]
        freshness_bonus = 1.0 + 0.1 * max(shelf_ratio - 0.5, 0)

        demand = features["demand_index"]
        demand_adj = 1.0 + 0.1 * (demand - 0.5)

        return max(market * quality_mult * urgency * freshness_bonus * demand_adj, 0.5)

    def _build_output(
        self,
        predicted_ideal: float,
        features: Dict[str, float],
        crop_name: str,
        market_price: Optional[float],
    ) -> Dict[str, Any]:
        """Build the full prediction output with ranges and explanations."""
        crop = crop_name.lower()

        # --- Confidence estimation ---
        confidence = 0.75
        if features["quality_code"] >= 2:
            confidence += 0.05
        if features["market_price_today"] > 0:
            confidence += 0.10
        if features["shelf_life_remaining_ratio"] > 0.5:
            confidence += 0.05
        confidence = min(confidence, 0.98)

        # --- Price range (confidence interval) ---
        spread = 0.12 * (1 - confidence + 0.2)
        price_range_lower = round(predicted_ideal * (1 - spread), 2)
        price_range_upper = round(predicted_ideal * (1 + spread), 2)

        # --- Seller-protected floor ---
        msp = MSP_DATA.get(crop, 0.0)
        cost_floor = predicted_ideal * 0.70  # never below 70% of ideal
        market_floor = (market_price or predicted_ideal) * 0.65
        min_acceptable = round(max(msp, cost_floor, market_floor, 1.0), 2)

        ideal_price = round(predicted_ideal, 2)

        # --- Feature importance (explainability) ---
        factors = self._explain(features, crop_name, market_price, ideal_price, min_acceptable)

        return {
            "ideal_price": ideal_price,
            "min_acceptable_price": min_acceptable,
            "price_range_lower": price_range_lower,
            "price_range_upper": price_range_upper,
            "confidence": round(confidence, 2),
            "factors": factors,
        }

    def _explain(
        self,
        features: Dict[str, float],
        crop_name: str,
        market_price: Optional[float],
        ideal_price: float,
        min_acceptable: float,
    ) -> List[Dict[str, Any]]:
        """Build human-readable explanation factors."""
        factors: List[Dict[str, Any]] = []

        # Market baseline
        mp = market_price or features["market_price_today"]
        if mp > 0:
            factors.append({
                "name": "Today's Market Price",
                "value": f"₹{mp:.1f}/kg",
                "impact": "baseline",
                "weight": 0.30,
            })

        avg7 = features["market_price_avg_7d"]
        if avg7 > 0:
            factors.append({
                "name": "7-Day Average",
                "value": f"₹{avg7:.1f}/kg",
                "impact": "reference",
                "weight": 0.15,
            })

        # Momentum
        mom = features["price_momentum"]
        if abs(mom) > 0.02:
            direction = "rising" if mom > 0 else "falling"
            factors.append({
                "name": "Price Trend",
                "value": f"{direction} ({mom * 100:+.1f}%)",
                "impact": "positive" if mom > 0 else "negative",
                "weight": 0.10,
            })

        # Quality
        qcode = int(features["quality_code"])
        grade_map = {3: "excellent", 2: "good", 1: "average", 0: "poor"}
        grade = grade_map.get(qcode, "average")
        factors.append({
            "name": "Quality Grade",
            "value": grade,
            "impact": "positive" if qcode >= 2 else "negative",
            "weight": 0.15,
        })

        # Shelf life
        ratio = features["shelf_life_remaining_ratio"]
        remaining_d = features["remaining_shelf_life_days"]
        factors.append({
            "name": "Remaining Shelf Life",
            "value": f"{remaining_d:.0f} days ({ratio * 100:.0f}%)",
            "impact": "positive" if ratio > 0.5 else "negative" if ratio < 0.2 else "neutral",
            "weight": 0.10,
        })

        # Spoilage
        spoilage = features["spoilage_risk_code"]
        risk_label = (
            "low" if spoilage < 0.2 else
            "medium" if spoilage < 0.5 else
            "high" if spoilage < 0.8 else "critical"
        )
        factors.append({
            "name": "Spoilage Risk",
            "value": risk_label,
            "impact": "negative" if spoilage > 0.5 else "neutral",
            "weight": 0.10,
        })

        # Demand
        demand = features["demand_index"]
        factors.append({
            "name": "Demand Index",
            "value": f"{demand:.0%}",
            "impact": "positive" if demand > 0.6 else "negative" if demand < 0.3 else "neutral",
            "weight": 0.10,
        })

        # MSP floor if applicable
        crop = crop_name.lower()
        if crop in MSP_DATA:
            factors.append({
                "name": "MSP Floor (Govt)",
                "value": f"₹{MSP_DATA[crop]:.1f}/kg",
                "impact": "protection",
                "weight": 0.0,
            })

        return factors

    def get_feature_importance(self) -> Dict[str, float]:
        """Return XGBoost feature importances if model is trained."""
        if not self.is_trained or self.model is None:
            return {}
        scores = self.model.get_score(importance_type="gain")
        total = sum(scores.values()) or 1.0
        return {k: round(v / total, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])}

    def what_if(
        self,
        base_prediction: Dict[str, Any],
        feature_overrides: Dict[str, Any],
        crop_name: str,
        original_features: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Causal what-if analysis: re-predict with one or more features changed.

        Example: what_if(base, {"storage_temp": 30}, "tomato", features)
        → Shows how price changes if storage temp increases to 30°C
        """
        modified = dict(original_features)
        modified.update(feature_overrides)
        vec = features_to_vector(modified)

        if self.is_trained and HAS_XGB:
            new_ideal = self._ml_predict(vec, modified)
        else:
            new_ideal = self._rule_predict(modified, crop_name)

        orig_ideal = base_prediction["ideal_price"]
        change = new_ideal - orig_ideal
        pct = (change / orig_ideal * 100) if orig_ideal else 0

        return {
            "original_ideal_price": orig_ideal,
            "new_ideal_price": round(new_ideal, 2),
            "price_change": round(change, 2),
            "price_change_pct": round(pct, 1),
            "overrides_applied": feature_overrides,
        }


# Singleton instance
price_model = PricePredictionModel()
