"""
Buyer matching service.
Connects farmers to nearby local buyers/shops using a multi-factor scoring
algorithm based on location, crop type, quantity, demand, rating, and pricing.
"""
import math
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta, timezone


# ---------------------------------------------------------------------------
# Demo buyer database (replace with DynamoDB/RDS queries in production)
# ---------------------------------------------------------------------------
DEMO_BUYERS = [
    {
        "id": 1, "shop_name": "Sharma Vegetables", "buyer_type": "retailer",
        "contact_name": "Ramesh Sharma", "contact_phone": "+919876500001",
        "district": "Lucknow", "state": "Uttar Pradesh",
        "latitude": 26.8467, "longitude": 80.9462,
        "preferred_crops": ["tomato", "potato", "onion", "cauliflower", "spinach"],
        "max_quantity_kg": 500, "is_verified": True,
        "rating": 4.5, "total_transactions": 120, "avg_payment_days": 1,
        "languages": ["hi", "en"], "operating_hours": "06:00-20:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 2, "shop_name": "Patel Fruit Mart", "buyer_type": "wholesaler",
        "contact_name": "Suresh Patel", "contact_phone": "+919876500002",
        "district": "Ahmedabad", "state": "Gujarat",
        "latitude": 23.0225, "longitude": 72.5714,
        "preferred_crops": ["mango", "banana", "apple", "guava", "grape"],
        "max_quantity_kg": 1000, "is_verified": True,
        "rating": 4.2, "total_transactions": 85, "avg_payment_days": 3,
        "languages": ["gu", "hi", "en"], "operating_hours": "07:00-19:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi", "bank_transfer"],
    },
    {
        "id": 3, "shop_name": "Kisan Fresh Store", "buyer_type": "retailer",
        "contact_name": "Prakash Yadav", "contact_phone": "+919876500003",
        "district": "Varanasi", "state": "Uttar Pradesh",
        "latitude": 25.3176, "longitude": 82.9739,
        "preferred_crops": ["tomato", "onion", "capsicum", "brinjal", "okra"],
        "max_quantity_kg": 300, "is_verified": True,
        "rating": 4.0, "total_transactions": 60, "avg_payment_days": 0,
        "languages": ["hi"], "operating_hours": "05:30-18:00",
        "accepts_delivery": False, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 4, "shop_name": "Green Valley Traders", "buyer_type": "wholesaler",
        "contact_name": "Anil Kumar", "contact_phone": "+919876500004",
        "district": "Patna", "state": "Bihar",
        "latitude": 25.6093, "longitude": 85.1376,
        "preferred_crops": ["potato", "onion", "cauliflower", "carrot", "rice"],
        "max_quantity_kg": 2000, "is_verified": True,
        "rating": 3.8, "total_transactions": 200, "avg_payment_days": 5,
        "languages": ["hi", "en"], "operating_hours": "06:00-21:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi", "bank_transfer"],
    },
    {
        "id": 5, "shop_name": "Apna Bazaar", "buyer_type": "retailer",
        "contact_name": "Dinesh Mishra", "contact_phone": "+919876500005",
        "district": "Kanpur", "state": "Uttar Pradesh",
        "latitude": 26.4499, "longitude": 80.3319,
        "preferred_crops": ["tomato", "potato", "onion", "spinach", "capsicum"],
        "max_quantity_kg": 400, "is_verified": True,
        "rating": 4.3, "total_transactions": 95, "avg_payment_days": 0,
        "languages": ["hi"], "operating_hours": "06:00-19:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 6, "shop_name": "Fresh Farm Produce", "buyer_type": "retailer",
        "contact_name": "Meera Devi", "contact_phone": "+919876500006",
        "district": "Jaipur", "state": "Rajasthan",
        "latitude": 26.9124, "longitude": 75.7873,
        "preferred_crops": ["onion", "tomato", "capsicum", "okra", "brinjal"],
        "max_quantity_kg": 600, "is_verified": True,
        "rating": 4.6, "total_transactions": 150, "avg_payment_days": 1,
        "languages": ["hi", "en"], "operating_hours": "06:00-20:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 7, "shop_name": "Govind Agri Store", "buyer_type": "aggregator",
        "contact_name": "Govind Singh", "contact_phone": "+919876500007",
        "district": "Bhopal", "state": "Madhya Pradesh",
        "latitude": 23.2599, "longitude": 77.4126,
        "preferred_crops": ["wheat", "rice", "potato", "onion", "tomato"],
        "max_quantity_kg": 5000, "is_verified": True,
        "rating": 4.1, "total_transactions": 300, "avg_payment_days": 7,
        "languages": ["hi", "en"], "operating_hours": "08:00-18:00",
        "accepts_delivery": True, "payment_modes": ["bank_transfer", "upi"],
    },
    {
        "id": 8, "shop_name": "Lakshmi Traders", "buyer_type": "retailer",
        "contact_name": "Lakshmi Narayana", "contact_phone": "+919876500008",
        "district": "Hyderabad", "state": "Telangana",
        "latitude": 17.3850, "longitude": 78.4867,
        "preferred_crops": ["tomato", "capsicum", "brinjal", "okra", "mango"],
        "max_quantity_kg": 800, "is_verified": True,
        "rating": 4.4, "total_transactions": 110, "avg_payment_days": 2,
        "languages": ["te", "hi", "en"], "operating_hours": "06:00-20:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi", "bank_transfer"],
    },
    {
        "id": 9, "shop_name": "Deccan Fresh Market", "buyer_type": "wholesaler",
        "contact_name": "Raju Patil", "contact_phone": "+919876500009",
        "district": "Pune", "state": "Maharashtra",
        "latitude": 18.5204, "longitude": 73.8567,
        "preferred_crops": ["tomato", "onion", "grape", "guava", "banana"],
        "max_quantity_kg": 1500, "is_verified": True,
        "rating": 4.7, "total_transactions": 250, "avg_payment_days": 3,
        "languages": ["mr", "hi", "en"], "operating_hours": "05:00-19:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi", "bank_transfer"],
    },
    {
        "id": 10, "shop_name": "South Fresh Mart", "buyer_type": "retailer",
        "contact_name": "Krishnan Iyer", "contact_phone": "+919876500010",
        "district": "Chennai", "state": "Tamil Nadu",
        "latitude": 13.0827, "longitude": 80.2707,
        "preferred_crops": ["banana", "mango", "rice", "carrot", "spinach"],
        "max_quantity_kg": 700, "is_verified": True,
        "rating": 4.3, "total_transactions": 180, "avg_payment_days": 1,
        "languages": ["ta", "en"], "operating_hours": "06:00-20:00",
        "accepts_delivery": True, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 11, "shop_name": "Nandi Fresh Vegetables", "buyer_type": "retailer",
        "contact_name": "Ravi Shankar", "contact_phone": "+919876500011",
        "district": "Bengaluru", "state": "Karnataka",
        "latitude": 12.9716, "longitude": 77.5946,
        "preferred_crops": ["tomato", "potato", "carrot", "capsicum", "spinach"],
        "max_quantity_kg": 350, "is_verified": True,
        "rating": 4.5, "total_transactions": 90, "avg_payment_days": 0,
        "languages": ["kn", "en", "hi"], "operating_hours": "05:30-19:00",
        "accepts_delivery": False, "payment_modes": ["cash", "upi"],
    },
    {
        "id": 12, "shop_name": "Punjab Grain House", "buyer_type": "aggregator",
        "contact_name": "Gurpreet Singh", "contact_phone": "+919876500012",
        "district": "Ludhiana", "state": "Punjab",
        "latitude": 30.9010, "longitude": 75.8573,
        "preferred_crops": ["wheat", "rice", "potato", "onion"],
        "max_quantity_kg": 10000, "is_verified": True,
        "rating": 4.0, "total_transactions": 500, "avg_payment_days": 7,
        "languages": ["pa", "hi", "en"], "operating_hours": "07:00-17:00",
        "accepts_delivery": True, "payment_modes": ["bank_transfer", "upi"],
    },
]


# ---------------------------------------------------------------------------
# Active demand (buyers who are currently looking for specific crops)
# ---------------------------------------------------------------------------
ACTIVE_DEMANDS: List[Dict[str, Any]] = [
    {"id": 1, "buyer_id": 1, "crop_name": "tomato", "quantity_needed_kg": 200, "max_price_per_kg": 30, "urgency": "high", "valid_until": (date.today() + timedelta(days=2)).isoformat()},
    {"id": 2, "buyer_id": 4, "crop_name": "potato", "quantity_needed_kg": 500, "max_price_per_kg": 22, "urgency": "medium", "valid_until": (date.today() + timedelta(days=5)).isoformat()},
    {"id": 3, "buyer_id": 6, "crop_name": "onion", "quantity_needed_kg": 300, "max_price_per_kg": 28, "urgency": "high", "valid_until": (date.today() + timedelta(days=1)).isoformat()},
    {"id": 4, "buyer_id": 9, "crop_name": "tomato", "quantity_needed_kg": 1000, "max_price_per_kg": 35, "urgency": "low", "valid_until": (date.today() + timedelta(days=7)).isoformat()},
    {"id": 5, "buyer_id": 2, "crop_name": "mango", "quantity_needed_kg": 300, "max_price_per_kg": 70, "urgency": "medium", "valid_until": (date.today() + timedelta(days=3)).isoformat()},
    {"id": 6, "buyer_id": 8, "crop_name": "capsicum", "quantity_needed_kg": 150, "max_price_per_kg": 50, "urgency": "high", "valid_until": (date.today() + timedelta(days=2)).isoformat()},
    {"id": 7, "buyer_id": 10, "crop_name": "banana", "quantity_needed_kg": 400, "max_price_per_kg": 35, "urgency": "medium", "valid_until": (date.today() + timedelta(days=4)).isoformat()},
    {"id": 8, "buyer_id": 12, "crop_name": "wheat", "quantity_needed_kg": 5000, "max_price_per_kg": 28, "urgency": "low", "valid_until": (date.today() + timedelta(days=14)).isoformat()},
    {"id": 9, "buyer_id": 5, "crop_name": "spinach", "quantity_needed_kg": 50, "max_price_per_kg": 30, "urgency": "high", "valid_until": (date.today() + timedelta(days=1)).isoformat()},
    {"id": 10, "buyer_id": 11, "crop_name": "carrot", "quantity_needed_kg": 100, "max_price_per_kg": 30, "urgency": "medium", "valid_until": (date.today() + timedelta(days=3)).isoformat()},
]

# In-memory offer storage
_offers: Dict[int, Dict[str, Any]] = {}
_offer_counter = 0


# ---------------------------------------------------------------------------
# Scoring weights (can be tuned)
# ---------------------------------------------------------------------------
MATCH_WEIGHTS = {
    "distance": 0.25,       # Closer is better
    "rating": 0.20,         # Higher rated is better
    "capacity_fit": 0.15,   # Quantity fit
    "payment_speed": 0.10,  # Faster payment is better
    "demand_urgency": 0.15, # Active urgent demand scores higher
    "reliability": 0.15,    # Verified + transaction count
}


class BuyerMatchingService:
    """
    Advanced buyer matching with multi-factor scoring.

    Matches farmers with nearby buyers based on:
    - Geographic proximity (Haversine)
    - Crop preference overlap
    - Quantity capacity fit
    - Buyer rating & reliability
    - Active demand urgency
    - Payment speed
    """

    # ------------------------------------------------------------------
    # Distance calculation
    # ------------------------------------------------------------------
    def _haversine_km(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _compute_match_score(
        self,
        buyer: Dict[str, Any],
        distance_km: float,
        max_distance_km: float,
        quantity_kg: float,
        crop_name: str,
    ) -> Dict[str, Any]:
        """
        Compute a 0-100 composite match score for a buyer.
        Returns individual sub-scores and the composite score.
        """
        w = MATCH_WEIGHTS

        # Distance score (1.0 for distance=0, 0.0 for distance=max)
        dist_score = max(0.0, 1.0 - (distance_km / max_distance_km))

        # Rating score (0-1 based on 5-star scale)
        rating = buyer.get("rating", 3.0)
        rating_score = min(rating / 5.0, 1.0)

        # Capacity fit score
        max_qty = buyer.get("max_quantity_kg", 100)
        if quantity_kg <= max_qty:
            capacity_score = 1.0
        elif quantity_kg <= max_qty * 2:
            capacity_score = 0.5
        else:
            capacity_score = 0.1

        # Payment speed score
        avg_days = buyer.get("avg_payment_days", 7)
        payment_score = max(0.0, 1.0 - (avg_days / 14.0))

        # Demand urgency score (check active demands)
        demand_score = 0.0
        active_demand = self._get_active_demand(buyer["id"], crop_name)
        if active_demand:
            urgency_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
            demand_score = urgency_map.get(active_demand.get("urgency", "low"), 0.3)

        # Reliability score
        txn_count = buyer.get("total_transactions", 0)
        verified = 1.0 if buyer.get("is_verified", False) else 0.0
        reliability_score = min((txn_count / 200.0), 1.0) * 0.7 + verified * 0.3

        # Composite
        composite = (
            w["distance"] * dist_score
            + w["rating"] * rating_score
            + w["capacity_fit"] * capacity_score
            + w["payment_speed"] * payment_score
            + w["demand_urgency"] * demand_score
            + w["reliability"] * reliability_score
        )

        return {
            "match_score": round(composite * 100, 1),
            "sub_scores": {
                "proximity": round(dist_score * 100, 1),
                "rating": round(rating_score * 100, 1),
                "capacity_fit": round(capacity_score * 100, 1),
                "payment_speed": round(payment_score * 100, 1),
                "demand_urgency": round(demand_score * 100, 1),
                "reliability": round(reliability_score * 100, 1),
            },
        }

    def _get_active_demand(
        self, buyer_id: int, crop_name: str
    ) -> Optional[Dict[str, Any]]:
        """Check if buyer has an active demand request for the crop."""
        today = date.today().isoformat()
        for demand in ACTIVE_DEMANDS:
            if (
                demand["buyer_id"] == buyer_id
                and demand["crop_name"].lower() == crop_name.lower()
                and demand["valid_until"] >= today
            ):
                return demand
        return None

    # ------------------------------------------------------------------
    # Core matching
    # ------------------------------------------------------------------
    def find_matching_buyers(
        self,
        crop_name: str,
        farmer_lat: float,
        farmer_lng: float,
        quantity_kg: float,
        max_distance_km: float = 50,
        buyer_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "score",  # "score" | "distance" | "rating"
    ) -> List[Dict[str, Any]]:
        """
        Find and rank buyers using multi-factor scoring.

        Filters: crop preference, distance, quantity capacity, buyer_type, min_rating.
        Sorting: by composite match_score (default), distance, or rating.
        """
        matches = []

        for buyer in DEMO_BUYERS:
            # Crop filter
            if crop_name.lower() not in [c.lower() for c in buyer["preferred_crops"]]:
                continue

            # Distance filter
            distance = self._haversine_km(
                farmer_lat, farmer_lng,
                buyer["latitude"], buyer["longitude"],
            )
            if distance > max_distance_km:
                continue

            # Quantity capacity (buyer can handle at least 30%)
            if buyer["max_quantity_kg"] < quantity_kg * 0.3:
                continue

            # Optional type filter
            if buyer_type and buyer.get("buyer_type") != buyer_type:
                continue

            # Optional rating filter
            if min_rating and buyer.get("rating", 0) < min_rating:
                continue

            # Compute score
            scoring = self._compute_match_score(
                buyer, distance, max_distance_km, quantity_kg, crop_name
            )

            # Active demand info
            active_demand = self._get_active_demand(buyer["id"], crop_name)

            match_entry = {
                "id": buyer["id"],
                "shop_name": buyer["shop_name"],
                "buyer_type": buyer.get("buyer_type", "retailer"),
                "contact_name": buyer["contact_name"],
                "contact_phone": buyer["contact_phone"],
                "district": buyer["district"],
                "state": buyer["state"],
                "distance_km": distance,
                "max_quantity_kg": buyer["max_quantity_kg"],
                "is_verified": buyer["is_verified"],
                "rating": buyer.get("rating", 0),
                "total_transactions": buyer.get("total_transactions", 0),
                "avg_payment_days": buyer.get("avg_payment_days", 0),
                "preferred_crops": buyer["preferred_crops"],
                "languages": buyer.get("languages", []),
                "operating_hours": buyer.get("operating_hours", ""),
                "accepts_delivery": buyer.get("accepts_delivery", False),
                "payment_modes": buyer.get("payment_modes", []),
                "match_score": scoring["match_score"],
                "sub_scores": scoring["sub_scores"],
                "has_active_demand": active_demand is not None,
                "active_demand": {
                    "quantity_needed_kg": active_demand["quantity_needed_kg"],
                    "max_price_per_kg": active_demand["max_price_per_kg"],
                    "urgency": active_demand["urgency"],
                    "valid_until": active_demand["valid_until"],
                } if active_demand else None,
                "created_at": datetime(2025, 1, 1).isoformat(),
            }
            matches.append(match_entry)

        # Sort
        if sort_by == "distance":
            matches.sort(key=lambda x: x["distance_km"])
        elif sort_by == "rating":
            matches.sort(key=lambda x: x["rating"], reverse=True)
        else:
            matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches

    # ------------------------------------------------------------------
    # Active demand queries
    # ------------------------------------------------------------------
    def get_active_demands(
        self,
        crop_name: Optional[str] = None,
        farmer_lat: Optional[float] = None,
        farmer_lng: Optional[float] = None,
        max_distance_km: float = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all currently active buyer demand requests,
        optionally filtered by crop and buyer proximity.
        """
        today = date.today().isoformat()
        results = []

        for demand in ACTIVE_DEMANDS:
            if demand["valid_until"] < today:
                continue
            if crop_name and demand["crop_name"].lower() != crop_name.lower():
                continue

            # Lookup buyer
            buyer = self.get_buyer_by_id(demand["buyer_id"])
            if not buyer:
                continue

            # Distance filter
            if farmer_lat is not None and farmer_lng is not None:
                dist = self._haversine_km(
                    farmer_lat, farmer_lng,
                    buyer["latitude"], buyer["longitude"],
                )
                if dist > max_distance_km:
                    continue
            else:
                dist = None

            results.append({
                "demand_id": demand["id"],
                "buyer_id": demand["buyer_id"],
                "shop_name": buyer["shop_name"],
                "buyer_type": buyer.get("buyer_type", "retailer"),
                "district": buyer["district"],
                "state": buyer["state"],
                "crop_name": demand["crop_name"],
                "quantity_needed_kg": demand["quantity_needed_kg"],
                "max_price_per_kg": demand["max_price_per_kg"],
                "urgency": demand["urgency"],
                "valid_until": demand["valid_until"],
                "distance_km": dist,
                "buyer_rating": buyer.get("rating", 0),
            })

        # Sort by urgency then distance
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        results.sort(key=lambda x: (
            urgency_order.get(x["urgency"], 2),
            x["distance_km"] if x["distance_km"] is not None else 9999,
        ))

        return results

    # ------------------------------------------------------------------
    # Offer / negotiation system
    # ------------------------------------------------------------------
    def create_offer(
        self,
        farmer_id: int,
        buyer_id: int,
        crop_name: str,
        quantity_kg: float,
        asking_price_per_kg: float,
        batch_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a sell offer from farmer to buyer.
        The buyer can accept, counter, or reject.
        """
        global _offer_counter

        buyer = self.get_buyer_by_id(buyer_id)
        if not buyer:
            return {"error": "Buyer not found"}

        _offer_counter += 1
        offer = {
            "id": _offer_counter,
            "farmer_id": farmer_id,
            "buyer_id": buyer_id,
            "buyer_name": buyer["shop_name"],
            "crop_name": crop_name,
            "quantity_kg": quantity_kg,
            "asking_price_per_kg": asking_price_per_kg,
            "batch_id": batch_id,
            "status": "pending",  # pending, accepted, counter, rejected, expired
            "counter_price_per_kg": None,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        }

        _offers[offer["id"]] = offer
        return offer

    def get_offer(self, offer_id: int) -> Optional[Dict[str, Any]]:
        """Get offer details by ID."""
        return _offers.get(offer_id)

    def update_offer_status(
        self,
        offer_id: int,
        status: str,
        counter_price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an offer's status (accept/reject/counter)."""
        offer = _offers.get(offer_id)
        if not offer:
            return None

        if status not in ("accepted", "rejected", "counter"):
            return None

        offer["status"] = status
        offer["updated_at"] = datetime.now(timezone.utc).isoformat()
        if status == "counter" and counter_price is not None:
            offer["counter_price_per_kg"] = counter_price

        return offer

    def get_farmer_offers(
        self, farmer_id: int, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all offers for a farmer, optionally filtered by status."""
        offers = [o for o in _offers.values() if o["farmer_id"] == farmer_id]
        if status:
            offers = [o for o in offers if o["status"] == status]
        offers.sort(key=lambda x: x["created_at"], reverse=True)
        return offers

    # ------------------------------------------------------------------
    # Buyer lookup
    # ------------------------------------------------------------------
    def get_buyer_by_id(self, buyer_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific buyer's details."""
        for buyer in DEMO_BUYERS:
            if buyer["id"] == buyer_id:
                return buyer
        return None

    def get_all_buyers(
        self,
        buyer_type: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all buyers with optional filters."""
        buyers = DEMO_BUYERS
        if buyer_type:
            buyers = [b for b in buyers if b.get("buyer_type") == buyer_type]
        if state:
            buyers = [b for b in buyers if b["state"].lower() == state.lower()]
        return buyers


# Singleton
buyer_service = BuyerMatchingService()
