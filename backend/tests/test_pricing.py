"""
Tests for the Ideal Price Prediction feature.
Tests the ML model, pricing service, and API endpoints.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch


# ---------------------------------------------------------------------------
# ML Model tests
# ---------------------------------------------------------------------------
class TestPriceFeatures:
    """Test feature engineering."""

    def test_build_features_returns_all_keys(self):
        from ml.pricing.features import build_features, FEATURE_NAMES

        features = build_features(
            crop_name="tomato",
            quantity_kg=100,
            harvest_date=date.today() - timedelta(days=2),
        )
        for name in FEATURE_NAMES:
            assert name in features, f"Missing feature: {name}"

    def test_features_to_vector_length(self):
        from ml.pricing.features import build_features, features_to_vector, FEATURE_NAMES

        features = build_features(
            crop_name="potato",
            quantity_kg=50,
            harvest_date=date.today(),
        )
        vec = features_to_vector(features)
        assert len(vec) == len(FEATURE_NAMES)

    def test_shelf_life_remaining_ratio(self):
        from ml.pricing.features import remaining_shelf_life_ratio

        # Just harvested → ratio ≈ 1.0
        ratio = remaining_shelf_life_ratio("tomato", date.today())
        assert 0.8 <= ratio <= 1.0

        # Long past shelf life → ratio = 0.0
        ratio = remaining_shelf_life_ratio("tomato", date.today() - timedelta(days=30))
        assert ratio == 0.0

    def test_msp_data_present(self):
        from ml.pricing.features import MSP_DATA

        assert "rice" in MSP_DATA
        assert "wheat" in MSP_DATA
        assert MSP_DATA["rice"] > 0

    def test_quality_grade_encoding(self):
        from ml.pricing.features import build_features

        f_good = build_features("tomato", 100, date.today(), quality_grade="good")
        f_poor = build_features("tomato", 100, date.today(), quality_grade="poor")
        assert f_good["quality_code"] > f_poor["quality_code"]

    def test_perishability_values(self):
        from ml.pricing.features import PERISHABILITY_INDEX

        assert PERISHABILITY_INDEX["spinach"] > PERISHABILITY_INDEX["potato"]
        assert PERISHABILITY_INDEX["rice"] < 0.1


class TestPriceModel:
    """Test the price prediction model."""

    def test_rule_based_prediction(self):
        from ml.pricing.model import PricePredictionModel

        model = PricePredictionModel()
        model.is_trained = False  # Force rule-based

        result = model.predict(
            crop_name="tomato",
            quantity_kg=100,
            harvest_date=date.today() - timedelta(days=1),
            quality_grade="good",
            market_price_today=25.0,
            market_price_avg_7d=24.0,
        )

        assert "ideal_price" in result
        assert "min_acceptable_price" in result
        assert "price_range_lower" in result
        assert "price_range_upper" in result
        assert "confidence" in result
        assert "factors" in result

        assert result["ideal_price"] > 0
        assert result["min_acceptable_price"] > 0
        assert result["min_acceptable_price"] <= result["ideal_price"]
        assert result["price_range_lower"] <= result["ideal_price"]
        assert result["ideal_price"] <= result["price_range_upper"]
        assert 0 < result["confidence"] <= 1

    def test_quality_affects_price(self):
        from ml.pricing.model import PricePredictionModel

        model = PricePredictionModel()
        model.is_trained = False

        base_kwargs = dict(
            crop_name="tomato",
            quantity_kg=100,
            harvest_date=date.today(),
            market_price_today=25.0,
            market_price_avg_7d=24.0,
        )

        r_excellent = model.predict(quality_grade="excellent", **base_kwargs)
        r_poor = model.predict(quality_grade="poor", **base_kwargs)

        assert r_excellent["ideal_price"] > r_poor["ideal_price"]

    def test_msp_floor_protection(self):
        from ml.pricing.model import PricePredictionModel

        model = PricePredictionModel()
        model.is_trained = False

        result = model.predict(
            crop_name="rice",
            quantity_kg=500,
            harvest_date=date.today(),
            quality_grade="poor",
            spoilage_risk="high",
            market_price_today=20.0,
            market_price_avg_7d=19.0,
        )

        from ml.pricing.features import MSP_DATA
        assert result["min_acceptable_price"] >= MSP_DATA["rice"]

    def test_what_if_analysis(self):
        from ml.pricing.model import PricePredictionModel
        from ml.pricing.features import build_features

        model = PricePredictionModel()
        model.is_trained = False

        base = model.predict(
            crop_name="tomato",
            quantity_kg=100,
            harvest_date=date.today(),
            quality_grade="average",
            market_price_today=25.0,
        )
        features = build_features(
            crop_name="tomato",
            quantity_kg=100,
            harvest_date=date.today(),
            quality_grade="average",
            market_price_today=25.0,
        )

        result = model.what_if(
            base, {"quality_code": 3.0}, "tomato", features
        )

        assert "original_ideal_price" in result
        assert "new_ideal_price" in result
        assert "price_change" in result
        assert "price_change_pct" in result
        assert result["new_ideal_price"] > result["original_ideal_price"]

    def test_factors_have_weights(self):
        from ml.pricing.model import PricePredictionModel

        model = PricePredictionModel()
        model.is_trained = False

        result = model.predict(
            crop_name="onion",
            quantity_kg=200,
            harvest_date=date.today(),
            quality_grade="good",
            spoilage_risk="low",
            market_price_today=22.0,
            market_price_avg_7d=21.0,
            demand_index=0.6,
        )

        assert len(result["factors"]) >= 4
        for factor in result["factors"]:
            assert "name" in factor
            assert "value" in factor
            assert "impact" in factor


# ---------------------------------------------------------------------------
# Pricing Service tests
# ---------------------------------------------------------------------------
class TestPricingService:
    """Test the enhanced pricing service."""

    def test_generate_recommendation_has_new_fields(self):
        from app.services.pricing_service import PricingService

        svc = PricingService()
        rec = svc.generate_price_recommendation(
            crop_name="tomato",
            quantity_kg=100,
            quality_grade="good",
        )

        # Core fields
        assert "ideal_price" in rec
        assert "recommended_min_price" in rec
        assert "recommended_max_price" in rec
        assert "price_range_lower" in rec
        assert "price_range_upper" in rec
        assert "confidence_score" in rec

        # New fields
        assert "action_text" in rec
        assert "demand_index" in rec
        assert "price_forecast_3d" in rec
        assert "what_if_scenarios" in rec
        assert "model_type" in rec

        # Forecast must have entries
        assert len(rec["price_forecast_3d"]) == 3

        # What-if scenarios must exist
        assert len(rec["what_if_scenarios"]) >= 1

    def test_forecast_prices(self):
        from app.services.pricing_service import PricingService

        svc = PricingService()
        forecast = svc.forecast_prices("onion", days_ahead=5)

        assert len(forecast) == 5
        for day in forecast:
            assert "date" in day
            assert "predicted_price" in day
            assert "confidence" in day
            assert day["predicted_price"] > 0
            assert 0 < day["confidence"] <= 1

    def test_sell_now_for_critical_spoilage(self):
        from app.services.pricing_service import PricingService

        svc = PricingService()
        rec = svc.generate_price_recommendation(
            crop_name="banana",
            quantity_kg=50,
            quality_grade="poor",
            spoilage_risk="critical",
            remaining_shelf_life_days=1,
        )
        assert rec["action"] == "sell_now"

    def test_demand_index_range(self):
        from app.services.pricing_service import PricingService

        svc = PricingService()
        demand = svc._get_demand_index("tomato")
        assert 0.0 <= demand <= 1.0

    def test_msp_note_for_grain(self):
        from app.services.pricing_service import PricingService

        svc = PricingService()
        rec = svc.generate_price_recommendation(
            crop_name="rice",
            quantity_kg=1000,
            quality_grade="good",
        )
        assert rec["msp_note"] is not None
        assert "MSP" in rec["msp_note"]


# ---------------------------------------------------------------------------
# API route tests (FastAPI TestClient)
# ---------------------------------------------------------------------------
class TestPricingAPI:
    """Test pricing API endpoints using FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def batch_id(self, client):
        """Create a test batch and return its ID."""
        response = client.post("/api/v1/produce/batches", json={
            "crop_type_id": 1,  # Tomato
            "quantity_kg": 200,
            "harvest_date": (date.today() - timedelta(days=1)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 25,
        })
        assert response.status_code == 200
        return response.json()["id"]

    def test_get_market_prices(self, client):
        resp = client.get("/api/v1/pricing/market/tomato?days=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_name"] == "tomato"
        assert len(data["prices"]) >= 5

    def test_get_recommendation_by_batch(self, client, batch_id):
        resp = client.get(f"/api/v1/pricing/recommend/{batch_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["batch_id"] == batch_id
        assert "ideal_price" in data
        assert "recommended_min_price" in data
        assert "what_if_scenarios" in data
        assert "price_forecast_3d" in data

    def test_direct_recommendation(self, client):
        resp = client.post("/api/v1/pricing/recommend", json={
            "crop_name": "onion",
            "quantity_kg": 150,
            "quality_grade": "good",
            "harvest_date": date.today().isoformat(),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_name"] == "onion"
        assert "ideal_price" in data
        assert data["ideal_price"] > 0

    def test_price_forecast(self, client):
        resp = client.get("/api/v1/pricing/forecast/tomato?days_ahead=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["forecast"]) == 3

    def test_price_trends(self, client):
        resp = client.get("/api/v1/pricing/trends/potato")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trend"] in ("rising", "falling", "stable")

    def test_feature_importance(self, client):
        resp = client.get("/api/v1/pricing/feature-importance")
        assert resp.status_code == 200

    def test_recommendation_not_found(self, client):
        resp = client.get("/api/v1/pricing/recommend/99999")
        assert resp.status_code == 404
