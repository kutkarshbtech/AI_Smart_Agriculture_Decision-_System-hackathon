"""
Tests for the Mandi price service (data.gov.in integration).
Covers: record parsing, caching, sync fetcher, API routes (mocked).
"""
import time
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

# ── Unit tests for the mandi service ──────────────────────

class TestMandiRecordParser:
    """Test MandiPriceClient._parse_record transforms raw API records correctly."""

    def _parser(self):
        from app.services.mandi_service import MandiPriceClient
        return MandiPriceClient._parse_record

    def test_basic_record(self):
        raw = {
            "state": "Maharashtra",
            "district": "Pune",
            "market": "Gultekdi",
            "commodity": "Tomato",
            "variety": "Local",
            "arrival_date": "06/03/2026",
            "min_price": "2000",
            "max_price": "3000",
            "modal_price": "2500",
        }
        rec = self._parser()(raw)
        assert rec["state"] == "Maharashtra"
        assert rec["market"] == "Gultekdi"
        assert rec["commodity"] == "Tomato"
        assert rec["modal_price_per_quintal"] == 2500
        assert rec["modal_price_per_kg"] == 25.0  # 2500/100
        assert rec["min_price_per_kg"] == 20.0
        assert rec["max_price_per_kg"] == 30.0
        assert rec["arrival_date"] == "2026-03-06"
        assert rec["source"] == "data.gov.in"

    def test_missing_fields_default_to_zero(self):
        raw = {"state": "Delhi"}
        rec = self._parser()(raw)
        assert rec["modal_price_per_kg"] == 0
        assert rec["min_price_per_kg"] == 0

    def test_alternate_date_format(self):
        raw = {"arrival_date": "2026-03-06", "min_price": "100", "max_price": "200", "modal_price": "150"}
        rec = self._parser()(raw)
        assert rec["arrival_date"] == "2026-03-06"

    def test_none_price_treated_as_zero(self):
        raw = {"min_price": None, "max_price": None, "modal_price": None}
        rec = self._parser()(raw)
        assert rec["modal_price_per_kg"] == 0


class TestMandiCaching:
    """Test the in-memory caching layer."""

    def test_cache_set_and_get(self):
        from app.services.mandi_service import _set_cache, _get_cached
        _set_cache("test_key_1", {"data": "hello"})
        result = _get_cached("test_key_1")
        assert result == {"data": "hello"}

    def test_cache_expires(self):
        from app.services.mandi_service import _cache, _get_cached, _set_cache, CACHE_TTL_SECONDS
        _set_cache("test_key_2", {"data": "old"})
        # Manually expire
        _cache["test_key_2"]["ts"] = time.time() - CACHE_TTL_SECONDS - 1
        result = _get_cached("test_key_2")
        assert result is None

    def test_cache_key_generation(self):
        from app.services.mandi_service import _cache_key
        k1 = _cache_key("Tomato", "Maharashtra", None)
        k2 = _cache_key("Tomato", "Delhi", None)
        assert k1 != k2
        k3 = _cache_key("Tomato", "Maharashtra", None)
        assert k1 == k3


class TestCommodityNameMap:
    """Test that commodity name mapping covers common crops."""

    def test_known_crops_map(self):
        from app.services.mandi_service import COMMODITY_NAME_MAP
        assert COMMODITY_NAME_MAP["tomato"] == "Tomato"
        assert COMMODITY_NAME_MAP["okra"] == "Ladies Finger"
        assert COMMODITY_NAME_MAP["soybean"] == "Soyabean"
        assert COMMODITY_NAME_MAP["chana"] == "Bengal Gram(Gram)(Whole)"

    def test_unknown_crop_gets_title_cased(self):
        from app.services.mandi_service import COMMODITY_NAME_MAP
        crop = "dragonfruit"
        result = COMMODITY_NAME_MAP.get(crop, crop.title())
        assert result == "Dragonfruit"


class TestMandiFetchSync:
    """Test synchronous fetch with mocked HTTP."""

    def _make_api_response(self, records):
        return {"total": len(records), "records": records}

    @patch("app.services.mandi_service.httpx.Client")
    def test_fetch_prices_sync_success(self, mock_client_cls):
        from app.services.mandi_service import MandiPriceClient, _cache

        # Clear cache
        _cache.clear()

        raw_records = [
            {
                "state": "Karnataka",
                "district": "Bengaluru",
                "market": "Yeshwanthpur",
                "commodity": "Tomato",
                "variety": "Local",
                "arrival_date": "06/03/2026",
                "min_price": "1500",
                "max_price": "2500",
                "modal_price": "2000",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._make_api_response(raw_records)
        mock_resp.raise_for_status = MagicMock()

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_ctx

        client = MandiPriceClient(api_key="test-key")
        result = client.fetch_prices_sync("tomato")

        assert result["total"] == 1
        assert result["source"] == "data.gov.in"
        assert len(result["records"]) == 1
        assert result["records"][0]["modal_price_per_kg"] == 20.0
        assert result["cached"] is False

    @patch("app.services.mandi_service.httpx.Client")
    def test_fetch_prices_sync_api_error(self, mock_client_cls):
        from app.services.mandi_service import MandiPriceClient, _cache
        import httpx as httpx_mod

        _cache.clear()

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(
            return_value=MagicMock(
                get=MagicMock(side_effect=httpx_mod.RequestError("timeout"))
            )
        )
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_ctx

        client = MandiPriceClient(api_key="test-key")
        result = client.fetch_prices_sync("tomato")

        assert result["records"] == []
        assert result["api_error"] is not None


class TestMandiFetchAsync:
    """Test async fetch with mocked HTTP."""

    @pytest.mark.asyncio
    @patch("app.services.mandi_service.httpx.AsyncClient")
    async def test_fetch_prices_async_success(self, mock_client_cls):
        from app.services.mandi_service import MandiPriceClient, _cache

        _cache.clear()

        raw_records = [
            {
                "state": "Delhi",
                "district": "New Delhi",
                "market": "Azadpur",
                "commodity": "Onion",
                "variety": "Red",
                "arrival_date": "06/03/2026",
                "min_price": "1800",
                "max_price": "2800",
                "modal_price": "2200",
            }
        ]

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total": 1, "records": raw_records}
        mock_resp.raise_for_status = MagicMock()

        mock_inner = AsyncMock()
        mock_inner.get.return_value = mock_resp

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_inner)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_ctx

        client = MandiPriceClient(api_key="test-key")
        result = await client.fetch_prices("onion")

        assert result["total"] == 1
        assert result["records"][0]["modal_price_per_kg"] == 22.0

    @pytest.mark.asyncio
    async def test_get_commodity_summary_empty(self):
        from app.services.mandi_service import MandiPriceClient

        client = MandiPriceClient(api_key="")

        with patch.object(client, "fetch_prices", return_value={
            "records": [], "total": 0, "source": "data.gov.in", "api_error": "no key",
        }):
            summary = await client.get_commodity_summary("tomato")
            assert summary["num_mandis"] == 0
            assert summary["avg_price_per_kg"] is None

    @pytest.mark.asyncio
    async def test_get_commodity_summary_with_data(self):
        from app.services.mandi_service import MandiPriceClient

        client = MandiPriceClient(api_key="test")

        fake_records = [
            {"modal_price_per_kg": 25.0, "min_price_per_kg": 20.0, "max_price_per_kg": 30.0, "state": "Maharashtra"},
            {"modal_price_per_kg": 30.0, "min_price_per_kg": 22.0, "max_price_per_kg": 35.0, "state": "Karnataka"},
        ]

        with patch.object(client, "fetch_prices", return_value={
            "records": fake_records, "total": 2, "source": "data.gov.in",
        }):
            summary = await client.get_commodity_summary("tomato")
            assert summary["num_mandis"] == 2
            assert summary["avg_price_per_kg"] == 27.5
            assert summary["min_price_per_kg"] == 20.0
            assert summary["max_price_per_kg"] == 35.0
            assert set(summary["states"]) == {"Maharashtra", "Karnataka"}


# ── Integration with PricingService ──────────────────────

class TestPricingServiceMandiIntegration:
    """Test PricingService live price methods."""

    def test_get_market_price_today_simulated_fallback(self):
        """Without mandi key, falls back to simulation."""
        from app.services.pricing_service import PricingService

        svc = PricingService()
        svc._has_mandi_key = False  # Force fallback

        result = svc._get_market_price_today("tomato")
        assert "simulated" in result["source"]
        assert result["modal_price"] > 0

    def test_get_market_price_today_live(self):
        """With mandi key + mock, returns live data."""
        from app.services.pricing_service import PricingService

        svc = PricingService()
        svc._has_mandi_key = True

        with patch.object(svc, "get_live_mandi_price", return_value={
            "modal_price": 28.5,
            "min_price": 22.0,
            "max_price": 35.0,
            "mandi_name": "Azadpur",
            "source": "data.gov.in",
            "num_mandis": 5,
        }):
            result = svc._get_market_price_today("tomato")
            assert result["source"] == "data.gov.in"
            assert result["modal_price"] == 28.5
            assert result["mandi_name"] == "Azadpur"

    def test_recommendation_includes_price_source(self):
        """Price recommendation should include price_source field."""
        from app.services.pricing_service import PricingService

        svc = PricingService()
        rec = svc.generate_price_recommendation(
            crop_name="tomato",
            quantity_kg=100,
            quality_grade="good",
        )
        assert "price_source" in rec
        assert rec["price_source"] in ("data.gov.in", "simulated")


# ── API route tests ──────────────────────────────────────

class TestMandiAPI:
    """Test the mandi API endpoints via FastAPI TestClient."""

    @pytest.fixture(autouse=True)
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    @patch("app.api.routes.pricing.mandi_client")
    def test_get_mandi_prices_success(self, mock_mandi):
        from app.services.mandi_service import MandiPriceClient

        fake_result = {
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
        mock_mandi.fetch_prices = AsyncMock(return_value=fake_result)

        resp = self.client.get("/api/v1/pricing/mandi/prices/tomato")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "data.gov.in"

    def test_get_mandi_summary_endpoint_exists(self):
        resp = self.client.get("/api/v1/pricing/mandi/summary/tomato")
        # Should not 404 (may 502 if no key)
        assert resp.status_code in (200, 502)

    def test_compare_endpoint_exists(self):
        resp = self.client.get("/api/v1/pricing/mandi/compare/tomato?states=Maharashtra,Delhi")
        assert resp.status_code in (200, 502)
