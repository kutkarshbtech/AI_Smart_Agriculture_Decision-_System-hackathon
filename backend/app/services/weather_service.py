"""
Weather integration service.
Adapted from Kisan.AI's OpenWeatherMap integration, extended for spoilage context.
Includes 5-day weather forecast for crop health price forecasting.
"""
import hashlib
import time
import httpx
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from app.core.config import settings


# ── Forecast cache (city/coords → data, TTL 1 hour) ──────────
_forecast_cache: Dict[str, Any] = {}
FORECAST_CACHE_TTL = 3600  # 1 hour


class WeatherService:
    """Fetches weather data and provides agricultural context."""

    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = settings.WEATHER_API_BASE_URL

    async def get_current_weather(
        self, lat: float, lng: float
    ) -> Dict[str, Any]:
        """Get current weather for a location (coordinates)."""
        if not self.api_key:
            return self._get_fallback_weather()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": lat,
                        "lon": lng,
                        "appid": self.api_key,
                        "units": "metric",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "rainfall_1h": data.get("rain", {}).get("1h", 0),
                    "city": data.get("name", "Unknown"),
                    "source": "openweathermap",
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_fallback_weather()

    async def get_weather_by_city(self, city: str) -> Dict[str, Any]:
        """Get weather data by city name."""
        if not self.api_key:
            return self._get_fallback_weather(city)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": "metric",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "rainfall_1h": data.get("rain", {}).get("1h", 0),
                    "city": data.get("name", city),
                    "source": "openweathermap",
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_fallback_weather(city)

    # ── Weather Forecast (5-day / 3-hour from OWM free tier) ────

    async def get_weather_forecast(
        self,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily weather forecast for up to 5 days.

        Uses OpenWeatherMap 5-day/3-hour forecast API (free tier),
        aggregated to daily summaries (avg temp, max temp, total rain,
        avg humidity, dominant condition).

        Returns a list of daily forecasts sorted by date.
        """
        cache_key = f"forecast|{city or ''}|{lat or ''}|{lng or ''}"
        cached = _forecast_cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < FORECAST_CACHE_TTL:
            return cached["data"]

        if not self.api_key:
            return self._get_fallback_forecast()

        params: Dict[str, Any] = {
            "appid": self.api_key,
            "units": "metric",
            "cnt": 40,  # max 5 days × 8 slots
        }
        if lat is not None and lng is not None:
            params["lat"] = lat
            params["lon"] = lng
        elif city:
            params["q"] = city
        else:
            return self._get_fallback_forecast()

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{self.base_url}/forecast", params=params)
                resp.raise_for_status()
                data = resp.json()

            daily = self._aggregate_forecast(data.get("list", []))
            city_name = data.get("city", {}).get("name", city or "Unknown")
            for d in daily:
                d["city"] = city_name
                d["source"] = "openweathermap"

            _forecast_cache[cache_key] = {"data": daily, "ts": time.time()}
            return daily

        except Exception as e:
            print(f"Weather forecast API error: {e}")
            return self._get_fallback_forecast()

    def _aggregate_forecast(
        self, slots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate 3-hour slots into daily weather summaries."""
        from collections import defaultdict

        by_date: Dict[str, list] = defaultdict(list)
        for slot in slots:
            dt_txt = slot.get("dt_txt", "")
            day_str = dt_txt[:10]  # "YYYY-MM-DD"
            if day_str:
                by_date[day_str].append(slot)

        daily: List[Dict[str, Any]] = []
        for day_str in sorted(by_date.keys()):
            items = by_date[day_str]
            temps = [s["main"]["temp"] for s in items]
            humidities = [s["main"]["humidity"] for s in items]
            wind_speeds = [s.get("wind", {}).get("speed", 0) for s in items]
            rain_total = sum(s.get("rain", {}).get("3h", 0) for s in items)

            # Dominant weather condition
            conditions = [s["weather"][0]["main"] for s in items if s.get("weather")]
            dominant = max(set(conditions), key=conditions.count) if conditions else "Clear"
            descriptions = [s["weather"][0]["description"] for s in items if s.get("weather")]
            dominant_desc = max(set(descriptions), key=descriptions.count) if descriptions else "clear sky"

            daily.append({
                "date": day_str,
                "temp_avg": round(sum(temps) / len(temps), 1),
                "temp_min": round(min(temps), 1),
                "temp_max": round(max(temps), 1),
                "humidity_avg": round(sum(humidities) / len(humidities), 0),
                "wind_speed_avg": round(sum(wind_speeds) / len(wind_speeds), 1),
                "rainfall_mm": round(rain_total, 1),
                "condition": dominant,
                "description": dominant_desc,
            })

        return daily

    def _get_fallback_forecast(self) -> List[Dict[str, Any]]:
        """Fallback forecast when API key is missing — seasonal estimates."""
        from datetime import timedelta
        today = date.today()
        month = today.month
        # Seasonal baseline for central India
        if month in (3, 4, 5):  # summer
            base_temp, base_hum = 38, 35
        elif month in (6, 7, 8, 9):  # monsoon
            base_temp, base_hum = 30, 80
        elif month in (10, 11):  # post-monsoon
            base_temp, base_hum = 28, 55
        else:  # winter
            base_temp, base_hum = 22, 50

        forecasts = []
        for i in range(5):
            d = today + timedelta(days=i)
            forecasts.append({
                "date": d.isoformat(),
                "temp_avg": base_temp + (i % 3 - 1),
                "temp_min": base_temp - 4,
                "temp_max": base_temp + 4,
                "humidity_avg": base_hum,
                "wind_speed_avg": 3.0,
                "rainfall_mm": 0.0 if month not in (6, 7, 8, 9) else 8.0,
                "condition": "Clear" if month not in (6, 7, 8, 9) else "Rain",
                "description": "seasonal estimate",
                "city": "Unknown",
                "source": "fallback_estimate",
            })
        return forecasts

    def get_spoilage_weather_context(
        self, weather: Dict[str, Any], crop_name: str
    ) -> Dict[str, Any]:
        """
        Analyze weather conditions for spoilage impact.
        High heat + humidity = faster spoilage for most crops.
        """
        temp = weather.get("temperature", 30)
        humidity = weather.get("humidity", 60)
        rainfall = weather.get("rainfall_1h", 0)

        risk_factors = []
        overall_impact = "neutral"

        # Temperature analysis
        if temp > 35:
            risk_factors.append({
                "factor": "Extreme heat",
                "value": f"{temp}°C",
                "impact": "Accelerates spoilage significantly. Use cold storage urgently.",
                "severity": "high",
            })
            overall_impact = "negative"
        elif temp > 28:
            risk_factors.append({
                "factor": "High temperature",
                "value": f"{temp}°C",
                "impact": "Above optimal for most produce. Consider covered/cooled storage.",
                "severity": "medium",
            })
            overall_impact = "negative"

        # Humidity analysis
        if humidity > 85:
            risk_factors.append({
                "factor": "High humidity",
                "value": f"{humidity}%",
                "impact": "Promotes fungal growth and mold. Ensure ventilation.",
                "severity": "medium",
            })
        elif humidity < 40:
            risk_factors.append({
                "factor": "Low humidity",
                "value": f"{humidity}%",
                "impact": "May cause dehydration and weight loss of produce.",
                "severity": "low",
            })

        # Rainfall
        if rainfall > 5:
            risk_factors.append({
                "factor": "Heavy rainfall",
                "value": f"{rainfall} mm/h",
                "impact": "Transport delays likely. Road conditions may affect logistics.",
                "severity": "medium",
            })

        return {
            "weather": weather,
            "overall_impact": overall_impact,
            "risk_factors": risk_factors,
            "advisory": self._generate_advisory(temp, humidity, rainfall, crop_name),
        }

    def _generate_advisory(
        self, temp: float, humidity: float, rainfall: float, crop_name: str
    ) -> str:
        """Generate a farmer-friendly weather advisory."""
        parts = []

        if temp > 35:
            parts.append(
                f"Today's temperature ({temp}°C) is very high. "
                f"Store your {crop_name} in the coolest available place or move to cold storage immediately."
            )
        elif temp > 28:
            parts.append(
                f"Temperature is {temp}°C — above ideal for {crop_name} storage. "
                "Keep produce in shade with good air flow."
            )
        else:
            parts.append(f"Temperature ({temp}°C) is manageable for {crop_name} storage.")

        if rainfall > 2:
            parts.append(
                "Rain expected — plan transport accordingly and protect produce from moisture."
            )

        return " ".join(parts)

    def _get_fallback_weather(self, city: str = "Unknown") -> Dict[str, Any]:
        """Fallback weather data for demo when API key is missing."""
        return {
            "temperature": 32.0,
            "humidity": 65,
            "pressure": 1013,
            "description": "partly cloudy",
            "wind_speed": 3.5,
            "rainfall_1h": 0,
            "city": city,
            "source": "fallback_estimate",
        }


# Singleton
weather_service = WeatherService()
