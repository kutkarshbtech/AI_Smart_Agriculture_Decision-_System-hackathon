"""
Spoilage prediction service.
Uses ML model + heuristics to predict spoilage risk and remaining shelf life.
"""
import math
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

# Crop shelf-life data (embedded for hackathon - later move to DB/Neptune)
CROP_SHELF_LIFE = {
    "tomato": {"ambient_days": 7, "cold_days": 21, "optimal_temp": (10, 15), "optimal_humidity": (85, 95)},
    "potato": {"ambient_days": 30, "cold_days": 120, "optimal_temp": (4, 8), "optimal_humidity": (90, 95)},
    "onion": {"ambient_days": 30, "cold_days": 180, "optimal_temp": (0, 4), "optimal_humidity": (65, 70)},
    "banana": {"ambient_days": 5, "cold_days": 14, "optimal_temp": (13, 15), "optimal_humidity": (85, 95)},
    "mango": {"ambient_days": 5, "cold_days": 21, "optimal_temp": (10, 13), "optimal_humidity": (85, 90)},
    "apple": {"ambient_days": 14, "cold_days": 120, "optimal_temp": (0, 4), "optimal_humidity": (90, 95)},
    "rice": {"ambient_days": 365, "cold_days": 730, "optimal_temp": (15, 20), "optimal_humidity": (60, 70)},
    "wheat": {"ambient_days": 180, "cold_days": 365, "optimal_temp": (15, 20), "optimal_humidity": (60, 65)},
    "cauliflower": {"ambient_days": 4, "cold_days": 21, "optimal_temp": (0, 2), "optimal_humidity": (95, 98)},
    "spinach": {"ambient_days": 2, "cold_days": 10, "optimal_temp": (0, 2), "optimal_humidity": (95, 100)},
    "okra": {"ambient_days": 3, "cold_days": 10, "optimal_temp": (7, 10), "optimal_humidity": (90, 95)},
    "brinjal": {"ambient_days": 5, "cold_days": 14, "optimal_temp": (10, 12), "optimal_humidity": (90, 95)},
    "grape": {"ambient_days": 3, "cold_days": 42, "optimal_temp": (-1, 0), "optimal_humidity": (90, 95)},
    "guava": {"ambient_days": 5, "cold_days": 21, "optimal_temp": (8, 10), "optimal_humidity": (85, 95)},
    "carrot": {"ambient_days": 7, "cold_days": 120, "optimal_temp": (0, 2), "optimal_humidity": (95, 100)},
    "capsicum": {"ambient_days": 5, "cold_days": 21, "optimal_temp": (7, 10), "optimal_humidity": (90, 95)},
}

DEFAULT_SHELF_LIFE = {"ambient_days": 7, "cold_days": 21, "optimal_temp": (5, 15), "optimal_humidity": (80, 95)}


class SpoilageService:
    """Predicts spoilage risk based on crop type, storage conditions, and time."""

    def get_crop_data(self, crop_name: str) -> Dict[str, Any]:
        """Get shelf-life data for a crop (case-insensitive)."""
        return CROP_SHELF_LIFE.get(crop_name.lower(), DEFAULT_SHELF_LIFE)

    def calculate_temperature_factor(
        self, current_temp: float, optimal_min: float, optimal_max: float
    ) -> float:
        """
        Returns a degradation multiplier based on how far temp is from optimal.
        1.0 = optimal, >1 = faster spoilage, value can go up to ~3.0.
        """
        if optimal_min <= current_temp <= optimal_max:
            return 1.0

        # Every 10°C above optimal roughly doubles spoilage rate (Q10 rule)
        if current_temp > optimal_max:
            delta = current_temp - optimal_max
            return min(2 ** (delta / 10), 5.0)

        # Below optimal but not freezing — slower degradation
        if current_temp < optimal_min and current_temp >= 0:
            delta = optimal_min - current_temp
            return 1.0 + (delta * 0.05)  # slight increase due to chilling injury

        # Freezing damage
        if current_temp < 0:
            return 3.0

        return 1.0

    def calculate_humidity_factor(
        self, current_humidity: float, optimal_min: float, optimal_max: float
    ) -> float:
        """Returns a degradation factor for humidity deviation."""
        if optimal_min <= current_humidity <= optimal_max:
            return 1.0

        if current_humidity < optimal_min:
            # Too dry — moisture loss, wilting
            delta = optimal_min - current_humidity
            return 1.0 + (delta * 0.02)

        if current_humidity > optimal_max:
            # Too humid — mold growth
            delta = current_humidity - optimal_max
            return 1.0 + (delta * 0.03)

        return 1.0

    def predict_spoilage(
        self,
        crop_name: str,
        harvest_date: date,
        storage_type: str = "ambient",
        current_temp: Optional[float] = None,
        current_humidity: Optional[float] = None,
        transport_hours: float = 0,
    ) -> Dict[str, Any]:
        """
        Core spoilage prediction engine.

        Returns:
            Dict with risk level, probability, shelf life, factors, recommendations.
        """
        crop_data = self.get_crop_data(crop_name)

        # Base shelf life
        if storage_type == "cold":
            base_shelf_life = crop_data["cold_days"]
        else:
            base_shelf_life = crop_data["ambient_days"]

        optimal_temp = crop_data["optimal_temp"]
        optimal_humidity = crop_data["optimal_humidity"]

        # Calculate degradation factors
        factors = []
        total_degradation = 1.0

        # Temperature impact
        if current_temp is not None:
            temp_factor = self.calculate_temperature_factor(
                current_temp, optimal_temp[0], optimal_temp[1]
            )
            total_degradation *= temp_factor
            if temp_factor > 1.2:
                factors.append({
                    "factor": "temperature",
                    "current": current_temp,
                    "optimal_range": f"{optimal_temp[0]}–{optimal_temp[1]}°C",
                    "impact": f"Accelerates spoilage by {(temp_factor - 1) * 100:.0f}%",
                    "severity": "high" if temp_factor > 2.0 else "medium"
                })
        else:
            # Assume ambient temp of 30°C (Indian summer default)
            assumed_temp = 30.0 if storage_type == "ambient" else optimal_temp[0] + 2
            temp_factor = self.calculate_temperature_factor(
                assumed_temp, optimal_temp[0], optimal_temp[1]
            )
            total_degradation *= temp_factor

        # Humidity impact
        if current_humidity is not None:
            humidity_factor = self.calculate_humidity_factor(
                current_humidity, optimal_humidity[0], optimal_humidity[1]
            )
            total_degradation *= humidity_factor
            if humidity_factor > 1.1:
                factors.append({
                    "factor": "humidity",
                    "current": current_humidity,
                    "optimal_range": f"{optimal_humidity[0]}–{optimal_humidity[1]}%",
                    "impact": f"Increases degradation by {(humidity_factor - 1) * 100:.0f}%",
                    "severity": "medium"
                })

        # Transport damage factor
        if transport_hours > 0:
            transport_factor = 1.0 + (transport_hours * 0.02)  # 2% per hour
            total_degradation *= transport_factor
            if transport_hours > 4:
                factors.append({
                    "factor": "transport_time",
                    "hours": transport_hours,
                    "impact": f"Transit adds {(transport_factor - 1) * 100:.0f}% spoilage risk",
                    "severity": "medium" if transport_hours < 12 else "high"
                })

        # Adjusted shelf life
        adjusted_shelf_life = max(1, int(base_shelf_life / total_degradation))

        # Days elapsed since harvest
        days_elapsed = (date.today() - harvest_date).days
        remaining_days = max(0, adjusted_shelf_life - days_elapsed)

        # Spoilage probability (sigmoid curve)
        progress_ratio = days_elapsed / max(adjusted_shelf_life, 1)
        spoilage_probability = 1 / (1 + math.exp(-8 * (progress_ratio - 0.6)))
        spoilage_probability = round(min(max(spoilage_probability, 0.01), 0.99), 3)

        # Risk classification
        if spoilage_probability < 0.2:
            risk_level = "low"
        elif spoilage_probability < 0.5:
            risk_level = "medium"
        elif spoilage_probability < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, storage_type, current_temp, optimal_temp,
            remaining_days, crop_name
        )

        # Causal explanation
        explanation = self._generate_explanation(
            crop_name, risk_level, days_elapsed, adjusted_shelf_life,
            current_temp, optimal_temp, factors
        )

        return {
            "spoilage_risk": risk_level,
            "spoilage_probability": spoilage_probability,
            "estimated_shelf_life_days": adjusted_shelf_life,
            "remaining_shelf_life_days": remaining_days,
            "risk_factors": factors,
            "recommendations": recommendations,
            "explanation": explanation,
        }

    def _generate_recommendations(
        self, risk_level: str, storage_type: str,
        current_temp: Optional[float], optimal_temp: tuple,
        remaining_days: int, crop_name: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        if risk_level in ("high", "critical"):
            recs.append("⚠️ Sell immediately to avoid losses")
            recs.append("Consider selling at nearby local market today")

        if storage_type == "ambient" and risk_level in ("medium", "high"):
            recs.append(f"Move to cold storage ({optimal_temp[0]}–{optimal_temp[1]}°C) to extend shelf life")

        if current_temp and current_temp > optimal_temp[1] + 5:
            recs.append(f"Reduce storage temperature — current {current_temp}°C is too high for {crop_name}")

        if remaining_days <= 2 and risk_level != "low":
            recs.append("Only 1-2 days of usable life remaining — prioritize quick sale")

        if risk_level == "low":
            recs.append("Produce is in good condition — you can wait for better prices")
            if remaining_days > 7:
                recs.append("Consider bulk sale to maximize returns")

        return recs

    def _generate_explanation(
        self, crop_name: str, risk_level: str, days_elapsed: int,
        shelf_life: int, current_temp: Optional[float],
        optimal_temp: tuple, factors: List[Dict]
    ) -> str:
        """Generate a causal explanation for the spoilage assessment."""
        parts = [f"Your {crop_name} batch was harvested {days_elapsed} day(s) ago."]
        parts.append(f"Estimated shelf life: {shelf_life} days under current conditions.")

        if current_temp and current_temp > optimal_temp[1]:
            delta = current_temp - optimal_temp[1]
            reduction = int((1 - 1 / (2 ** (delta / 10))) * 100)
            parts.append(
                f"Storage temperature ({current_temp}°C) is {delta:.0f}°C above optimal "
                f"({optimal_temp[0]}–{optimal_temp[1]}°C), reducing shelf life by ~{reduction}%."
            )

        for f in factors:
            if f["factor"] == "transport_time":
                parts.append(f"Transit time of {f['hours']}h contributes to quality degradation.")

        if risk_level == "critical":
            parts.append("URGENT: Produce is at critical risk of spoilage. Sell today.")
        elif risk_level == "high":
            parts.append("Sell within 1-2 days to prevent losses.")
        elif risk_level == "medium":
            parts.append("Monitor closely and plan sale within the week.")

        return " ".join(parts)


# Singleton
spoilage_service = SpoilageService()
