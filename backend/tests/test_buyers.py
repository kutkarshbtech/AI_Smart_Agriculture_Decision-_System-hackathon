"""
Tests for the Local Buyer & Shop Matching feature.
Tests the enhanced matching service, active demands, offers, and API endpoints.
"""
import pytest
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Buyer Service tests
# ---------------------------------------------------------------------------
class TestBuyerMatchingService:
    """Test the enhanced buyer matching service."""

    def test_find_matching_buyers_returns_scores(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=500,
        )

        assert len(matches) > 0
        for m in matches:
            assert "match_score" in m
            assert "sub_scores" in m
            assert "buyer_type" in m
            assert "rating" in m
            assert "has_active_demand" in m
            assert 0 <= m["match_score"] <= 100
            assert m["distance_km"] <= 500

    def test_sorted_by_score_by_default(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=2000,
        )

        if len(matches) > 1:
            scores = [m["match_score"] for m in matches]
            assert scores == sorted(scores, reverse=True)

    def test_sort_by_distance(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=2000,
            sort_by="distance",
        )

        if len(matches) > 1:
            distances = [m["distance_km"] for m in matches]
            assert distances == sorted(distances)

    def test_filter_by_buyer_type(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=2000,
            buyer_type="retailer",
        )

        for m in matches:
            assert m["buyer_type"] == "retailer"

    def test_filter_by_min_rating(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=2000,
            min_rating=4.5,
        )

        for m in matches:
            assert m["rating"] >= 4.5

    def test_haversine_distance(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        # Delhi to Mumbai ≈ 1150 km
        dist = svc._haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1100 < dist < 1200

    def test_active_demand_detection(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        matches = svc.find_matching_buyers(
            crop_name="tomato",
            farmer_lat=26.8,
            farmer_lng=80.9,
            quantity_kg=100,
            max_distance_km=2000,
        )

        # At least one buyer should have active demand for tomato
        has_demand = any(m["has_active_demand"] for m in matches)
        assert has_demand, "Expected at least one buyer with active demand for tomato"


class TestActiveDemands:
    """Test active demand queries."""

    def test_get_all_demands(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        demands = svc.get_active_demands()
        assert len(demands) > 0

        for d in demands:
            assert "demand_id" in d
            assert "crop_name" in d
            assert "quantity_needed_kg" in d
            assert "urgency" in d
            assert d["urgency"] in ("high", "medium", "low")

    def test_filter_demands_by_crop(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        demands = svc.get_active_demands(crop_name="tomato")
        for d in demands:
            assert d["crop_name"].lower() == "tomato"

    def test_filter_demands_by_location(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        demands = svc.get_active_demands(
            farmer_lat=26.8, farmer_lng=80.9, max_distance_km=100
        )
        for d in demands:
            if d["distance_km"] is not None:
                assert d["distance_km"] <= 100

    def test_demands_sorted_by_urgency(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        demands = svc.get_active_demands()

        urgency_order = {"high": 0, "medium": 1, "low": 2}
        urgency_values = [urgency_order[d["urgency"]] for d in demands]
        assert urgency_values == sorted(urgency_values)


class TestOfferSystem:
    """Test the offer/negotiation system."""

    def test_create_offer(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        offer = svc.create_offer(
            farmer_id=1,
            buyer_id=1,
            crop_name="tomato",
            quantity_kg=100,
            asking_price_per_kg=28.0,
        )

        assert offer["status"] == "pending"
        assert offer["asking_price_per_kg"] == 28.0
        assert offer["buyer_name"] == "Sharma Vegetables"
        assert "expires_at" in offer

    def test_accept_offer(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        offer = svc.create_offer(
            farmer_id=1, buyer_id=1,
            crop_name="tomato", quantity_kg=50,
            asking_price_per_kg=30.0,
        )

        updated = svc.update_offer_status(offer["id"], "accepted")
        assert updated["status"] == "accepted"

    def test_counter_offer(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        offer = svc.create_offer(
            farmer_id=1, buyer_id=2,
            crop_name="mango", quantity_kg=200,
            asking_price_per_kg=65.0,
        )

        updated = svc.update_offer_status(offer["id"], "counter", counter_price=60.0)
        assert updated["status"] == "counter"
        assert updated["counter_price_per_kg"] == 60.0

    def test_reject_offer(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        offer = svc.create_offer(
            farmer_id=1, buyer_id=3,
            crop_name="onion", quantity_kg=300,
            asking_price_per_kg=35.0,
        )

        updated = svc.update_offer_status(offer["id"], "rejected")
        assert updated["status"] == "rejected"

    def test_offer_for_invalid_buyer(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()
        result = svc.create_offer(
            farmer_id=1, buyer_id=9999,
            crop_name="tomato", quantity_kg=50,
            asking_price_per_kg=25.0,
        )
        assert "error" in result

    def test_list_farmer_offers(self):
        from app.services.buyer_service import BuyerMatchingService

        svc = BuyerMatchingService()

        # Create a few offers
        svc.create_offer(1, 1, "tomato", 50, 25.0)
        svc.create_offer(1, 5, "onion", 100, 22.0)

        offers = svc.get_farmer_offers(farmer_id=1)
        assert len(offers) >= 2


# ---------------------------------------------------------------------------
# API route tests (FastAPI TestClient)
# ---------------------------------------------------------------------------
class TestBuyerAPI:
    """Test buyer matching API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def batch_id(self, client):
        resp = client.post("/api/v1/produce/batches", json={
            "crop_type_id": 1,  # Tomato
            "quantity_kg": 150,
            "harvest_date": (date.today() - timedelta(days=1)).isoformat(),
            "storage_type": "ambient",
        })
        assert resp.status_code == 200
        return resp.json()["id"]

    def test_match_buyers_with_scores(self, client, batch_id):
        resp = client.post("/api/v1/buyers/match", json={
            "batch_id": batch_id,
            "farmer_lat": 26.8,
            "farmer_lng": 80.9,
            "max_distance_km": 2000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_matches"] > 0
        for buyer in data["matched_buyers"]:
            assert "match_score" in buyer
            assert "sub_scores" in buyer

    def test_nearby_buyers(self, client):
        resp = client.get(
            "/api/v1/buyers/nearby",
            params={
                "crop_name": "tomato",
                "lat": 26.8,
                "lng": 80.9,
                "max_distance_km": 2000,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_matches"] > 0

    def test_nearby_with_filters(self, client):
        resp = client.get(
            "/api/v1/buyers/nearby",
            params={
                "crop_name": "tomato",
                "lat": 26.8,
                "lng": 80.9,
                "max_distance_km": 2000,
                "buyer_type": "retailer",
                "min_rating": 4.0,
                "sort_by": "rating",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        for buyer in data["matched_buyers"]:
            assert buyer["buyer_type"] == "retailer"
            assert buyer["rating"] >= 4.0

    def test_active_demands(self, client):
        resp = client.get("/api/v1/buyers/demands")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

    def test_demands_filtered_by_crop(self, client):
        resp = client.get("/api/v1/buyers/demands", params={"crop_name": "tomato"})
        assert resp.status_code == 200
        for d in resp.json()["demands"]:
            assert d["crop_name"].lower() == "tomato"

    def test_create_and_get_offer(self, client):
        # Create
        resp = client.post("/api/v1/buyers/offers", json={
            "buyer_id": 1,
            "crop_name": "tomato",
            "quantity_kg": 100,
            "asking_price_per_kg": 28.0,
        })
        assert resp.status_code == 200
        offer = resp.json()
        assert offer["status"] == "pending"

        # Get
        resp2 = client.get(f"/api/v1/buyers/offers/{offer['id']}")
        assert resp2.status_code == 200
        assert resp2.json()["id"] == offer["id"]

    def test_accept_offer_api(self, client):
        resp = client.post("/api/v1/buyers/offers", json={
            "buyer_id": 1,
            "crop_name": "tomato",
            "quantity_kg": 50,
            "asking_price_per_kg": 25.0,
        })
        offer_id = resp.json()["id"]

        resp2 = client.put(f"/api/v1/buyers/offers/{offer_id}", json={
            "status": "accepted",
        })
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "accepted"

    def test_counter_offer_api(self, client):
        resp = client.post("/api/v1/buyers/offers", json={
            "buyer_id": 2,
            "crop_name": "mango",
            "quantity_kg": 200,
            "asking_price_per_kg": 65.0,
        })
        offer_id = resp.json()["id"]

        resp2 = client.put(f"/api/v1/buyers/offers/{offer_id}", json={
            "status": "counter",
            "counter_price_per_kg": 60.0,
        })
        assert resp2.status_code == 200
        assert resp2.json()["counter_price_per_kg"] == 60.0

    def test_list_offers(self, client):
        resp = client.get("/api/v1/buyers/offers")
        assert resp.status_code == 200
        assert "offers" in resp.json()

    def test_list_all_buyers(self, client):
        resp = client.get("/api/v1/buyers/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

    def test_get_buyer_details(self, client):
        resp = client.get("/api/v1/buyers/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_buyer_not_found(self, client):
        resp = client.get("/api/v1/buyers/99999")
        assert resp.status_code == 404

    def test_match_batch_not_found(self, client):
        resp = client.post("/api/v1/buyers/match", json={
            "batch_id": 99999,
            "farmer_lat": 26.8,
            "farmer_lng": 80.9,
        })
        assert resp.status_code == 404
