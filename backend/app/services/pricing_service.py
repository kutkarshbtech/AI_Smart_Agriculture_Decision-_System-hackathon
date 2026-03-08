"""
Pricing intelligence service.
Forecasts market prices, generates seller-friendly price recommendations
using an XGBoost ML model with causal explanation support.

When a data.gov.in API key is configured, live mandi prices are used
to ground the ML model; otherwise simulated prices serve as fallback.
"""
import logging
import random
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from ml.pricing.model import price_model
from ml.pricing.features import (
    build_features,
    features_to_vector,
    MSP_DATA,
    PERISHABILITY_INDEX,
    remaining_shelf_life_ratio,
)
from app.services.mandi_service import mandi_client
from app.core.config import settings

logger = logging.getLogger("swadesh.pricing")


# Simulated market data for hackathon demo (replace with live API later)
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

DEFAULT_PRICE = {"base_price": 30, "volatility": 0.2, "season_factor": {"summer": 1.0, "winter": 1.0, "monsoon": 1.0, "spring": 1.0}}

# Indian mandi names for demo
NEARBY_MANDIS = [
    "Azadpur Mandi, Delhi",
    "Vashi APMC, Mumbai",
    "Koyambedu Market, Chennai",
    "Devaraja Market, Mysuru",
    "Gaddiannaram, Hyderabad",
    "Bowenpally, Hyderabad",
    "Gultekdi Market, Pune",
    "Yeshwanthpur APMC, Bengaluru",
]

# Demand simulation by season × crop category
DEMAND_INDEX_TABLE = {
    ("summer", "vegetable"): 0.55,
    ("summer", "fruit"): 0.75,
    ("summer", "grain"): 0.40,
    ("monsoon", "vegetable"): 0.70,
    ("monsoon", "fruit"): 0.60,
    ("monsoon", "grain"): 0.50,
    ("spring", "vegetable"): 0.50,
    ("spring", "fruit"): 0.55,
    ("spring", "grain"): 0.55,
    ("winter", "vegetable"): 0.45,
    ("winter", "fruit"): 0.65,
    ("winter", "grain"): 0.45,
}

CROP_CATEGORY_MAP = {
    "tomato": "vegetable", "potato": "vegetable", "onion": "vegetable",
    "banana": "fruit", "mango": "fruit", "apple": "fruit",
    "rice": "grain", "wheat": "grain",
    "cauliflower": "vegetable", "spinach": "vegetable", "capsicum": "vegetable",
    "okra": "vegetable", "brinjal": "vegetable",
    "guava": "fruit", "grape": "fruit", "carrot": "vegetable",
}


class PricingService:
    """
    Market price intelligence and recommendation engine.

    Combines simulated market data with an XGBoost ML model
    to provide seller-friendly price recommendations with
    causal explanations and what-if analysis.
    """

    def __init__(self):
        # Ensure ML model is available (trains if needed)
        if not price_model.is_trained:
            try:
                price_model.train(n_samples=10_000)
            except Exception as e:
                print(f"[PricingService] ML model training skipped: {e}")

        # Track whether we have a usable mandi API key
        self._has_mandi_key = bool(mandi_client.api_key)

    def _get_current_season(self) -> str:
        month = date.today().month
        if month in (3, 4, 5):
            return "summer"
        elif month in (6, 7, 8, 9):
            return "monsoon"
        elif month in (10, 11):
            return "spring"
        else:
            return "winter"

    def _get_demand_index(self, crop_name: str) -> float:
        """Estimate demand index for current season and crop."""
        season = self._get_current_season()
        category = CROP_CATEGORY_MAP.get(crop_name.lower(), "vegetable")
        base = DEMAND_INDEX_TABLE.get((season, category), 0.5)
        # Add small day-of-week variation (weekends slightly higher)
        dow = date.today().weekday()
        if dow >= 5:
            base = min(base + 0.05, 1.0)
        return round(base, 2)

    # ── Live mandi data ──────────────────────────────────────

    def get_live_mandi_price(
        self,
        crop_name: str,
        state: Optional[str] = None,
        market: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Try to fetch live mandi prices via data.gov.in.
        Returns a summary dict or None if unavailable.
        """
        if not self._has_mandi_key:
            return None

        try:
            result = mandi_client.fetch_prices_sync(
                crop_name, state=state, market=market, limit=30,
            )
            records = result.get("records", [])
            if not records:
                return None

            modal_prices = [r["modal_price_per_kg"] for r in records]
            min_prices = [r["min_price_per_kg"] for r in records]
            max_prices = [r["max_price_per_kg"] for r in records]

            return {
                "modal_price": round(sum(modal_prices) / len(modal_prices), 2),
                "min_price": round(min(min_prices), 2),
                "max_price": round(max(max_prices), 2),
                "mandi_name": records[0].get("market", "N/A"),
                "source": "data.gov.in",
                "num_mandis": len(records),
                "records": records,
            }
        except Exception as exc:
            logger.warning("Live mandi price fetch failed for %s: %s", crop_name, exc)
            return None

    def _get_market_price_today(
        self,
        crop_name: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get today's market price — live mandi data first, with retry.
        Falls back to simulated data if the external API is unreachable,
        even in AWS_ONLY mode (with a warning), because data.gov.in
        availability is outside our control.
        """
        # Try up to 2 times (initial + 1 retry) to handle transient timeouts
        live = None
        for attempt in range(2):
            live = self.get_live_mandi_price(crop_name, state=state)
            if live:
                break
            if attempt == 0:
                import time
                time.sleep(1)  # brief pause before retry

        if live:
            return {
                "crop_name": crop_name,
                "mandi_name": live["mandi_name"],
                "min_price": live["min_price"],
                "max_price": live["max_price"],
                "modal_price": live["modal_price"],
                "date": date.today().isoformat(),
                "source": "data.gov.in",
                "num_mandis": live["num_mandis"],
            }

        if settings.AWS_ONLY:
            logger.warning(
                "AWS_ONLY mode: Live mandi price fetch failed for '%s' after retries. "
                "Falling back to simulated data.",
                crop_name,
            )

        # Fallback to simulation
        sim = self._simulate_daily_price(crop_name, date.today())
        sim["num_mandis"] = 0
        sim["source"] = "simulated (mandi API unavailable)"
        return sim

    def _simulate_daily_price(
        self, crop_name: str, target_date: date
    ) -> Dict[str, Any]:
        """Generate realistic-looking price data for a given crop and date."""
        crop_data = MARKET_PRICE_DATA.get(crop_name.lower(), DEFAULT_PRICE)
        season = self._get_current_season()
        season_multiplier = crop_data["season_factor"].get(season, 1.0)

        base = crop_data["base_price"] * season_multiplier
        volatility = crop_data["volatility"]

        # Deterministic-ish variation based on date
        day_seed = target_date.toordinal()
        random.seed(day_seed + hash(crop_name))
        daily_variation = random.gauss(0, volatility)

        modal_price = round(base * (1 + daily_variation), 2)
        min_price = round(modal_price * 0.85, 2)
        max_price = round(modal_price * 1.15, 2)

        mandi = random.choice(NEARBY_MANDIS)

        return {
            "crop_name": crop_name,
            "mandi_name": mandi,
            "min_price": max(min_price, 1),
            "max_price": max(max_price, 1),
            "modal_price": max(modal_price, 1),
            "date": target_date.isoformat(),
            "source": "simulated",
        }

    def get_daily_prices(
        self, crop_name: str, days: int = 7, state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily prices for the past N days.
        Uses live data for 'today' when available, simulated for history.
        """
        prices = []
        for i in range(days, 0, -1):
            target = date.today() - timedelta(days=i)
            prices.append(self._simulate_daily_price(crop_name, target))

        # Today: try live data first
        today_data = self._get_market_price_today(crop_name, state=state)
        prices.append(today_data)
        return prices

    def get_price_trend(self, crop_name: str) -> str:
        """Analyze recent price trend: rising, falling, or stable."""
        prices = self.get_daily_prices(crop_name, days=7)
        modal_prices = [p["modal_price"] for p in prices]

        if len(modal_prices) < 3:
            return "stable"

        recent_avg = sum(modal_prices[-3:]) / 3
        earlier_avg = sum(modal_prices[:3]) / 3

        change_pct = (recent_avg - earlier_avg) / earlier_avg

        if change_pct > 0.05:
            return "rising"
        elif change_pct < -0.05:
            return "falling"
        return "stable"

    def forecast_prices(self, crop_name: str, days_ahead: int = 3) -> List[Dict[str, Any]]:
        """
        Forecast prices for the next N days.
        Uses trend extrapolation from historical simulated data.
        (Legacy method — prefer forecast_prices_weather for weather-aware forecasts.)
        """
        prices_7d = self.get_daily_prices(crop_name, 7)
        modal_prices = [p["modal_price"] for p in prices_7d]
        avg = sum(modal_prices) / len(modal_prices) if modal_prices else 30
        trend = self.get_price_trend(crop_name)

        trend_mult = {"rising": 1.015, "falling": 0.985, "stable": 1.0}[trend]

        forecasts = []
        for i in range(1, days_ahead + 1):
            target_date = date.today() + timedelta(days=i)
            projected = round(avg * (trend_mult ** i), 2)
            forecasts.append({
                "date": target_date.isoformat(),
                "predicted_price": projected,
                "confidence": round(max(0.5, 0.9 - 0.05 * i), 2),
                "trend": trend,
            })
        return forecasts

    async def forecast_prices_weather(
        self,
        crop_name: str,
        days_ahead: int = 5,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        quality_grade: Optional[str] = None,
        storage_type: str = "ambient",
        harvest_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Weather-aware price & crop health forecast.

        Uses OpenWeatherMap 5-day forecast to model how upcoming weather
        conditions affect crop shelf life, spoilage risk, and therefore
        the ideal selling price window.

        Returns:
            daily_forecast: per-day weather + crop health + price impact
            overall_advisory: sell/wait/store recommendation
            weather_source: "openweathermap" or "fallback_estimate"
        """
        from app.services.weather_service import weather_service
        from app.services.spoilage_service import spoilage_service

        crop = crop_name.lower()
        crop_data = MARKET_PRICE_DATA.get(crop, DEFAULT_PRICE)

        # ── Get current market price baseline ───────────────
        today_price = self._get_market_price_today(crop_name)
        market_modal = today_price["modal_price"]
        data_source = today_price.get("source", "simulated")

        # ── Crop health baseline ────────────────────────────
        if harvest_date is None:
            harvest_date = date.today() - timedelta(days=1)

        crop_shelf = spoilage_service.get_crop_data(crop_name)
        shelf_days = crop_shelf["cold_days"] if storage_type in ("cold", "controlled") else crop_shelf["ambient_days"]
        optimal_temp_min, optimal_temp_max = crop_shelf["optimal_temp"]
        optimal_hum_min, optimal_hum_max = crop_shelf["optimal_humidity"]

        days_since = max((date.today() - harvest_date).days, 0)
        remaining_shelf = max(shelf_days - days_since, 0)

        quality_mult = {"excellent": 1.0, "good": 0.95, "average": 0.85, "poor": 0.70}
        base_quality = quality_mult.get(quality_grade, 0.90)

        perishability = PERISHABILITY_INDEX.get(crop, 0.5)

        # ── Get weather forecast ────────────────────────────
        weather_forecast = await weather_service.get_weather_forecast(
            city=city, lat=lat, lng=lng,
        )
        weather_source = weather_forecast[0].get("source", "unknown") if weather_forecast else "unknown"
        forecast_city = weather_forecast[0].get("city", "Unknown") if weather_forecast else "Unknown"

        # ── Build daily forecast ────────────────────────────
        daily_forecast: List[Dict[str, Any]] = []
        cumulative_spoilage = 0.0

        for i, day_weather in enumerate(weather_forecast[:days_ahead]):
            day_num = i + 1
            forecast_date = date.today() + timedelta(days=day_num)

            temp = day_weather["temp_avg"]
            temp_max = day_weather["temp_max"]
            humidity = day_weather["humidity_avg"]
            rainfall = day_weather["rainfall_mm"]
            condition = day_weather["condition"]

            # ── Spoilage acceleration from weather ──────────
            temp_factor = spoilage_service.calculate_temperature_factor(
                temp, optimal_temp_min, optimal_temp_max,
            )
            humidity_factor = spoilage_service.calculate_humidity_factor(
                humidity, optimal_hum_min, optimal_hum_max,
            )
            # Rain increases ambient humidity risk and transport delays
            rain_factor = 1.0 + min(rainfall / 20, 0.5)  # up to +50%

            daily_degradation = temp_factor * humidity_factor * rain_factor
            cumulative_spoilage += daily_degradation * perishability

            # Effective remaining shelf life considering weather
            effective_remaining = max(remaining_shelf - day_num * daily_degradation, 0)
            shelf_ratio = effective_remaining / shelf_days if shelf_days > 0 else 0

            # ── Crop health score (0-100) ───────────────────
            # Starts from quality baseline, degrades with weather
            health_score = max(0, min(100, base_quality * 100 - cumulative_spoilage * 15))

            # ── Price impact from weather ───────────────────
            # Supply-side: bad weather = supply disruption = prices rise
            supply_impact = 0.0
            if condition in ("Rain", "Thunderstorm", "Drizzle"):
                supply_impact += 0.03  # transport disruptions → supply tightens
            if temp_max > 38:
                supply_impact += 0.02  # extreme heat → faster field/transit spoilage
            if rainfall > 15:
                supply_impact += 0.04  # heavy rain → logistics disruption

            # Demand-side: extreme weather can shift demand
            demand_impact = 0.0
            if temp_max > 35:
                demand_impact += 0.01  # slight increase for essentials
            if condition in ("Rain", "Thunderstorm") and rainfall > 10:
                demand_impact -= 0.02  # fewer buyers at mandi

            # Farmer's produce quality impact (this specific batch)
            quality_penalty = 0.0
            if storage_type == "ambient":
                # Ambient storage is vulnerable to weather
                if temp > optimal_temp_max + 5:
                    quality_penalty = -0.05 * day_num  # accelerating quality loss
                if humidity > optimal_hum_max + 10:
                    quality_penalty -= 0.03

            net_price_impact = supply_impact + demand_impact + quality_penalty
            projected_price = round(market_modal * (1 + net_price_impact), 2)

            # ── Weather risk level for this crop ────────────
            if daily_degradation > 2.0:
                weather_risk = "high"
            elif daily_degradation > 1.3:
                weather_risk = "medium"
            else:
                weather_risk = "low"

            # ── Advisory for the day ────────────────────────
            day_advisory = self._weather_day_advisory(
                crop_name, temp, temp_max, humidity, rainfall, condition,
                optimal_temp_min, optimal_temp_max, storage_type,
                weather_risk, health_score,
            )

            daily_forecast.append({
                "date": forecast_date.isoformat(),
                "day_number": day_num,
                "weather": {
                    "temp_avg": temp,
                    "temp_max": temp_max,
                    "temp_min": day_weather["temp_min"],
                    "humidity": humidity,
                    "rainfall_mm": rainfall,
                    "condition": condition,
                    "description": day_weather["description"],
                    "wind_speed": day_weather["wind_speed_avg"],
                },
                "crop_health": {
                    "health_score": round(health_score, 1),
                    "effective_shelf_life_days": round(effective_remaining, 1),
                    "daily_degradation_rate": round(daily_degradation, 2),
                    "weather_risk": weather_risk,
                    "spoilage_factors": {
                        "temperature": round(temp_factor, 2),
                        "humidity": round(humidity_factor, 2),
                        "rainfall": round(rain_factor, 2),
                    },
                },
                "price_impact": {
                    "projected_price": projected_price,
                    "supply_impact_pct": round(supply_impact * 100, 1),
                    "demand_impact_pct": round(demand_impact * 100, 1),
                    "quality_impact_pct": round(quality_penalty * 100, 1),
                    "net_impact_pct": round(net_price_impact * 100, 1),
                },
                "advisory": day_advisory,
            })

        # ── Overall recommendation ──────────────────────────
        overall = self._weather_overall_advisory(
            crop_name, daily_forecast, remaining_shelf, perishability,
            market_modal, storage_type,
        )

        return {
            "crop_name": crop_name,
            "current_market_price": market_modal,
            "price_source": data_source,
            "location": forecast_city,
            "weather_source": weather_source,
            "quality_grade": quality_grade or "unassessed",
            "storage_type": storage_type,
            "remaining_shelf_life_days": remaining_shelf,
            "daily_forecast": daily_forecast,
            **overall,
        }

    def _weather_day_advisory(
        self,
        crop_name: str,
        temp: float,
        temp_max: float,
        humidity: float,
        rainfall: float,
        condition: str,
        optimal_temp_min: float,
        optimal_temp_max: float,
        storage_type: str,
        weather_risk: str,
        health_score: float,
    ) -> str:
        """Generate a daily advisory based on weather + crop health."""
        parts = []

        if temp_max > 38:
            parts.append(f"Extreme heat ({temp_max}°C) expected — accelerates spoilage for {crop_name}.")
        elif temp > optimal_temp_max + 5:
            parts.append(f"Temperature ({temp}°C) significantly above optimal ({optimal_temp_min}-{optimal_temp_max}°C) for {crop_name}.")

        if rainfall > 15:
            parts.append("Heavy rain likely — mandi transport may be disrupted, causing supply shortages and price spikes.")
        elif rainfall > 5:
            parts.append("Light to moderate rain — plan transport timing carefully.")

        if humidity > 85 and storage_type == "ambient":
            parts.append(f"High humidity ({humidity}%) promotes fungal growth. Consider moving to cold storage.")

        if health_score < 50:
            parts.append("⚠️ Crop health declining — sell as soon as possible to avoid value loss.")
        elif health_score < 70:
            parts.append("Crop health moderate — consider selling within 1-2 days.")

        if weather_risk == "low" and health_score > 80:
            parts.append("Weather conditions are favorable — safe to hold if market timing is better.")

        return " ".join(parts) if parts else "Weather conditions are normal for this crop."

    def _weather_overall_advisory(
        self,
        crop_name: str,
        daily_forecast: List[Dict[str, Any]],
        remaining_shelf: int,
        perishability: float,
        market_price: float,
        storage_type: str,
    ) -> Dict[str, Any]:
        """Generate the overall sell/wait/store recommendation."""
        health_scores = [d["crop_health"]["health_score"] for d in daily_forecast]
        projected_prices = [d["price_impact"]["projected_price"] for d in daily_forecast]
        weather_risks = [d["crop_health"]["weather_risk"] for d in daily_forecast]

        min_health = min(health_scores) if health_scores else 0
        max_price_day = max(range(len(projected_prices)), key=lambda i: projected_prices[i]) if projected_prices else 0
        best_price = projected_prices[max_price_day] if projected_prices else market_price
        high_risk_days = sum(1 for r in weather_risks if r == "high")

        # Decision logic
        if min_health < 40 or remaining_shelf <= 2:
            action = "sell_now"
            reason = (
                f"Your {crop_name} health is projected to drop below safe levels. "
                "Sell immediately to maximize returns before quality deteriorates further."
            )
            best_day = daily_forecast[0]["date"] if daily_forecast else date.today().isoformat()
        elif high_risk_days >= 3 and perishability > 0.5:
            action = "sell_now"
            reason = (
                f"Weather forecast shows {high_risk_days} high-risk days ahead for {crop_name}. "
                "With high perishability, selling now avoids weather-driven losses."
            )
            best_day = daily_forecast[0]["date"]
        elif best_price > market_price * 1.03 and min_health > 70:
            action = "wait"
            reason = (
                f"Weather disruptions may push prices up to ₹{best_price}/kg "
                f"(+{((best_price / market_price) - 1) * 100:.1f}%) by day {max_price_day + 1}. "
                f"Crop health remains strong (>{min_health:.0f}/100). Consider waiting."
            )
            best_day = daily_forecast[max_price_day]["date"]
        elif perishability < 0.3 and min_health > 80 and storage_type in ("cold", "controlled"):
            action = "store"
            reason = (
                f"{crop_name.title()} is well-suited for storage. Weather won't significantly "
                "impact cold-stored produce. Wait for better market conditions."
            )
            best_day = daily_forecast[-1]["date"] if daily_forecast else date.today().isoformat()
        else:
            action = "sell_now"
            reason = (
                "Market conditions and weather outlook suggest selling at current rates "
                "is a sound decision."
            )
            best_day = daily_forecast[0]["date"] if daily_forecast else date.today().isoformat()

        return {
            "overall_action": action,
            "overall_reason": reason,
            "best_selling_day": best_day,
            "best_projected_price": best_price,
            "health_trend": (
                "declining" if health_scores and health_scores[-1] < health_scores[0] - 10
                else "stable" if health_scores
                else "unknown"
            ),
        }

    def generate_price_recommendation(
        self,
        crop_name: str,
        quantity_kg: float,
        quality_grade: Optional[str] = None,
        spoilage_risk: Optional[str] = None,
        remaining_shelf_life_days: Optional[int] = None,
        spoilage_probability: Optional[float] = None,
        harvest_date: Optional[date] = None,
        storage_type: str = "ambient",
        storage_temp: Optional[float] = None,
        storage_humidity: Optional[float] = None,
        farmer_lat: Optional[float] = None,
        farmer_lng: Optional[float] = None,
        farmer_district: Optional[str] = None,
        damage_score: Optional[float] = None,
        damage_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered price recommendation with seller protection.

        Uses the XGBoost ML model for prediction and provides:
        - Ideal selling price range (min, ideal, max)
        - Seller-protected floor price (MSP-aware)
        - Confidence score
        - Explainable factors with weights
        - Actionable sell/wait recommendation
        - 3-day price forecast
        - What-if scenarios
        """
        # ── Check for unsellable produce due to high damage ────
        if damage_score is not None and damage_score > 60:
            return self._generate_unsellable_recommendation(
                crop_name, quantity_kg, damage_score, damage_level, "high_damage"
            )

        if damage_level and damage_level.lower() in ["severe", "critical", "high"]:
            return self._generate_unsellable_recommendation(
                crop_name, quantity_kg, damage_score, damage_level, "high_damage"
            )

        # Check for critically poor quality
        if quality_grade and quality_grade.lower() == "rotten":
            return self._generate_unsellable_recommendation(
                crop_name, quantity_kg, damage_score, damage_level, "rotten"
            )

        # Get current market data (live → simulated fallback)
        today_price = self._get_market_price_today(crop_name)
        trend = self.get_price_trend(crop_name)
        prices_7d = self.get_daily_prices(crop_name, 7)
        modal_prices_7d = [p["modal_price"] for p in prices_7d]
        avg_7d = sum(modal_prices_7d) / len(modal_prices_7d)

        market_modal = today_price["modal_price"]
        data_source = today_price.get("source", "simulated")
        demand_index = self._get_demand_index(crop_name)

        # When live mandi data is used for today but simulated for history,
        # the avg_7d can diverge wildly from the live price, creating an
        # unrealistic price_momentum signal. Anchor avg_7d to live price
        # with a small simulated spread so the model sees consistent data.
        if data_source == "data.gov.in" and market_modal > 0:
            sim_avg = avg_7d
            # Blend: weight live price heavily so momentum stays realistic
            avg_7d = market_modal * 0.6 + sim_avg * 0.4

        # Default harvest date to today if not provided
        if harvest_date is None:
            harvest_date = date.today() - timedelta(days=1)

        # ── ML-based prediction ─────────────────────────────────
        ml_result = price_model.predict(
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
            market_price_today=market_modal,
            market_price_avg_7d=avg_7d,
            demand_index=demand_index,
        )

        ideal_price = ml_result["ideal_price"]
        min_acceptable = ml_result["min_acceptable_price"]
        price_range_lower = ml_result["price_range_lower"]
        price_range_upper = ml_result["price_range_upper"]
        confidence = ml_result["confidence"]
        factors = ml_result["factors"]

        predicted_market = round(market_modal, 2)

        # ── Action recommendation ───────────────────────────────
        action, action_text = self._determine_action(
            crop_name, trend, spoilage_risk, remaining_shelf_life_days,
            ideal_price, min_acceptable, demand_index,
        )

        # ── 3-day price forecast ────────────────────────────────
        forecast = self.forecast_prices(crop_name, days_ahead=3)

        # ── What-if scenarios ───────────────────────────────────
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
            market_price_today=market_modal,
            market_price_avg_7d=avg_7d,
            demand_index=demand_index,
        )
        what_if_scenarios = self._generate_what_if_scenarios(
            ml_result, crop_name, features, storage_temp
        )

        # ── Build recommendation text ───────────────────────────
        recommendation_text = (
            f"Based on AI analysis of market trends, quality, and demand, "
            f"your {crop_name} (quality: {quality_grade or 'unassessed'}) "
            f"should sell between ₹{min_acceptable}/kg and ₹{price_range_upper}/kg. "
            f"Ideal price: ₹{ideal_price}/kg. {action_text}."
        )

        # MSP note
        crop_lower = crop_name.lower()
        msp_note = None
        if crop_lower in MSP_DATA:
            msp = MSP_DATA[crop_lower]
            if min_acceptable >= msp:
                msp_note = f"Your minimum price ₹{min_acceptable}/kg is above MSP of ₹{msp}/kg ✓"
            else:
                msp_note = f"Warning: recommended price is near MSP floor of ₹{msp}/kg"

        return {
            "sellable": True,
            "recommended_min_price": min_acceptable,
            "recommended_max_price": price_range_upper,
            "ideal_price": ideal_price,
            "price_range_lower": price_range_lower,
            "price_range_upper": price_range_upper,
            "predicted_market_price": predicted_market,
            "confidence_score": confidence,
            "factors": factors,
            "recommendation_text": recommendation_text,
            "action": action,
            "action_text": action_text,
            "msp_note": msp_note,
            "demand_index": demand_index,
            "price_forecast_3d": forecast,
            "what_if_scenarios": what_if_scenarios,
            "valid_until": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
            "trend": trend,
            "avg_7d": round(avg_7d, 2),
            "model_type": "xgboost" if price_model.is_trained else "rule_based",
            "price_source": data_source,
        }

    def _generate_unsellable_recommendation(
        self,
        crop_name: str,
        quantity_kg: float,
        damage_score: Optional[float],
        damage_level: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        """Generate recommendation for unsellable produce."""
        if reason == "high_damage":
            action = "discard_or_compost"
            action_text = (
                f"This {crop_name} has severe physical damage "
                f"(damage score: {damage_score or 'N/A'}%, level: {damage_level or 'high'}). "
                f"It is NOT recommended for commercial sale. Consider composting, "
                f"animal feed, or biogas production instead."
            )
            recommendation_text = (
                f"Unfortunately, your {crop_name} has excessive damage and cannot be sold "
                f"in commercial markets. The produce does not meet minimum quality standards "
                f"for human consumption."
            )
        elif reason == "rotten":
            action = "discard"
            action_text = (
                f"This {crop_name} is classified as rotten and is unsuitable for sale. "
                f"Dispose of properly to prevent contamination of other produce."
            )
            recommendation_text = (
                f"Your {crop_name} is rotten and cannot be sold. Please discard it properly "
                f"to maintain food safety standards."
            )
        else:
            action = "not_sellable"
            action_text = "This produce does not meet minimum quality standards for sale."
            recommendation_text = f"Your {crop_name} is not suitable for commercial sale."

        return {
            "sellable": False,
            "recommended_min_price": 0,
            "recommended_max_price": 0,
            "ideal_price": 0,
            "price_range_lower": 0,
            "price_range_upper": 0,
            "predicted_market_price": 0,
            "confidence_score": 1.0,
            "factors": [],
            "recommendation_text": recommendation_text,
            "action": action,
            "action_text": action_text,
            "msp_note": None,
            "demand_index": 0,
            "price_forecast_3d": [],
            "what_if_scenarios": [],
            "valid_until": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "trend": "n/a",
            "avg_7d": 0,
            "model_type": "rule_based",
            "price_source": "n/a",
            "damage_score": damage_score,
            "damage_level": damage_level,
            "unsellable_reason": reason,
        }

    def _determine_action(
        self,
        crop_name: str,
        trend: str,
        spoilage_risk: Optional[str],
        remaining_shelf_life_days: Optional[int],
        ideal_price: float,
        min_acceptable: float,
        demand_index: float,
    ) -> tuple:
        """Determine the sell/wait/store action and explanation."""
        # Critical spoilage → sell now
        if spoilage_risk in ("critical", "high") and remaining_shelf_life_days and remaining_shelf_life_days <= 2:
            return "sell_now", "Sell immediately — produce quality is declining rapidly"

        # Very high demand + rising prices → wait (if shelf life allows)
        if (
            trend == "rising"
            and demand_index > 0.6
            and spoilage_risk in ("low", None)
            and (remaining_shelf_life_days or 10) > 5
        ):
            return "wait", f"Prices are rising and demand is high ({demand_index:.0%}). Consider waiting 2-3 days for better rates"

        # Falling prices → sell
        if trend == "falling":
            return "sell_now", "Market prices are falling — selling soon is recommended"

        # Good shelf life + cold storage possible → consider storing
        perishability = PERISHABILITY_INDEX.get(crop_name.lower(), 0.5)
        if (
            perishability < 0.3
            and (remaining_shelf_life_days or 10) > 14
            and trend == "stable"
            and demand_index < 0.4
        ):
            return "store", "Low perishability and weak demand — consider cold storage for 1-2 weeks to wait for better prices"

        return "sell_now", "Market conditions are stable — good time to sell"

    def _generate_what_if_scenarios(
        self,
        base_prediction: Dict[str, Any],
        crop_name: str,
        features: Dict[str, float],
        current_temp: Optional[float],
    ) -> List[Dict[str, Any]]:
        """Generate 2-3 causal what-if scenarios for explainability."""
        scenarios = []

        # Scenario 1: What if quality improves?
        if features["quality_code"] < 3:
            result = price_model.what_if(
                base_prediction, {"quality_code": 3.0}, crop_name, features
            )
            scenarios.append({
                "scenario": "If quality improves to 'excellent'",
                "price_change": f"₹{result['price_change']:+.2f}/kg ({result['price_change_pct']:+.1f}%)",
                "new_ideal_price": result["new_ideal_price"],
                "recommendation": "Invest in proper sorting and grading",
            })

        # Scenario 2: What if stored in cold storage?
        if features["is_cold_storage"] < 1.0:
            result = price_model.what_if(
                base_prediction,
                {"is_cold_storage": 1.0, "storage_type_code": 1.0, "storage_temp": 4.0},
                crop_name,
                features,
            )
            scenarios.append({
                "scenario": "If moved to cold storage (4°C)",
                "price_change": f"₹{result['price_change']:+.2f}/kg ({result['price_change_pct']:+.1f}%)",
                "new_ideal_price": result["new_ideal_price"],
                "recommendation": "Cold storage extends shelf life and preserves value",
            })

        # Scenario 3: What if temperature rises?
        temp = current_temp if current_temp is not None else features.get("storage_temp", 25.0)
        result = price_model.what_if(
            base_prediction,
            {"storage_temp": temp + 5.0, "spoilage_risk_code": min(features["spoilage_risk_code"] + 0.33, 1.0)},
            crop_name,
            features,
        )
        scenarios.append({
            "scenario": f"If storage temperature rises by 5°C (to {temp + 5:.0f}°C)",
            "price_change": f"₹{result['price_change']:+.2f}/kg ({result['price_change_pct']:+.1f}%)",
            "new_ideal_price": result["new_ideal_price"],
            "recommendation": "Maintain cool storage to prevent value loss",
        })

        return scenarios

    def get_feature_importance(self) -> Dict[str, float]:
        """Expose model feature importances for the dashboard."""
        return price_model.get_feature_importance()


# Singleton
pricing_service = PricingService()
