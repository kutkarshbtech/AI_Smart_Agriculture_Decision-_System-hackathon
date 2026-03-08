"""
Logistics recommendation service.
Recommends optimal transport solutions based on distance, crop type, and quantity.
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# Vehicle types with capacity and cost specifications
VEHICLE_TYPES = {
    "two_wheeler": {
        "name": "Two Wheeler (Bike/Scooter)",
        "icon": "&#127949;",
        "max_capacity_kg": 30,
        "cost_per_km": 5,
        "fixed_cost": 50,
        "avg_speed_kmph": 40,
        "suitable_for": ["small quantities", "urban delivery", "quick transport"],
        "crops_suited": ["vegetables", "fruits"],
    },
    "auto_rickshaw": {
        "name": "Auto Rickshaw",
        "icon": "&#128763;",
        "max_capacity_kg": 150,
        "cost_per_km": 8,
        "fixed_cost": 100,
        "avg_speed_kmph": 35,
        "suitable_for": ["small to medium loads", "local delivery"],
        "crops_suited": ["vegetables", "fruits"],
    },
    "pickup_van": {
        "name": "Pickup Van / Chota Hathi",
        "icon": "&#128666;",
        "max_capacity_kg": 500,
        "cost_per_km": 12,
        "fixed_cost": 200,
        "avg_speed_kmph": 50,
        "suitable_for": ["medium loads", "inter-city transport"],
        "crops_suited": ["vegetables", "fruits", "grains"],
    },
    "mini_truck": {
        "name": "Mini Truck (Tata Ace)",
        "icon": "&#128667;",
        "max_capacity_kg": 1000,
        "cost_per_km": 18,
        "fixed_cost": 350,
        "avg_speed_kmph": 60,
        "suitable_for": ["medium to large loads", "regional transport"],
        "crops_suited": ["all crops"],
    },
    "truck_6_wheeler": {
        "name": "6-Wheeler Truck",
        "icon": "&#128666;",
        "max_capacity_kg": 3000,
        "cost_per_km": 25,
        "fixed_cost": 500,
        "avg_speed_kmph": 55,
        "suitable_for": ["large loads", "long distance"],
        "crops_suited": ["all crops", "bulk transport"],
    },
    "truck_10_wheeler": {
        "name": "10-Wheeler Truck",
        "icon": "&#128666;",
        "max_capacity_kg": 8000,
        "cost_per_km": 35,
        "fixed_cost": 800,
        "avg_speed_kmph": 50,
        "suitable_for": ["very large loads", "inter-state transport"],
        "crops_suited": ["all crops", "bulk wholesale"],
    },
    "refrigerated_truck": {
        "name": "Refrigerated Truck (Cold Chain)",
        "icon": "&#129523;",
        "max_capacity_kg": 2000,
        "cost_per_km": 45,
        "fixed_cost": 1000,
        "avg_speed_kmph": 55,
        "suitable_for": ["perishable goods", "long distance cold chain"],
        "crops_suited": ["fruits", "vegetables", "dairy"],
    },
}

# Demo logistics providers
LOGISTICS_PROVIDERS = [
    {
        "id": 1,
        "name": "Porter",
        "type": "On-demand",
        "rating": 4.3,
        "vehicles": ["two_wheeler", "auto_rickshaw", "pickup_van", "mini_truck"],
        "operating_states": ["Maharashtra", "Karnataka", "Delhi", "Gujarat", "Tamil Nadu"],
        "phone": "+91-9876543210",
        "features": ["Real-time tracking", "Instant booking", "Digital payment"],
    },
    {
        "id": 2,
        "name": "LetsTransport",
        "type": "On-demand",
        "rating": 4.1,
        "vehicles": ["pickup_van", "mini_truck", "truck_6_wheeler"],
        "operating_states": ["All India"],
        "phone": "+91-9876543211",
        "features": ["24/7 support", "Verified drivers", "Insurance covered"],
    },
    {
        "id": 3,
        "name": "VRL Logistics",
        "type": "Traditional",
        "rating": 4.5,
        "vehicles": ["truck_6_wheeler", "truck_10_wheeler"],
        "operating_states": ["All India"],
        "phone": "+91-9876543212",
        "features": ["Nationwide network", "30+ years experience", "Door delivery"],
    },
    {
        "id": 4,
        "name": "Rivigo",
        "type": "Tech-enabled",
        "rating": 4.4,
        "vehicles": ["truck_6_wheeler", "truck_10_wheeler", "refrigerated_truck"],
        "operating_states": ["All India"],
        "phone": "+91-9876543213",
        "features": ["Relay-based driving", "GPS tracking", "Cold chain available"],
    },
    {
        "id": 5,
        "name": "Kisan Transport",
        "type": "Agriculture-focused",
        "rating": 4.2,
        "vehicles": ["pickup_van", "mini_truck", "truck_6_wheeler", "refrigerated_truck"],
        "operating_states": ["Punjab", "Haryana", "Uttar Pradesh", "Madhya Pradesh"],
        "phone": "+91-9876543214",
        "features": ["Farm-friendly", "Mandi expertise", "Fresh produce handling"],
    },
    {
        "id": 6,
        "name": "TruckSuvidha",
        "type": "Marketplace",
        "rating": 4.0,
        "vehicles": ["mini_truck", "truck_6_wheeler", "truck_10_wheeler"],
        "operating_states": ["All India"],
        "phone": "+91-9876543215",
        "features": ["Multiple quotes", "Choose your driver", "Competitive rates"],
    },
]

# Perishability index for crops (0 = highly perishable, 1 = less perishable)
CROP_PERISHABILITY = {
    "tomato": 0.2,
    "banana": 0.3,
    "mango": 0.3,
    "apple": 0.5,
    "potato": 0.7,
    "onion": 0.8,
    "rice": 0.95,
    "wheat": 0.95,
    "carrot": 0.4,
    "capsicum": 0.3,
    "cucumber": 0.2,
    "spinach": 0.1,
    "cauliflower": 0.3,
}


class LogisticsService:
    """
    Logistics recommendation engine for farm-to-market transportation.
    """

    def recommend_vehicle(
        self,
        distance_km: float,
        quantity_kg: float,
        crop_name: str,
        urgency: str = "medium",  # "low", "medium", "high"
    ) -> Dict[str, Any]:
        """
        Recommend the best vehicle type based on distance, quantity, and crop.
        
        Returns:
            - Primary recommendation
            - Alternative options
            - Estimated cost and time
        """
        crop_perishability = CROP_PERISHABILITY.get(crop_name.lower(), 0.5)
        
        # Filter vehicles by capacity
        suitable_vehicles = {}
        for vehicle_id, vehicle in VEHICLE_TYPES.items():
            if vehicle["max_capacity_kg"] >= quantity_kg:
                suitable_vehicles[vehicle_id] = vehicle
        
        if not suitable_vehicles:
            # Need multiple trips or largest vehicle
            suitable_vehicles = {"truck_10_wheeler": VEHICLE_TYPES["truck_10_wheeler"]}
        
        # Score each vehicle
        scored_vehicles = []
        for vehicle_id, vehicle in suitable_vehicles.items():
            cost = self._calculate_cost(distance_km, vehicle)
            time_hours = distance_km / vehicle["avg_speed_kmph"]
            
            # Scoring factors
            cost_score = 1.0 / (cost / 100 + 1)  # Lower cost = higher score
            capacity_efficiency = min(quantity_kg / vehicle["max_capacity_kg"], 1.0)
            
            # Perishability urgency
            if crop_perishability < 0.3 and time_hours > 6:
                # Highly perishable crop, long distance
                if vehicle_id == "refrigerated_truck":
                    perishability_score = 1.0
                else:
                    perishability_score = 0.3
            else:
                perishability_score = 0.8
            
            # Urgency factor
            urgency_map = {"low": 0.6, "medium": 0.8, "high": 1.0}
            urgency_factor = urgency_map.get(urgency, 0.8)
            
            # Distance suitability — realistic operating ranges
            if distance_km < 10:
                # Very short: two-wheelers and autos ideal
                distance_score = 1.0 if vehicle_id in ["two_wheeler", "auto_rickshaw"] else 0.7
            elif distance_km < 30:
                # Short urban: autos OK, pickup vans good
                if vehicle_id == "two_wheeler":
                    distance_score = 0.6
                elif vehicle_id == "auto_rickshaw":
                    distance_score = 0.8
                elif vehicle_id in ["pickup_van", "mini_truck"]:
                    distance_score = 1.0
                else:
                    distance_score = 0.7
            elif distance_km < 100:
                # Medium inter-city: pickup vans and mini trucks ideal
                if vehicle_id in ["two_wheeler", "auto_rickshaw"]:
                    distance_score = 0.15  # very impractical
                elif vehicle_id in ["pickup_van", "mini_truck"]:
                    distance_score = 1.0
                else:
                    distance_score = 0.8
            elif distance_km < 300:
                # Long inter-city: trucks ideal
                if vehicle_id in ["two_wheeler", "auto_rickshaw"]:
                    distance_score = 0.05  # essentially impossible
                elif vehicle_id == "pickup_van":
                    distance_score = 0.8
                elif "truck" in vehicle_id:
                    distance_score = 1.0
                else:
                    distance_score = 0.6
            else:
                # Very long distance (300+ km): only trucks
                if vehicle_id in ["two_wheeler", "auto_rickshaw"]:
                    distance_score = 0.0  # not feasible
                elif vehicle_id == "pickup_van":
                    distance_score = 0.6
                elif "truck" in vehicle_id:
                    distance_score = 1.0
                else:
                    distance_score = 0.4
            
            composite_score = (
                cost_score * 0.2
                + capacity_efficiency * 0.2
                + perishability_score * 0.2
                + distance_score * 0.3
                + urgency_factor * 0.1
            )
            
            scored_vehicles.append({
                "vehicle_id": vehicle_id,
                "vehicle": vehicle,
                "score": composite_score,
                "cost": cost,
                "time_hours": time_hours,
                "capacity_utilization": min(quantity_kg / vehicle["max_capacity_kg"] * 100, 100),
            })
        
        # Sort by score
        scored_vehicles.sort(key=lambda x: x["score"], reverse=True)
        
        primary = scored_vehicles[0]
        alternatives = scored_vehicles[1:3] if len(scored_vehicles) > 1 else []
        
        return {
            "primary_recommendation": {
                "vehicle_type": primary["vehicle_id"],
                "vehicle_name": primary["vehicle"]["name"],
                "icon": primary["vehicle"]["icon"],
                "estimated_cost": round(primary["cost"], 0),
                "estimated_time_hours": round(primary["time_hours"], 1),
                "capacity_utilization": round(primary["capacity_utilization"], 0),
                "score": round(primary["score"] * 100, 1),
                "reasons": self._generate_reasons(primary, crop_name, distance_km, quantity_kg),
            },
            "alternatives": [
                {
                    "vehicle_type": alt["vehicle_id"],
                    "vehicle_name": alt["vehicle"]["name"],
                    "icon": alt["vehicle"]["icon"],
                    "estimated_cost": round(alt["cost"], 0),
                    "estimated_time_hours": round(alt["time_hours"], 1),
                    "capacity_utilization": round(alt["capacity_utilization"], 0),
                }
                for alt in alternatives
            ],
            "distance_km": distance_km,
            "quantity_kg": quantity_kg,
            "crop_name": crop_name,
        }
    
    def _calculate_cost(self, distance_km: float, vehicle: Dict[str, Any]) -> float:
        """Calculate total transport cost."""
        variable_cost = distance_km * vehicle["cost_per_km"]
        total = vehicle["fixed_cost"] + variable_cost
        return total
    
    def _generate_reasons(
        self,
        recommendation: Dict[str, Any],
        crop_name: str,
        distance_km: float,
        quantity_kg: float,
    ) -> List[str]:
        """Generate human-readable reasons for the recommendation."""
        reasons = []
        vehicle = recommendation["vehicle"]
        
        if recommendation["capacity_utilization"] > 80:
            reasons.append("Optimal capacity utilization")
        elif recommendation["capacity_utilization"] < 50:
            reasons.append("Room for additional cargo")
        
        if distance_km < 20:
            reasons.append("Best for short-distance local delivery")
        elif distance_km < 100:
            reasons.append("Suitable for regional transport")
        else:
            reasons.append("Designed for long-distance haul")
        
        perishability = CROP_PERISHABILITY.get(crop_name.lower(), 0.5)
        if perishability < 0.3 and vehicle["name"].startswith("Refrigerated"):
            reasons.append("Cold chain preserves freshness")
        elif perishability < 0.3:
            reasons.append("Fast delivery recommended for perishable produce")
        
        if quantity_kg <= vehicle["max_capacity_kg"] * 0.5:
            reasons.append("Single-trip transport")
        
        return reasons
    
    def find_logistics_providers(
        self,
        vehicle_type: str,
        source_state: str,
        destination_state: str,
        min_rating: float = 3.5,
    ) -> List[Dict[str, Any]]:
        """
        Find logistics providers that offer the required vehicle type
        and operate in the source/destination states.
        """
        matches = []
        
        for provider in LOGISTICS_PROVIDERS:
            # Check vehicle availability
            if vehicle_type not in provider["vehicles"]:
                continue
            
            # Check rating
            if provider["rating"] < min_rating:
                continue
            
            # Check state coverage
            if "All India" in provider["operating_states"]:
                operates_source = True
                operates_dest = True
            else:
                operates_source = source_state in provider["operating_states"]
                operates_dest = destination_state in provider["operating_states"]
            
            if not (operates_source or operates_dest or "All India" in provider["operating_states"]):
                continue
            
            matches.append({
                "provider_id": provider["id"],
                "name": provider["name"],
                "type": provider["type"],
                "rating": provider["rating"],
                "phone": provider["phone"],
                "features": provider["features"],
                "coverage": provider["operating_states"],
            })
        
        # Sort by rating
        matches.sort(key=lambda x: x["rating"], reverse=True)
        
        return matches
    
    def get_complete_logistics_recommendation(
        self,
        seller_location: str,
        buyer_location: str,
        distance_km: float,
        quantity_kg: float,
        crop_name: str,
        urgency: str = "medium",
    ) -> Dict[str, Any]:
        """
        Complete logistics recommendation including vehicle and providers.
        """
        # Extract states from location strings
        seller_state = seller_location.split(",")[-1].strip() if "," in seller_location else seller_location
        buyer_state = buyer_location.split(",")[-1].strip() if "," in buyer_location else buyer_location
        
        # Get vehicle recommendation
        vehicle_rec = self.recommend_vehicle(distance_km, quantity_kg, crop_name, urgency)
        
        # Get logistics providers
        primary_vehicle = vehicle_rec["primary_recommendation"]["vehicle_type"]
        providers = self.find_logistics_providers(
            primary_vehicle,
            seller_state,
            buyer_state,
            min_rating=3.5,
        )
        
        # Calculate delivery timeline
        est_time_hours = vehicle_rec["primary_recommendation"]["estimated_time_hours"]
        loading_time = 1.0  # hours
        unloading_time = 0.5  # hours
        total_time = est_time_hours + loading_time + unloading_time
        
        # Estimated delivery date
        now = datetime.now()
        delivery_date = now + timedelta(hours=total_time)
        
        return {
            "vehicle_recommendation": vehicle_rec,
            "logistics_providers": providers[:3],  # Top 3
            "route_info": {
                "source": seller_location,
                "destination": buyer_location,
                "distance_km": distance_km,
                "estimated_travel_time_hours": round(est_time_hours, 1),
                "estimated_total_time_hours": round(total_time, 1),
                "estimated_delivery": delivery_date.strftime("%d %b %Y, %I:%M %p"),
            },
            "cost_breakdown": {
                "transport_cost": vehicle_rec["primary_recommendation"]["estimated_cost"],
                "loading_charges": 100 if quantity_kg > 100 else 50,
                "toll_estimated": round(distance_km * 0.5, 0) if distance_km > 50 else 0,
                "total_estimated": round(
                    vehicle_rec["primary_recommendation"]["estimated_cost"]
                    + (100 if quantity_kg > 100 else 50)
                    + (distance_km * 0.5 if distance_km > 50 else 0),
                    0
                ),
            },
        }


# Singleton instance
logistics_service = LogisticsService()
