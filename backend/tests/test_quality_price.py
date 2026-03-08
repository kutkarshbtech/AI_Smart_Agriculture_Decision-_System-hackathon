"""
Tests for Quality → Price integration endpoints.
Covers: simulate-and-price, assess-and-price (standalone + batch), helper functions.
"""
import io
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Fixtures / Helpers ───────────────────────────────────


FAKE_QUALITY_RESULT = {
    "overall_grade": "good",
    "quality_score": 78,
    "freshness_status": "fresh",
    "freshness_score": 0.82,
    "damage_score": 0.05,
    "ripeness_level": "ripe",
    "model_type": "simulation",
    "confidence": 0.9,
    "defects_detected": [],
    "recommendations": {
        "english": "Produce is in good condition.",
        "hindi": "उत्पाद अच्छी स्थिति में है।",
    },
}

FAKE_PRICE_REC = {
    "crop_name": "tomato",
    "ideal_price": 18.5,
    "recommended_min_price": 15.0,
    "price_range_upper": 23.0,
    "model_type": "xgboost",
    "price_source": "data.gov.in",
    "action": "sell_now",
    "action_text": "Market conditions are favourable.",
    "what_if_scenarios": [],
    "msp_note": None,
}

FAKE_MANDI_RESULT = {
    "records": [
        {
            "state": "Maharashtra",
            "district": "Pune",
            "market": "Gultekdi",
            "commodity": "Tomato",
            "variety": "Local",
            "arrival_date": "2026-03-06",
            "min_price_per_quintal": 2000,
            "max_price_per_quintal": 3000,
            "modal_price_per_quintal": 2500,
            "min_price_per_kg": 20.0,
            "max_price_per_kg": 30.0,
            "modal_price_per_kg": 25.0,
            "source": "data.gov.in",
        }
    ],
    "total": 1,
    "source": "data.gov.in",
    "commodity": "Tomato",
    "api_error": None,
    "cached": False,
}

FAKE_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Minimal fake PNG header


# ═══════════════════════════════════════════════════════════
#  1. Helper function tests
# ═══════════════════════════════════════════════════════════


class TestQualityPriceNoteHelper:
    """Test the _quality_price_note helper."""

    def _note(self, grade, price_rec):
        from app.api.routes.quality import _quality_price_note
        return _quality_price_note(grade, price_rec)

    def test_excellent_note(self):
        note = self._note("excellent", FAKE_PRICE_REC)
        assert "premium" in note.lower() or "Excellent" in note
        assert "18.5" in note
        assert "live mandi data" in note  # source is data.gov.in

    def test_good_note(self):
        note = self._note("good", FAKE_PRICE_REC)
        assert "Good" in note or "fair" in note.lower()
        assert "18.5" in note

    def test_average_note(self):
        note = self._note("average", FAKE_PRICE_REC)
        assert "Average" in note or "quickly" in note.lower()

    def test_poor_note(self):
        note = self._note("poor", FAKE_PRICE_REC)
        assert "poor" in note.lower() or "immediately" in note.lower()

    def test_unknown_grade_fallback(self):
        note = self._note("unknown_grade", FAKE_PRICE_REC)
        assert "18.5" in note  # Still shows price

    def test_simulated_source_label(self):
        rec = {**FAKE_PRICE_REC, "price_source": "simulated"}
        note = self._note("good", rec)
        assert "estimated market data" in note


class TestQualityGradeToSpoilage:
    """Test the grade→spoilage mapping constant."""

    def test_mapping_values(self):
        from app.api.routes.quality import QUALITY_GRADE_TO_SPOILAGE
        assert QUALITY_GRADE_TO_SPOILAGE["excellent"] == "low"
        assert QUALITY_GRADE_TO_SPOILAGE["good"] == "low"
        assert QUALITY_GRADE_TO_SPOILAGE["average"] == "medium"
        assert QUALITY_GRADE_TO_SPOILAGE["poor"] == "high"


# ═══════════════════════════════════════════════════════════
#  2. simulate-and-price endpoint
# ═══════════════════════════════════════════════════════════


class TestSimulateAndPriceEndpoint:
    """Test GET /api/v1/quality/simulate-and-price/{crop_name}"""

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_simulate_and_price_basic(self, mock_qs, mock_ps, mock_mc):
        mock_qs._simulate_assessment.return_value = FAKE_QUALITY_RESULT.copy()
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.get("/api/v1/quality/simulate-and-price/tomato")
        assert resp.status_code == 200

        data = resp.json()
        assert data["crop_name"] == "tomato"
        assert data["quantity_kg"] == 100  # default

        # Quality
        qa = data["quality_assessment"]
        assert qa["overall_grade"] == "good"
        assert "note" in qa  # Simulated note

        # Price
        pr = data["price_recommendation"]
        assert pr["ideal_price"] == 18.5
        assert "quality_based_note" in pr

        # Mandi
        assert "mandi_prices" in data
        assert data["mandi_prices"]["total_mandis"] == 1

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_simulate_and_price_custom_params(self, mock_qs, mock_ps, mock_mc):
        mock_qs._simulate_assessment.return_value = FAKE_QUALITY_RESULT.copy()
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.get(
            "/api/v1/quality/simulate-and-price/mango"
            "?quantity_kg=200&storage_type=cold&state=Karnataka"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_name"] == "mango"
        assert data["quantity_kg"] == 200

        # Verify pricing called with correct params
        mock_ps.generate_price_recommendation.assert_called_once()
        call_kwargs = mock_ps.generate_price_recommendation.call_args.kwargs
        assert call_kwargs["crop_name"] == "mango"
        assert call_kwargs["quantity_kg"] == 200
        assert call_kwargs["storage_type"] == "cold"

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_simulate_and_price_has_created_at(self, mock_qs, mock_ps, mock_mc):
        mock_qs._simulate_assessment.return_value = FAKE_QUALITY_RESULT.copy()
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.get("/api/v1/quality/simulate-and-price/potato")
        data = resp.json()
        assert "created_at" in data

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_spoilage_risk_derived_from_grade(self, mock_qs, mock_ps, mock_mc):
        """Ensure quality grade gets mapped to correct spoilage risk."""
        poor_quality = {**FAKE_QUALITY_RESULT, "overall_grade": "poor"}
        mock_qs._simulate_assessment.return_value = poor_quality
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.get("/api/v1/quality/simulate-and-price/banana")
        assert resp.status_code == 200

        call_kwargs = mock_ps.generate_price_recommendation.call_args.kwargs
        assert call_kwargs["spoilage_risk"] == "high"  # poor → high


# ═══════════════════════════════════════════════════════════
#  3. assess-and-price standalone endpoint
# ═══════════════════════════════════════════════════════════


class TestAssessAndPriceStandalone:
    """Test POST /api/v1/quality/assess-and-price (standalone)"""

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_standalone(self, mock_qs, mock_ps, mock_mc):
        mock_qs.assess_quality_from_image = AsyncMock(return_value=FAKE_QUALITY_RESULT.copy())
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.post(
            "/api/v1/quality/assess-and-price?crop_name=tomato&quantity_kg=50",
            files={"file": ("tomato.png", io.BytesIO(FAKE_IMAGE), "image/png")},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["crop_name"] == "tomato"
        assert data["quantity_kg"] == 50
        assert data["quality_assessment"]["overall_grade"] == "good"
        assert data["price_recommendation"]["ideal_price"] == 18.5
        assert "quality_based_note" in data["price_recommendation"]
        assert "mandi_prices" in data

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_empty_file(self, mock_qs, mock_ps, mock_mc):
        resp = client.post(
            "/api/v1/quality/assess-and-price?crop_name=tomato",
            files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert resp.status_code == 400
        assert "Empty" in resp.json()["detail"]

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_with_state_filter(self, mock_qs, mock_ps, mock_mc):
        mock_qs.assess_quality_from_image = AsyncMock(return_value=FAKE_QUALITY_RESULT.copy())
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()
        mock_mc.fetch_prices = AsyncMock(return_value=FAKE_MANDI_RESULT.copy())

        resp = client.post(
            "/api/v1/quality/assess-and-price"
            "?crop_name=apple&storage_type=cold&state=Himachal%20Pradesh",
            files={"file": ("apple.png", io.BytesIO(FAKE_IMAGE), "image/png")},
        )
        assert resp.status_code == 200

        # Verify state was passed for mandi lookup
        mock_mc.fetch_prices.assert_called_once()
        call_args = mock_mc.fetch_prices.call_args
        assert call_args.kwargs.get("state") == "Himachal Pradesh" or \
               (len(call_args.args) >= 2 and call_args.args[1] == "Himachal Pradesh") or \
               call_args[1].get("state") == "Himachal Pradesh"


# ═══════════════════════════════════════════════════════════
#  4. assess-and-price batch endpoint
# ═══════════════════════════════════════════════════════════


class TestAssessAndPriceBatch:
    """Test POST /api/v1/quality/assess-and-price/{batch_id}"""

    def _create_batch(self):
        """Create a batch via API to get a batch_id."""
        resp = client.post("/api/v1/produce/batches", json={
            "crop_type_id": 1,  # Tomato
            "quantity_kg": 200,
            "harvest_date": "2026-03-01",
            "storage_type": "ambient",
            "location_lat": 18.52,
            "location_lng": 73.85,
        })
        assert resp.status_code in (200, 201), f"Batch creation failed: {resp.text}"
        return resp.json()["id"]

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_with_batch(self, mock_qs, mock_ps, mock_mc):
        batch_id = self._create_batch()

        mock_qs.assess_quality_from_image = AsyncMock(return_value=FAKE_QUALITY_RESULT.copy())
        mock_ps.generate_price_recommendation.return_value = FAKE_PRICE_REC.copy()

        resp = client.post(
            f"/api/v1/quality/assess-and-price/{batch_id}",
            files={"file": ("tomato.png", io.BytesIO(FAKE_IMAGE), "image/png")},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["batch_id"] == batch_id
        assert data["crop_name"] == "Tomato"
        assert "quality_assessment" in data
        assert "price_recommendation" in data
        assert "quality_based_note" in data["price_recommendation"]
        assert "created_at" in data

    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_batch_not_found(self, mock_qs):
        resp = client.post(
            "/api/v1/quality/assess-and-price/99999",
            files={"file": ("tomato.png", io.BytesIO(FAKE_IMAGE), "image/png")},
        )
        assert resp.status_code == 404
        assert "Batch not found" in resp.json()["detail"]

    @patch("app.api.routes.quality.mandi_client")
    @patch("app.api.routes.quality.pricing_service")
    @patch("app.api.routes.quality.quality_service")
    def test_assess_and_price_batch_empty_image(self, mock_qs, mock_ps, mock_mc):
        batch_id = self._create_batch()

        resp = client.post(
            f"/api/v1/quality/assess-and-price/{batch_id}",
            files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════
#  5. Existing quality endpoints still work
# ═══════════════════════════════════════════════════════════


class TestExistingQualityEndpoints:
    """Sanity-check original quality endpoints still function."""

    def test_model_status_endpoint(self):
        resp = client.get("/api/v1/quality/model-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "model_type" in data

    def test_simulate_endpoint(self):
        resp = client.get("/api/v1/quality/simulate/tomato")
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_name"] == "tomato"
        assert "overall_grade" in data
        assert "quality_score" in data

    @patch("app.api.routes.quality.quality_service")
    def test_assess_standalone_rejects_empty(self, mock_qs):
        resp = client.post(
            "/api/v1/quality/assess-standalone?crop_name=tomato",
            files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert resp.status_code == 400
