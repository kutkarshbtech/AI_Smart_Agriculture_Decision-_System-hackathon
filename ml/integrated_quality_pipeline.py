"""
Integrated Quality & Spoilage Prediction Pipeline

Combines:
1. Enhanced Freshness Detection (Computer Vision)
2. Spoilage Risk Prediction (ML + Heuristics)  
3. Unified recommendations for farmers

This is the refinement that integrates the two separate modules.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Any, Optional

# Add paths
freshness_path = Path(__file__).parent / "freshness_detection"
spoilage_path = Path(__file__).parent / "spoilage_prediction"
sys.path.insert(0, str(freshness_path))
sys.path.insert(0, str(spoilage_path))


class IntegratedQualityPipeline:
    """
    Unified pipeline combining freshness detection and spoilage prediction.
    
    Flow:
    Image → Enhanced Freshness Detector
         → Current Quality State
         + Storage Conditions
         → Spoilage Predictor
         → Future Shelf Life & Recommendations
    """
    
    def __init__(
        self,
        freshness_model_dir: str = "ml/freshness_detection/models",
        spoilage_model_dir: str = "ml/spoilage_prediction/models",
        enable_ml_spoilage: bool = False,  # Use ML model if available
    ):
        """Initialize integrated pipeline."""
        
        # Initialize enhanced freshness detector
        try:
            from enhanced_inference import create_enhanced_detector
            self.freshness_detector = create_enhanced_detector(
                model_dir=freshness_model_dir,
                enable_damage_assessment=True
            )
            print("✓ Enhanced Freshness Detector loaded")
        except Exception as e:
            print(f"⚠ Could not load enhanced freshness detector: {e}")
            self.freshness_detector = None
        
        # Initialize spoilage predictor
        if enable_ml_spoilage:
            try:
                from inference import SpoilagePredictor
                self.spoilage_predictor = SpoilagePredictor(
                    model_dir=spoilage_model_dir,
                    use_bedrock=False  # Can enable for production
                )
                print("✓ ML Spoilage Predictor loaded")
            except Exception as e:
                print(f"⚠ Could not load ML spoilage predictor: {e}")
                print("  Falling back to heuristic-based prediction")
                self.spoilage_predictor = None
        else:
            self.spoilage_predictor = None
        
        # Load simplified spoilage heuristics
        from simplified_spoilage import SimplifiedSpoilagePredictor
        self.simple_spoilage = SimplifiedSpoilagePredictor()
        print("✓ Heuristic Spoilage Predictor loaded")
    
    def analyze(
        self,
        image_path: str,
        crop_name: Optional[str] = None,
        harvest_date: Optional[date] = None,
        storage_temp: Optional[float] = None,
        storage_humidity: Optional[float] = None,
        storage_type: str = "ambient",
        transport_hours: float = 0,
    ) -> Dict[str, Any]:
        """
        Full integrated analysis.
        
        Args:
            image_path: Path to produce image
            crop_name: Optional crop name (auto-detected if None)
            harvest_date: When harvested (default: 1 day ago)
            storage_temp: Current storage temperature (°C)
            storage_humidity: Current storage humidity (%)
            storage_type: "ambient" or "cold"
            transport_hours: Hours in transport
        
        Returns:
            Comprehensive analysis with current quality + future predictions
        """
        
        # Step 1: Freshness Detection
        print("\n🔬 Running freshness detection...")
        if self.freshness_detector:
            freshness_result = self.freshness_detector.predict(image_path, crop_name)
        else:
            # Fallback simulation
            freshness_result = self._simulate_freshness(crop_name or "tomato")
        
        # Extract key info
        detected_crop = freshness_result["crop_type"]
        current_quality_grade = freshness_result["freshness_grade"]
        quality_score = freshness_result["quality_score"]
        damage_level = freshness_result.get("damage_level", "minimal")
        
        print(f"  ✓ Detected: {detected_crop}")
        print(f"  ✓ Quality: {current_quality_grade} (Score: {quality_score})")
        print(f"  ✓ Damage: {damage_level}")
        
        # Step 2: Spoilage Prediction
        print("\n📊 Running spoilage prediction...")
        
        # Prepare inputs
        if harvest_date is None:
            # Estimate from quality grade
            days_old = self._estimate_days_from_grade(current_quality_grade)
            harvest_date = date.today() - timedelta(days=days_old)
        
        if storage_temp is None:
            storage_temp = 30.0 if storage_type == "ambient" else 10.0
        
        if storage_humidity is None:
            storage_humidity = 70.0 if storage_type == "ambient" else 85.0
        
        # Run spoilage prediction
        spoilage_result = self.simple_spoilage.predict(
            crop_name=detected_crop,
            harvest_date=harvest_date,
            storage_type=storage_type,
            current_temp=storage_temp,
            current_humidity=storage_humidity,
            transport_hours=transport_hours,
            current_quality_score=quality_score,  # Pass current state
        )
        
        print(f"  ✓ Spoilage Risk: {spoilage_result['spoilage_risk']}")
        print(f"  ✓ Remaining Shelf Life: {spoilage_result['remaining_shelf_life_days']} days")
        
        # Step 3: Generate Unified Recommendations
        print("\n💡 Generating unified recommendations...")
        unified_recs = self._generate_unified_recommendations(
            freshness_result, spoilage_result, detected_crop
        )
        
        # Step 4: Combine Results
        integrated_result = {
            # Current State (from freshness detection)
            "current_quality": {
                "crop": detected_crop,
                "freshness_grade": current_quality_grade,
                "quality_score": quality_score,
                "overall_grade": freshness_result["overall_grade"],
                "damage_level": damage_level,
                "damage_score": freshness_result["damage_score"],
                "ripeness_stage": freshness_result.get("ripeness_stage", "unknown"),
                "confidence": freshness_result["confidence"],
            },
            
            # Future Prediction (from spoilage model)
            "spoilage_prediction": {
                "risk_level": spoilage_result["spoilage_risk"],
                "probability": spoilage_result["spoilage_probability"],
                "remaining_days": spoilage_result["remaining_shelf_life_days"],
                "estimated_total_shelf_life": spoilage_result["estimated_shelf_life_days"],
                "risk_factors": spoilage_result.get("risk_factors", []),
            },
            
            # Storage Conditions
            "storage_conditions": {
                "type": storage_type,
                "temperature_c": storage_temp,
                "humidity_pct": storage_humidity,
                "days_since_harvest": (date.today() - harvest_date).days,
                "transport_hours": transport_hours,
            },
            
            # Unified Action Plan
            "action_plan": unified_recs,
            
            # Raw results for debugging
            "_raw_freshness": freshness_result,
            "_raw_spoilage": spoilage_result,
        }
        
        return integrated_result
    
    def _estimate_days_from_grade(self, grade: str) -> int:
        """Estimate how many days old based on quality grade."""
        grade_to_days = {
            "excellent": 1,
            "good": 2,
            "fair": 4,
            "poor": 6,
            "rotten": 8,
        }
        return grade_to_days.get(grade, 3)
    
    def _generate_unified_recommendations(
        self, freshness_result: Dict, spoilage_result: Dict, crop: str
    ) -> Dict[str, Any]:
        """Generate unified actionable recommendations."""
        
        grade = freshness_result["freshness_grade"]
        risk = spoilage_result["spoilage_risk"]
        remaining_days = spoilage_result["remaining_shelf_life_days"]
        damage_level = freshness_result.get("damage_level", "minimal")
        
        actions = []
        urgency = "moderate"
        sell_within_days = remaining_days
        price_strategy = "market_rate"
        
        # Decision logic
        if grade in ("excellent", "good") and risk == "low" and remaining_days >= 4:
            actions.append(f"✅ Quality is {grade}! You can hold for better prices.")
            actions.append(f"💰 Estimated sellable window: {remaining_days} days")
            actions.append("📈 Monitor market prices - consider waiting 1-2 days for premium")
            urgency = "low"
            price_strategy = "hold_for_premium"
            
        elif grade == "good" and risk == "medium":
            actions.append("⚠️ Good quality but shelf life is moderate")
            actions.append(f"🎯 Sell within {min(remaining_days, 3)} days for best returns")
            actions.append("🏪 Target local mandis for quick turnover")
            urgency = "moderate"
            sell_within_days = min(remaining_days, 3)
            price_strategy = "market_rate"
            
        elif grade == "fair" or risk in ("high", "critical"):
            actions.append("🔴 URGENT: Quality is declining")
            actions.append(f"⏰ Sell within {min(remaining_days, 2)} days to prevent loss")
            actions.append("💸 Accept slight discount for quick sale")
            urgency = "high"
            sell_within_days = min(remaining_days, 2)
            price_strategy = "quick_sale"
            
        elif grade == "poor" or risk == "critical":
            actions.append("🚨 CRITICAL: Sell immediately or process today")
            actions.append("⚡ Accept any reasonable offer to avoid total loss")
            actions.append("🏭 Consider processing into value-added products")
            urgency = "critical"
            sell_within_days = 1
            price_strategy = "distress_sale"
            
        else:  # rotten
            actions.append("❌ Quality unacceptable for sale")
            actions.append("🗑️ Discard to prevent contamination of good produce")
            urgency = "immediate"
            sell_within_days = 0
            price_strategy = "do_not_sell"
        
        # Storage advice
        storage_tips = spoilage_result.get("recommendations", [])
        
        # Add damage-specific advice
        if damage_level in ("moderate", "severe"):
            actions.append(f"⚠️ Damage detected: {damage_level} - sort batch and remove damaged items")
        
        # Hindi translation
        crop_hindi = {
            "tomato": "टमाटर", "banana": "केला", "mango": "आम",
            "apple": "सेब", "potato": "आलू", "onion": "प्याज",
            "carrot": "गाजर", "okra": "भिंडी",
        }.get(crop, crop)
        
        urgency_hindi = {
            "low": "जल्दी नहीं",
            "moderate": "सामान्य",
            "high": "ज़रूरी",
            "critical": "अत्यावश्यक",
            "immediate": "तुरंत",
        }.get(urgency, urgency)
        
        hindi_summary = f"आपका {crop_hindi} {grade} गुणवत्ता में है। "
        
        if urgency in ("low", "moderate"):
            hindi_summary += f"{remaining_days} दिन में बेचें।"
        else:
            hindi_summary += "तुरंत बेच दें!"
        
        return {
            "primary_action": actions[0] if actions else "Monitor quality",
            "all_actions": actions,
            "storage_tips": storage_tips,
            "urgency": urgency,
            "urgency_hindi": urgency_hindi,
            "sell_within_days": sell_within_days,
            "price_strategy": price_strategy,
            "english_summary": " ".join(actions[:2]) if len(actions) >= 2 else actions[0] if actions else "",
            "hindi_summary": hindi_summary,
            "confidence_level": "high" if freshness_result["is_confident"] else "medium",
        }
    
    def _simulate_freshness(self, crop: str) -> Dict:
        """Fallback simulation when detector not available."""
        import random
        
        grades = ["excellent", "good", "fair"]
        grade = random.choice(grades)
        score = {"excellent": 90, "good": 75, "fair": 55}.get(grade, 70)
        
        return {
            "crop_type": crop,
            "freshness_grade": grade,
            "quality_score": score,
            "overall_grade": "A" if score >= 85 else "B" if score >= 70 else "C",
            "damage_level": "minimal",
            "damage_score": 10,
            "ripeness_stage": "ripe",
            "confidence": 0.8,
            "is_confident": True,
            "demo_mode": True,
        }


# Import simplified spoilage predictor
class SimplifiedSpoilagePredictor:
    """Simplified spoilage predictor using heuristics (when ML model not available)."""
    
    CROP_SHELF_LIFE = {
        "tomato": {"ambient": 7, "cold": 21, "optimal_temp": (10, 15)},
        "banana": {"ambient": 5, "cold": 14, "optimal_temp": (13, 15)},
        "mango": {"ambient": 5, "cold": 21, "optimal_temp": (10, 13)},
        "apple": {"ambient": 14, "cold": 120, "optimal_temp": (0, 4)},
        "potato": {"ambient": 30, "cold": 120, "optimal_temp": (4, 8)},
        "onion": {"ambient": 30, "cold": 180, "optimal_temp": (0, 4)},
        "carrot": {"ambient": 7, "cold": 120, "optimal_temp": (0, 2)},
        "okra": {"ambient": 3, "cold": 10, "optimal_temp": (7, 10)},
        "orange": {"ambient": 10, "cold": 60, "optimal_temp": (3, 8)},
        "cucumber": {"ambient": 7, "cold": 14, "optimal_temp": (10, 13)},
    }
    
    def predict(
        self,
        crop_name: str,
        harvest_date: date,
        storage_type: str = "ambient",
        current_temp: float = 25.0,
        current_humidity: float = 70.0,
        transport_hours: float = 0,
        current_quality_score: int = 80,
    ) -> Dict[str, Any]:
        """Predict spoilage using simplified heuristics."""
        
        crop_data = self.CROP_SHELF_LIFE.get(
            crop_name.lower(),
            {"ambient": 7, "cold": 21, "optimal_temp": (5, 15)}
        )
        
        # Base shelf life
        base_days = crop_data[storage_type] if storage_type in crop_data else crop_data["ambient"]
        
        # Adjust based on current quality
        if current_quality_score < 50:
            base_days = int(base_days * 0.3)
        elif current_quality_score < 70:
            base_days = int(base_days * 0.6)
        elif current_quality_score < 85:
            base_days = int(base_days * 0.85)
        
        # Temperature factor
        optimal_temp = crop_data["optimal_temp"]
        if current_temp > optimal_temp[1] + 5:
            temp_factor = 0.5  # High temp = 50% reduction
        elif current_temp > optimal_temp[1]:
            temp_factor = 0.75
        else:
            temp_factor = 1.0
        
        adjusted_days = int(base_days * temp_factor)
        
        # Days elapsed
        days_elapsed = (date.today() - harvest_date).days
        remaining = max(0, adjusted_days - days_elapsed)
        
        # Risk calculation
        progress = days_elapsed / max(adjusted_days, 1)
        if progress < 0.3:
            risk = "low"
            prob = 0.1
        elif progress < 0.6:
            risk = "medium"
            prob = 0.35
        elif progress < 0.85:
            risk = "high"
            prob = 0.7
        else:
            risk = "critical"
            prob = 0.95
        
        return {
            "spoilage_risk": risk,
            "spoilage_probability": prob,
            "estimated_shelf_life_days": adjusted_days,
            "remaining_shelf_life_days": remaining,
            "risk_factors": [],
            "recommendations": [
                f"Store at {optimal_temp[0]}-{optimal_temp[1]}°C for optimal shelf life",
                f"Current temperature {current_temp}°C affects shelf life" if current_temp > optimal_temp[1] else "Temperature is acceptable"
            ],
        }


if __name__ == "__main__":
    # Quick test
    pipeline = IntegratedQualityPipeline(
        freshness_model_dir="freshness_detection/models",
        enable_ml_spoilage=False
    )
    
    # Simulate analysis
    import tempfile
    from PIL import Image
    import numpy as np
    
    # Create dummy image
    dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        dummy_img.save(f.name)
        
        result = pipeline.analyze(
            image_path=f.name,
            crop_name="tomato",
            storage_temp=28.0,
            storage_humidity=65.0,
        )
    
    print("\n" + "="*70)
    print("📊 INTEGRATED ANALYSIS RESULT")
    print("="*70)
    print(f"\nCurrent Quality: {result['current_quality']['freshness_grade'].upper()}")
    print(f"Quality Score: {result['current_quality']['quality_score']}/100")
    print(f"Spoilage Risk: {result['spoilage_prediction']['risk_level'].upper()}")
    print(f"Remaining Shelf Life: {result['spoilage_prediction']['remaining_days']} days")
    print(f"\n🎯 Primary Action: {result['action_plan']['primary_action']}")
    print(f"⏰ Urgency: {result['action_plan']['urgency'].upper()}")
    print(f"💰 Price Strategy: {result['action_plan']['price_strategy']}")
    print("\n" + "="*70)
