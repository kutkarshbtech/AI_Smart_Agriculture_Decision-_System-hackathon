"""
Inference engine for fruit freshness detection.

Provides:
- Single image prediction
- Batch prediction
- Confidence thresholding
- Human-readable result formatting (Hindi + English)

Usage:
    python inference.py --image fruit.jpg --model_path models/freshness_v1_best.pth
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import numpy as np
from PIL import Image

from dataset import (
    get_inference_transforms,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    NUM_CLASSES,
    CLASS_NAMES,
    IDX_TO_CLASS,
    FRUIT_CLASSES,
)
from model import FreshnessClassifier, build_model


class FreshnessDetector:
    """
    Production-ready inference engine for fruit freshness detection.

    Features:
    - Automatic device selection (CUDA/CPU)
    - Confidence thresholding
    - Top-K predictions
    - Hindi + English labels
    - Actionable recommendations for farmers
    """

    def __init__(
        self,
        model_path: str,
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize the freshness detector.

        Args:
            model_path: Path to trained .pth checkpoint
            device: "cuda", "cpu", or None for auto-detect
            confidence_threshold: Minimum confidence to accept prediction
        """
        # Device
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model
        self.model = build_model(pretrained=False, freeze_backbone=False)

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        self.confidence_threshold = confidence_threshold
        self.transform = get_inference_transforms()

        # Load class mapping if available
        mapping_path = os.path.join(os.path.dirname(model_path), "class_mapping.json")
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                self.class_mapping = json.load(f)
        else:
            self.class_mapping = None

        print(f"FreshnessDetector initialized on {self.device}")
        print(f"  Model: {model_path}")
        print(f"  Confidence threshold: {confidence_threshold}")

    def predict(self, image_path: str) -> Dict:
        """
        Predict freshness from an image file path.

        Args:
            image_path: Path to the fruit/produce image

        Returns:
            Dict with prediction results, confidence, recommendations
        """
        image = Image.open(image_path).convert("RGB")
        return self.predict_from_pil(image)

    def predict_from_bytes(self, image_bytes: bytes) -> Dict:
        """Predict from raw image bytes (e.g., from API upload)."""
        import io
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.predict_from_pil(image)

    @torch.no_grad()
    def predict_from_pil(self, image: Image.Image) -> Dict:
        """
        Predict freshness from a PIL Image.

        Returns comprehensive result dict with:
        - predicted_class, freshness_status, crop_type
        - confidence score
        - top-K predictions
        - quality_grade, freshness_score
        - farmer-friendly recommendations in Hindi + English
        """
        start_time = time.time()

        # Preprocess
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # Forward pass
        logits = self.model(input_tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        # Top predictions
        top_k = min(5, NUM_CLASSES)
        top_probs, top_indices = torch.topk(probs, top_k)

        predicted_idx = top_indices[0].item()
        predicted_class = IDX_TO_CLASS[predicted_idx]
        confidence = top_probs[0].item()

        class_info = FRUIT_CLASSES.get(predicted_class, {})
        freshness = class_info.get("freshness", "unknown")
        crop = class_info.get("crop", "unknown")
        hindi_name = class_info.get("hindi", "")

        # Determine quality metrics from freshness
        quality_grade, freshness_score = self._freshness_to_quality(freshness, confidence)

        # Build result
        result = {
            "predicted_class": predicted_class,
            "freshness_status": freshness,
            "crop_type": crop,
            "confidence": round(confidence, 4),
            "is_confident": confidence >= self.confidence_threshold,
            "quality_grade": quality_grade,
            "freshness_score": freshness_score,
            "hindi_label": hindi_name,
            "top_predictions": [
                {
                    "class": IDX_TO_CLASS[top_indices[i].item()],
                    "confidence": round(top_probs[i].item(), 4),
                    "hindi": FRUIT_CLASSES.get(IDX_TO_CLASS[top_indices[i].item()], {}).get("hindi", ""),
                }
                for i in range(top_k)
            ],
            "recommendations": self._generate_recommendations(freshness, crop, confidence, hindi_name),
            "inference_time_ms": round((time.time() - start_time) * 1000, 1),
        }

        return result

    def predict_batch(self, image_paths: List[str]) -> List[Dict]:
        """Predict freshness for multiple images."""
        results = []
        for path in image_paths:
            try:
                result = self.predict(path)
                result["image_path"] = path
                results.append(result)
            except Exception as e:
                results.append({
                    "image_path": path,
                    "error": str(e),
                })
        return results

    def _freshness_to_quality(
        self, freshness: str, confidence: float
    ) -> Tuple[str, int]:
        """
        Map freshness prediction to a quality grade and score.

        Returns:
            (quality_grade, freshness_score_0_100)
        """
        if freshness == "fresh":
            if confidence > 0.9:
                return "excellent", int(85 + confidence * 15)
            elif confidence > 0.7:
                return "good", int(70 + confidence * 15)
            else:
                return "good", int(60 + confidence * 15)
        else:  # rotten
            if confidence > 0.9:
                return "poor", int(5 + (1 - confidence) * 20)
            elif confidence > 0.7:
                return "poor", int(15 + (1 - confidence) * 25)
            else:
                return "average", int(30 + (1 - confidence) * 25)

    # Hindi names for each crop (used in recommendations)
    CROP_HINDI = {
        "apple": "सेब", "banana": "केला", "bell_pepper": "शिमला मिर्च",
        "bitter_gourd": "करेला", "capsicum": "शिमला मिर्च", "carrot": "गाजर",
        "cucumber": "खीरा", "mango": "आम", "okra": "भिंडी",
        "orange": "संतरा", "potato": "आलू", "strawberry": "स्ट्रॉबेरी",
        "tomato": "टमाटर",
    }

    def _generate_recommendations(
        self, freshness: str, crop: str, confidence: float,
        hindi_label: str = "",
    ) -> Dict[str, str]:
        """
        Generate actionable farmer recommendations in Hindi + English.
        """
        crop_display = crop.replace("_", " ").title()
        crop_hi = self.CROP_HINDI.get(crop, hindi_label or crop)

        if freshness == "fresh":
            if confidence > 0.8:
                return {
                    "action": "sell_at_premium",
                    "english": (
                        f"Your {crop_display} is in excellent fresh condition! "
                        f"You can command premium prices at the mandi. "
                        f"Consider selling within 2-3 days for best returns."
                    ),
                    "hindi": (
                        f"आपका {crop_hi} बहुत ताज़ा है! "
                        f"मंडी में अच्छे दाम मिल सकते हैं। "
                        f"2-3 दिन में बेचने पर सबसे अच्छा मुनाफ़ा होगा।"
                    ),
                    "urgency": "low",
                    "storage_advice_en": "Store in cool, dry place. Avoid direct sunlight.",
                    "storage_advice_hi": "ठंडी, सूखी जगह पर रखें। सीधी धूप से बचाएं।",
                }
            else:
                return {
                    "action": "sell_soon",
                    "english": (
                        f"Your {crop_display} appears fresh but may be approaching its peak. "
                        f"Sell within 1-2 days to get good prices."
                    ),
                    "hindi": (
                        f"आपका {crop_hi} ताज़ा लग रहा है लेकिन जल्दी बेचना बेहतर होगा। "
                        f"1-2 दिन में बेचें।"
                    ),
                    "urgency": "medium",
                    "storage_advice_en": "Ensure proper ventilation and cool temperature.",
                    "storage_advice_hi": "हवादार और ठंडी जगह पर रखें।",
                }
        else:  # rotten
            if confidence > 0.8:
                return {
                    "action": "sell_immediately_or_process",
                    "english": (
                        f"Your {crop_display} shows signs of spoilage. "
                        f"Sell immediately at a reduced price, or consider "
                        f"selling to a processing unit (juice, sauce, etc.)."
                    ),
                    "hindi": (
                        f"आपके {crop_hi} में खराबी के लक्षण हैं। "
                        f"तुरंत कम दाम पर बेचें, या प्रोसेसिंग यूनिट "
                        f"(जूस, सॉस) को बेचने पर विचार करें।"
                    ),
                    "urgency": "critical",
                    "storage_advice_en": "Do NOT store further. Separate from fresh produce immediately.",
                    "storage_advice_hi": "और न रखें। ताज़ी फसल से तुरंत अलग करें।",
                }
            else:
                return {
                    "action": "inspect_closely",
                    "english": (
                        f"Your {crop_display} may be showing early signs of spoilage. "
                        f"Inspect closely and sell within 1 day if quality is declining."
                    ),
                    "hindi": (
                        f"आपके {crop_hi} में खराबी शुरू हो सकती है। "
                        f"ध्यान से देखें और 1 दिन में बेच दें।"
                    ),
                    "urgency": "high",
                    "storage_advice_en": "Move to cold storage if available.",
                    "storage_advice_hi": "कोल्ड स्टोरेज में रखें अगर उपलब्ध है।",
                }


def main():
    parser = argparse.ArgumentParser(description="Fruit freshness inference")
    parser.add_argument("--image", type=str, required=True,
                        help="Path to fruit image")
    parser.add_argument("--model_path", type=str, default="models/freshness_v1_best.pth",
                        help="Path to trained model")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Confidence threshold")
    parser.add_argument("--device", type=str, default=None,
                        choices=["cuda", "cpu"])
    args = parser.parse_args()

    detector = FreshnessDetector(
        model_path=args.model_path,
        device=args.device,
        confidence_threshold=args.threshold,
    )

    result = detector.predict(args.image)

    print(f"\n{'='*50}")
    print(f"  FRESHNESS DETECTION RESULT")
    print(f"{'='*50}")
    print(f"  Image: {args.image}")
    print(f"  Crop:  {result['crop_type']}")
    print(f"  Hindi: {result['hindi_label']}")
    print(f"")
    print(f"  Status:     {'🟢 FRESH' if result['freshness_status'] == 'fresh' else '🔴 ROTTEN'}")
    print(f"  Confidence: {result['confidence']*100:.1f}%")
    print(f"  Grade:      {result['quality_grade']}")
    print(f"  Score:      {result['freshness_score']}/100")
    print(f"  Time:       {result['inference_time_ms']:.1f}ms")
    print(f"")
    print(f"  Recommendation:")
    rec = result["recommendations"]
    print(f"    EN: {rec['english']}")
    print(f"    HI: {rec['hindi']}")
    print(f"    Urgency: {rec['urgency']}")
    print(f"{'='*50}")

    # Print top predictions
    print(f"\n  Top predictions:")
    for i, pred in enumerate(result["top_predictions"], 1):
        print(f"    {i}. {pred['class']} ({pred['confidence']*100:.1f}%) — {pred['hindi']}")


if __name__ == "__main__":
    main()
