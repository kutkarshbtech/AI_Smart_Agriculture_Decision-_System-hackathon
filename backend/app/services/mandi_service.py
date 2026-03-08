"""
Mandi (market) price service — fetches live daily commodity prices from
the Government of India Open Data Portal (data.gov.in).

API:  https://api.data.gov.in/resource/<RESOURCE_ID>
Docs: https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi

Prices returned by the API are in ₹ per quintal (100 kg).
This service normalises them to ₹/kg for downstream consumers and
caches results in-memory (TTL-based) to avoid hitting rate limits.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("swadesh.mandi")

# ── Constants ────────────────────────────────────────────────────────────
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_BASE = "https://api.data.gov.in/resource"
DEFAULT_LIMIT = 50
CACHE_TTL_SECONDS = 15 * 60  # 15 minutes

# Commodity name mapping: our internal lowercase → data.gov.in commodity name
# The API uses title-case names; this map handles common crops
COMMODITY_NAME_MAP: Dict[str, str] = {
    "tomato": "Tomato",
    "potato": "Potato",
    "onion": "Onion",
    "banana": "Banana",
    "mango": "Mango",
    "apple": "Apple",
    "rice": "Rice",
    "wheat": "Wheat",
    "cauliflower": "Cauliflower",
    "spinach": "Spinach",
    "capsicum": "Capsicum",
    "okra": "Ladies Finger",
    "brinjal": "Brinjal",
    "guava": "Guava",
    "grape": "Grape",
    "carrot": "Carrot",
    "cabbage": "Cabbage",
    "peas": "Peas",
    "ginger": "Ginger",
    "garlic": "Garlic",
    "lemon": "Lemon",
    "papaya": "Papaya",
    "watermelon": "Watermelon",
    "pomegranate": "Pomegranate",
    "orange": "Orange",
    "cucumber": "Cucumber",
    "bitter gourd": "Bitter gourd",
    "bottle gourd": "Bottle gourd",
    "maize": "Maize",
    "cotton": "Cotton",
    "soybean": "Soyabean",
    "mustard": "Mustard",
    "chilli": "Chillies (Green)",
    "coriander": "Coriander(Leaves)",
    "turmeric": "Turmeric",
    "coconut": "Coconut",
    "groundnut": "Groundnut",
    "jowar": "Jowar(Sorghum)",
    "bajra": "Bajra(Pearl Millet)",
    "ragi": "Ragi (Finger Millet)",
    "moong": "Green Gram (Moong)",
    "urad": "Black Gram (Urd Beans)",
    "arhar": "Arhar (Tur/Red Gram)",
    "chana": "Bengal Gram(Gram)(Whole)",
    "sugarcane": "Sugarcane",
}


# ── In-memory cache ─────────────────────────────────────────────────────
_cache: Dict[str, Any] = {}  # key → {"data": ..., "ts": float}


def _cache_key(commodity: str, state: Optional[str], market: Optional[str]) -> str:
    return f"{commodity}|{state or ''}|{market or ''}"


def _get_cached(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _set_cache(key: str, data: Any) -> None:
    _cache[key] = {"data": data, "ts": time.time()}


# ── Core API client ─────────────────────────────────────────────────────

class MandiPriceClient:
    """
    Async client for the data.gov.in mandi commodity price API.

    Usage:
        client = MandiPriceClient()
        prices = await client.fetch_prices("tomato", state="Maharashtra")
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 25.0):
        self.api_key = api_key or settings.MANDI_API_KEY
        self.base_url = f"{API_BASE}/{RESOURCE_ID}"
        self.timeout = timeout

        # Warn if API key is missing
        if not self.api_key or self.api_key == "":
            logger.warning(
                "MANDI_API_KEY not configured. "
                "Register at https://data.gov.in/ and request API access from your profile. "
                "Will use simulated data as fallback."
            )

    # ── public methods ──────────────────────────────────────

    async def fetch_prices(
        self,
        commodity: str,
        *,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Fetch current daily prices for a commodity.

        Returns dict with keys:
            records     : List[MandiPriceRecord]
            total       : int  (total matching records from API)
            source      : "data.gov.in"
            cached      : bool
            commodity   : str
        """
        # Normalise commodity name
        api_commodity = COMMODITY_NAME_MAP.get(commodity.lower(), commodity.title())

        # Use simulated data if API key is missing
        if not self.api_key or self.api_key == "":
            return self._generate_simulated_prices(api_commodity, state, limit)

        cache_k = _cache_key(api_commodity, state, market)
        cached = _get_cached(cache_k)
        if cached is not None:
            result = {**cached, "cached": True}
            # data.gov.in does partial/substring matching on state filter,
            # so always post-filter to keep only exact state matches.
            if state:
                result["records"] = [
                    r for r in result["records"]
                    if r.get("state", "").lower() == state.lower()
                ]
            return result

        params = self._build_params(api_commodity, state, district, market, limit, offset)

        records: List[Dict[str, Any]] = []
        total = 0
        api_error: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.base_url, params=params)
                resp.raise_for_status()
                data = resp.json()

                total = int(data.get("total", 0))
                raw_records = data.get("records", [])
                records = [self._parse_record(r) for r in raw_records]

                # data.gov.in does partial/substring matching on filters,
                # e.g. state="Madhya Pradesh" also returns "Himachal Pradesh".
                # Post-filter to keep only exact matches.
                if state:
                    records = [
                        r for r in records
                        if r.get("state", "").lower() == state.lower()
                    ]

        except httpx.HTTPStatusError as exc:
            api_error = f"HTTP {exc.response.status_code}"
            logger.warning("Mandi API HTTP error: %s", api_error)
            # Fallback to simulated data on authentication errors
            if exc.response.status_code in (400, 401, 403):
                return self._generate_simulated_prices(api_commodity, state, limit)
        except httpx.RequestError as exc:
            api_error = str(exc)
            logger.warning("Mandi API request error: %s", api_error)
            # Fallback to simulated data on timeout/connection errors
            return self._generate_simulated_prices(api_commodity, state, limit)
        except Exception as exc:
            api_error = str(exc)
            logger.exception("Unexpected mandi API error")
            return self._generate_simulated_prices(api_commodity, state, limit)

        result = {
            "records": records,
            "total": total,
            "source": "data.gov.in",
            "commodity": api_commodity,
            "api_error": api_error,
            "cached": False,
        }

        if records:
            _set_cache(cache_k, result)

        return result

    async def fetch_prices_multi_market(
        self,
        commodity: str,
        states: Optional[List[str]] = None,
        limit_per_state: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch prices across multiple states in parallel.

        Falls back to a single nationwide query when no states are provided.
        """
        if not states:
            result = await self.fetch_prices(commodity, limit=limit_per_state * 3)
            return result["records"]

        tasks = [
            self.fetch_prices(commodity, state=s, limit=limit_per_state)
            for s in states
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_records: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, dict):
                all_records.extend(r["records"])
        return all_records

    async def search_commodity(
        self, query: str, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for a commodity by partial name.
        Returns matching records so the user can discover available commodities.
        """
        return await self.fetch_prices(query, limit=limit)

    async def get_commodity_summary(
        self,
        commodity: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a summary of current prices for a commodity:
        avg, min, max (in ₹/kg), number of reporting mandis, list of states.
        """
        result = await self.fetch_prices(commodity, state=state, limit=100)
        records = result["records"]

        if not records:
            return {
                "commodity": commodity,
                "num_mandis": 0,
                "avg_price_per_kg": None,
                "min_price_per_kg": None,
                "max_price_per_kg": None,
                "modal_price_per_kg": None,
                "states": [],
                "source": result["source"],
                "api_error": result.get("api_error"),
            }

        modal_prices = [r["modal_price_per_kg"] for r in records]
        min_prices = [r["min_price_per_kg"] for r in records]
        max_prices = [r["max_price_per_kg"] for r in records]
        states_set = {r["state"] for r in records if r.get("state")}

        return {
            "commodity": commodity,
            "num_mandis": len(records),
            "avg_price_per_kg": round(sum(modal_prices) / len(modal_prices), 2),
            "min_price_per_kg": round(min(min_prices), 2),
            "max_price_per_kg": round(max(max_prices), 2),
            "modal_price_per_kg": round(
                sorted(modal_prices)[len(modal_prices) // 2], 2
            ),
            "states": sorted(states_set),
            "source": result["source"],
        }

    # ── sync wrapper for use in non-async code ──────────────

    def fetch_prices_sync(
        self,
        commodity: str,
        *,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        """Synchronous wrapper — for use inside PricingService."""
        api_commodity = COMMODITY_NAME_MAP.get(commodity.lower(), commodity.title())

        # Use simulated data if API key is missing
        if not self.api_key or self.api_key == "":
            return self._generate_simulated_prices(api_commodity, state, limit)

        cache_k = _cache_key(api_commodity, state, market)
        cached = _get_cached(cache_k)
        if cached is not None:
            result = {**cached, "cached": True}
            if state:
                result["records"] = [
                    r for r in result["records"]
                    if r.get("state", "").lower() == state.lower()
                ]
            return result

        params = self._build_params(api_commodity, state, district, market, limit, 0)

        records: List[Dict[str, Any]] = []
        total = 0
        api_error: Optional[str] = None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self.base_url, params=params)
                resp.raise_for_status()
                data = resp.json()

                total = int(data.get("total", 0))
                raw_records = data.get("records", [])
                records = [self._parse_record(r) for r in raw_records]

                # data.gov.in does partial/substring matching on filters,
                # e.g. state="Madhya Pradesh" also returns "Himachal Pradesh".
                # Post-filter to keep only exact matches.
                if state:
                    records = [
                        r for r in records
                        if r.get("state", "").lower() == state.lower()
                    ]

        except httpx.HTTPStatusError as exc:
            api_error = f"HTTP {exc.response.status_code}"
            logger.warning("Mandi API HTTP error (sync): %s", api_error)
            if exc.response.status_code in (400, 401, 403):
                return self._generate_simulated_prices(api_commodity, state, limit)
        except httpx.RequestError as exc:
            api_error = str(exc)
            logger.warning("Mandi API request error (sync): %s", api_error)
            return self._generate_simulated_prices(api_commodity, state, limit)
        except Exception as exc:
            api_error = str(exc)
            logger.exception("Unexpected mandi API error (sync)")
            return self._generate_simulated_prices(api_commodity, state, limit)

        result = {
            "records": records,
            "total": total,
            "source": "data.gov.in",
            "commodity": api_commodity,
            "api_error": api_error,
            "cached": False,
        }

        if records:
            _set_cache(cache_k, result)

        return result

    # ── private helpers ─────────────────────────────────────

    def _build_params(
        self,
        commodity: str,
        state: Optional[str],
        district: Optional[str],
        market: Optional[str],
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        # Filters
        if commodity:
            params["filters[commodity]"] = commodity
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district
        if market:
            params["filters[market]"] = market
        return params

    @staticmethod
    def _parse_record(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single API record into a normalised dict.

        API fields (typical):
            state, district, market, commodity, variety,
            arrival_date (DD/MM/YYYY), min_price, max_price, modal_price
            (prices are ₹ per quintal = 100 kg)
        """
        min_q = float(raw.get("min_price", 0) or 0)
        max_q = float(raw.get("max_price", 0) or 0)
        modal_q = float(raw.get("modal_price", 0) or 0)

        # Parse arrival_date (DD/MM/YYYY)
        raw_date = raw.get("arrival_date", "")
        arrival_date = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                arrival_date = datetime.strptime(raw_date, fmt).date()
                break
            except (ValueError, TypeError):
                continue

        return {
            "state": raw.get("state", ""),
            "district": raw.get("district", ""),
            "market": raw.get("market", ""),
            "commodity": raw.get("commodity", ""),
            "variety": raw.get("variety", ""),
            "arrival_date": arrival_date.isoformat() if arrival_date else raw_date,
            # Per-quintal prices (original)
            "min_price_per_quintal": min_q,
            "max_price_per_quintal": max_q,
            "modal_price_per_quintal": modal_q,
            # Normalised to ₹/kg
            "min_price_per_kg": round(min_q / 100, 2),
            "max_price_per_kg": round(max_q / 100, 2),
            "modal_price_per_kg": round(modal_q / 100, 2),
            "source": "data.gov.in",
        }


    def _generate_simulated_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        """
        Generate simulated mandi prices when API is unavailable.

        Returns realistic price data for demo purposes.
        """
        import random
        from datetime import timedelta

        # Base prices per kg (realistic averages for India)
        base_prices = {
            "tomato": 35, "potato": 25, "onion": 30, "banana": 40,
            "mango": 60, "apple": 120, "cauliflower": 45, "okra": 50,
            "carrot": 40, "capsicum": 70, "cucumber": 35, "beans": 55,
            "rice": 38, "wheat": 28, "brinjal": 30, "cabbage": 20,
            "grapes": 80, "guava": 45, "lemon": 50, "peas": 60,
            "spinach": 25,
        }

        base_price = base_prices.get(commodity.lower(), 50)

        # Major agricultural states
        states_list = [
            "Maharashtra", "Karnataka", "Andhra Pradesh", "Tamil Nadu",
            "Gujarat", "Madhya Pradesh", "Uttar Pradesh", "Punjab",
            "Haryana", "Rajasthan", "West Bengal", "Kerala",
        ]

        if state and state in states_list:
            selected_states = [state]
        else:
            selected_states = random.sample(states_list, min(limit // 3, len(states_list)))

        records = []
        for _ in range(min(limit, 20)):
            state_name = random.choice(selected_states)

            # Generate realistic price variation (±30% from base)
            modal = round(base_price * random.uniform(0.7, 1.3), 2)
            min_price = round(modal * random.uniform(0.85, 0.95), 2)
            max_price = round(modal * random.uniform(1.05, 1.15), 2)

            # Recent dates
            days_ago = random.randint(0, 5)
            arrival_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            records.append({
                "state": state_name,
                "district": f"{state_name[:4]} District {random.randint(1, 5)}",
                "market": f"{state_name[:5]} Mandi {random.randint(1, 10)}",
                "commodity": commodity.title(),
                "variety": "Common" if random.random() > 0.3 else "Local",
                "arrival_date": arrival_date,
                "min_price_per_quintal": min_price * 100,
                "max_price_per_quintal": max_price * 100,
                "modal_price_per_quintal": modal * 100,
                "min_price_per_kg": min_price,
                "max_price_per_kg": max_price,
                "modal_price_per_kg": modal,
                "source": "simulated",
            })

        return {
            "records": records,
            "total": len(records),
            "source": "simulated",
            "commodity": commodity.title(),
            "api_error": "No API key configured - using simulated data",
            "cached": False,
        }


# ── Singleton ────────────────────────────────────────────────────────────
mandi_client = MandiPriceClient()
