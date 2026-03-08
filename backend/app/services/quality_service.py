"""
Quality assessment service.
Analyzes produce images to determine freshness, damage, and ripeness.

Inference hierarchy (tried in order):
    1. SageMaker endpoint (production ONNX model)
    2. Amazon Bedrock Nova Lite vision (multimodal LLM — image analysis)
    3. Local ONNX / PyTorch model (development)
    4. Amazon Rekognition (generic label detection fallback)
    5. Simulated assessment (demo/testing fallback)
"""
import base64
import io
import json
import os
import random
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.config import settings


# ── Constants ─────────────────────────────────────────────────────

IMAGE_SIZE = 224
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Classes from our freshness detection model (sorted alphabetically)
# Matches ULNN Food Freshness Dataset: 13 food types × 2 states = 26 classes
FRESHNESS_CLASSES = [
    "fresh_apple", "fresh_banana", "fresh_bell_pepper", "fresh_bitter_gourd",
    "fresh_capsicum", "fresh_carrot", "fresh_cucumber", "fresh_mango",
    "fresh_okra", "fresh_orange", "fresh_potato", "fresh_strawberry", "fresh_tomato",
    "rotten_apple", "rotten_banana", "rotten_bell_pepper", "rotten_bitter_gourd",
    "rotten_capsicum", "rotten_carrot", "rotten_cucumber", "rotten_mango",
    "rotten_okra", "rotten_orange", "rotten_potato", "rotten_strawberry", "rotten_tomato",
]

# Hindi names for each class
FRESHNESS_HINDI = {
    "fresh_apple": "ताज़ा सेब",               "rotten_apple": "सड़ा सेब",
    "fresh_banana": "ताज़ा केला",             "rotten_banana": "सड़ा केला",
    "fresh_bell_pepper": "ताज़ा शिमला मिर्च",  "rotten_bell_pepper": "सड़ी शिमला मिर्च",
    "fresh_bitter_gourd": "ताज़ा करेला",       "rotten_bitter_gourd": "सड़ा करेला",
    "fresh_capsicum": "ताज़ी शिमला मिर्च",     "rotten_capsicum": "सड़ी शिमला मिर्च",
    "fresh_carrot": "ताज़ा गाजर",             "rotten_carrot": "सड़ी गाजर",
    "fresh_cucumber": "ताज़ा खीरा",           "rotten_cucumber": "सड़ा खीरा",
    "fresh_mango": "ताज़ा आम",                "rotten_mango": "सड़ा आम",
    "fresh_okra": "ताज़ी भिंडी",               "rotten_okra": "सड़ी भिंडी",
    "fresh_orange": "ताज़ा संतरा",            "rotten_orange": "सड़ा संतरा",
    "fresh_potato": "ताज़ा आलू",              "rotten_potato": "सड़ा आलू",
    "fresh_strawberry": "ताज़ी स्ट्रॉबेरी",     "rotten_strawberry": "सड़ी स्ट्रॉबेरी",
    "fresh_tomato": "ताज़ा टमाटर",            "rotten_tomato": "सड़ा टमाटर",
}

# Crop name normalization (maps user input → model class prefix)
CROP_ALIASES = {
    "apple": "apple", "seb": "apple", "सेब": "apple",
    "banana": "banana", "kela": "banana", "केला": "banana",
    "bell_pepper": "bell_pepper", "bell pepper": "bell_pepper", "शिमला मिर्च": "bell_pepper",
    "bitter_gourd": "bitter_gourd", "bitter gourd": "bitter_gourd", "karela": "bitter_gourd", "करेला": "bitter_gourd",
    "capsicum": "capsicum", "shimla mirch": "capsicum", "शिमला मिर्च": "capsicum",
    "carrot": "carrot", "gajar": "carrot", "गाजर": "carrot",
    "cucumber": "cucumber", "kheera": "cucumber", "खीरा": "cucumber",
    "mango": "mango", "aam": "mango", "आम": "mango",
    "okra": "okra", "bhindi": "okra", "भिंडी": "okra",
    "orange": "orange", "santra": "orange", "संतरा": "orange",
    "potato": "potato", "aloo": "potato", "आलू": "potato",
    "strawberry": "strawberry", "स्ट्रॉबेरी": "strawberry",
    "tomato": "tomato", "tamatar": "tomato", "टमाटर": "tomato",
}


class QualityService:
    """
    Image-based quality assessment for produce.

    Inference hierarchy (tried in order):
        1. SageMaker endpoint  (AWS-hosted ONNX model — preferred in production)
        2. Bedrock Nova Lite   (multimodal LLM — accurate vision analysis)
        3. Local ONNX model    (onnxruntime — fast CPU inference)
        4. Local PyTorch model  (checkpoint — development fallback)
        5. Amazon Rekognition   (generic label detection)
        6. Simulated assessment (demo / testing)
    """

    def __init__(self):
        self._onnx_session = None
        self._torch_model = None
        self._model_loaded = False
        self._model_type: Optional[str] = None  # "sagemaker", "onnx", "pytorch", or None

        # SageMaker endpoint (set via env or config)
        self._sagemaker_endpoint = os.environ.get(
            "SAGEMAKER_FRESHNESS_ENDPOINT",
            settings.SAGEMAKER_FRESHNESS_ENDPOINT
            if hasattr(settings, "SAGEMAKER_FRESHNESS_ENDPOINT")
            else "",
        )
        self._sagemaker_client = None

        if self._sagemaker_endpoint:
            self._init_sagemaker()
        else:
            # Try loading a local model
            self._try_load_model()

    # ── SageMaker endpoint ─────────────────────────────────────────

    def _init_sagemaker(self):
        """Initialize SageMaker runtime client for endpoint invocation."""
        try:
            from app.core.aws_clients import get_sagemaker_runtime
            self._sagemaker_client = get_sagemaker_runtime()
            self._model_loaded = True
            self._model_type = "sagemaker"
            print(f"✓ SageMaker freshness endpoint configured: {self._sagemaker_endpoint}")
        except Exception as e:
            print(f"⚠ SageMaker client init failed ({e}), falling back to local model")
            self._try_load_model()

    def _assess_with_sagemaker(
        self, image_bytes: bytes, crop_name: str
    ) -> Dict[str, Any]:
        """
        Invoke the SageMaker endpoint with raw image bytes.

        The endpoint runs our ONNX model and returns a structured JSON
        response with quality scores, recommendations, etc.
        """
        start_time = time.time()

        response = self._sagemaker_client.invoke_endpoint(
            EndpointName=self._sagemaker_endpoint,
            ContentType="image/jpeg",
            Body=image_bytes,
        )

        result = json.loads(response["Body"].read().decode("utf-8"))
        e2e_ms = round((time.time() - start_time) * 1000, 1)

        # Normalize the SageMaker response into our standard schema
        freshness_status = result.get("freshness_status", "unknown")
        confidence = result.get("confidence", 0.0)
        crop_type = result.get("crop_type", crop_name)
        quality_score = result.get("quality_score", 50)

        grade_map = {"A": "excellent", "B": "good", "C": "average", "D": "poor"}
        grade = grade_map.get(result.get("quality_grade", "C"), "average")

        defects = []
        if freshness_status == "rotten":
            if confidence > 0.85:
                defects.extend(["visible spoilage", "discoloration"])
            elif confidence > 0.6:
                defects.append("early signs of spoilage")

        return {
            "overall_grade": grade,
            "quality_score": quality_score,
            "freshness_score": result.get("freshness_score", quality_score),
            "damage_score": result.get("damage_score", max(0, 100 - quality_score)),
            "ripeness_level": result.get("ripeness_level", "ripe"),
            "freshness_status": freshness_status,
            "predicted_class": result.get("predicted_class", ""),
            "confidence": round(confidence, 4),
            "defects_detected": defects,
            "analysis_summary": self._generate_summary(
                crop_name, grade, quality_score, defects,
                result.get("ripeness_level", "ripe"),
            ),
            "analysis_summary_hindi": result.get("recommendations", {}).get("hindi", ""),
            "top_predictions": result.get("top_predictions", []),
            "recommendations": result.get("recommendations", {}),
            "model_type": "sagemaker",
            "inference_time_ms": result.get("inference_time_ms", 0),
            "e2e_latency_ms": e2e_ms,
        }

    # ── Local model loading ───────────────────────────────────────

    def _try_load_model(self):
        """Attempt to load the custom freshness detection model."""
        model_dir = os.environ.get(
            "FRESHNESS_MODEL_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "freshness_detection", "models"),
        )
        model_dir = str(Path(model_dir).resolve())

        # Try ONNX first (fastest inference)
        onnx_path = os.path.join(model_dir, "freshness_v1_best.onnx")
        if os.path.exists(onnx_path):
            try:
                import onnxruntime as ort
                self._onnx_session = ort.InferenceSession(
                    onnx_path,
                    providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
                )
                self._model_loaded = True
                self._model_type = "onnx"
                print(f"✓ Loaded ONNX freshness model from: {onnx_path}")
                return
            except Exception as e:
                print(f"  ONNX load failed: {e}")

        # Try PyTorch checkpoint
        pth_path = os.path.join(model_dir, "freshness_v1_best.pth")
        if os.path.exists(pth_path):
            try:
                import torch
                from torchvision import models
                from torchvision.models import MobileNet_V2_Weights

                model = models.mobilenet_v2(weights=None)
                in_features = model.classifier[1].in_features
                model.classifier = torch.nn.Sequential(
                    torch.nn.Dropout(p=0.3),
                    torch.nn.Linear(in_features, 512),
                    torch.nn.BatchNorm1d(512),
                    torch.nn.ReLU(inplace=True),
                    torch.nn.Dropout(p=0.15),
                    torch.nn.Linear(512, 128),
                    torch.nn.ReLU(inplace=True),
                    torch.nn.Dropout(p=0.09),
                    torch.nn.Linear(128, len(FRESHNESS_CLASSES)),
                )
                checkpoint = torch.load(pth_path, map_location="cpu", weights_only=True)
                model.load_state_dict(checkpoint["model_state_dict"])
                model.eval()
                self._torch_model = model
                self._model_loaded = True
                self._model_type = "pytorch"
                print(f"✓ Loaded PyTorch freshness model from: {pth_path}")
                return
            except Exception as e:
                print(f"  PyTorch load failed: {e}")

        print("⚠ No custom freshness model found — will use Rekognition/simulation fallback")

    # ── Image preprocessing ───────────────────────────────────────

    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image bytes for model inference.

        Returns:
            numpy array of shape (1, 3, 224, 224), normalized to ImageNet stats
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Resize to 256, center crop to 224
        image = image.resize((256, 256), Image.BILINEAR)
        left = (256 - IMAGE_SIZE) // 2
        top = (256 - IMAGE_SIZE) // 2
        image = image.crop((left, top, left + IMAGE_SIZE, top + IMAGE_SIZE))

        # To numpy array, normalize
        img_array = np.array(image, dtype=np.float32) / 255.0
        img_array = (img_array - IMAGENET_MEAN) / IMAGENET_STD

        # HWC → CHW, add batch dimension
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    # ── Main assessment method ────────────────────────────────────

    async def assess_quality_from_image(
        self, image_bytes: bytes, crop_name: str
    ) -> Dict[str, Any]:
        """
        Analyze produce image for freshness/quality.

        When settings.AWS_ONLY is True, only SageMaker and Rekognition are used.
        Local models and simulation are disabled — failures raise HTTPException.

        After quality assessment, enriches the result with Bedrock-generated
        farmer recommendations in both English and Hindi.
        """
        aws_only = settings.AWS_ONLY
        result = None

        # 1. SageMaker endpoint (production)
        if self._model_type == "sagemaker":
            try:
                result = self._assess_with_sagemaker(image_bytes, crop_name)
            except Exception as e:
                print(f"SageMaker inference failed ({e}), trying Bedrock vision...")

        # 2. Bedrock Nova Lite vision (multimodal LLM — accurate image analysis)
        if result is None:
            try:
                result = await self._assess_with_bedrock_vision(image_bytes, crop_name)
            except Exception as e:
                print(f"Bedrock vision failed ({e}), trying next fallback...")

        # 3. Local custom MobileNetV2 freshness model (disabled in AWS_ONLY)
        if result is None and not aws_only and self._model_loaded and self._model_type in ("onnx", "pytorch"):
            try:
                result = self._assess_with_custom_model(image_bytes, crop_name)
            except Exception as e:
                print(f"Custom model inference failed ({e}), falling back...")

        # 4. Amazon Rekognition
        if result is None:
            try:
                result = await self._assess_with_rekognition(image_bytes, crop_name)
            except Exception as e:
                if aws_only:
                    raise RuntimeError(
                        f"AWS_ONLY mode: All vision backends failed. "
                        "SageMaker, Bedrock, and Rekognition are unavailable."
                    )
                print(f"Rekognition unavailable ({e}), using simulated assessment")

        # 5. Simulation fallback (disabled in AWS_ONLY)
        if result is None:
            result = self._simulate_assessment(crop_name)

        # ── Enrich with Bedrock AI recommendations (English + Hindi) ──
        try:
            bedrock_recs = await self._generate_bedrock_recommendations(result, crop_name)
            result["bedrock_recommendations"] = bedrock_recs
            # Also update the top-level recommendations with Bedrock output
            result["recommendations"] = {
                **(result.get("recommendations") or {}),
                "english": bedrock_recs.get("recommendation_en", ""),
                "hindi": bedrock_recs.get("recommendation_hi", ""),
                "storage_tips_en": bedrock_recs.get("storage_tips_en", ""),
                "storage_tips_hi": bedrock_recs.get("storage_tips_hi", ""),
                "selling_strategy_en": bedrock_recs.get("selling_strategy_en", ""),
                "selling_strategy_hi": bedrock_recs.get("selling_strategy_hi", ""),
                "urgency": bedrock_recs.get("urgency", "medium"),
                "action": bedrock_recs.get("action", "sell_soon"),
                "source": bedrock_recs.get("source", "bedrock"),
            }
            result["analysis_summary_hindi"] = bedrock_recs.get("recommendation_hi", "")
        except Exception as e:
            print(f"⚠ Bedrock recommendation enrichment failed ({e})")

        return result

    # ── Custom model inference ────────────────────────────────────

    def _assess_with_custom_model(
        self, image_bytes: bytes, crop_name: str
    ) -> Dict[str, Any]:
        """
        Run inference with our trained MobileNetV2 freshness classifier.

        Returns structured quality assessment with:
        - Freshness status (fresh/rotten)
        - Confidence score
        - Quality grade
        - Top predictions
        - Farmer recommendations (Hindi + English)
        """
        start_time = time.time()

        # Preprocess
        input_array = self._preprocess_image(image_bytes)

        # Inference
        if self._model_type == "onnx":
            logits = self._infer_onnx(input_array)
        else:
            logits = self._infer_pytorch(input_array)

        # Softmax
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        probs = probs[0]  # Remove batch dim

        # Top predictions
        top_k = min(5, len(FRESHNESS_CLASSES))
        top_indices = np.argsort(probs)[::-1][:top_k]

        predicted_idx = top_indices[0]
        predicted_class = FRESHNESS_CLASSES[predicted_idx]
        confidence = float(probs[predicted_idx])

        # Parse class name
        freshness_status = "fresh" if predicted_class.startswith("fresh_") else "rotten"
        crop_type = predicted_class.split("_", 1)[1]

        # Quality grading
        quality_grade, freshness_score, damage_score = self._compute_quality_metrics(
            freshness_status, confidence, probs
        )

        # Defects
        defects = self._detect_defects(freshness_status, confidence, probs, top_indices)

        # Ripeness mapping
        ripeness = self._estimate_ripeness(freshness_status, confidence)

        inference_ms = round((time.time() - start_time) * 1000, 1)

        # Recommendations
        recommendations = self._generate_farmer_recommendations(
            freshness_status, crop_type, confidence
        )

        return {
            "overall_grade": quality_grade,
            "quality_score": freshness_score,
            "freshness_score": freshness_score,
            "damage_score": damage_score,
            "ripeness_level": ripeness,
            "freshness_status": freshness_status,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "defects_detected": defects,
            "analysis_summary": self._generate_summary(
                crop_name, quality_grade, freshness_score, defects, ripeness
            ),
            "analysis_summary_hindi": recommendations.get("hindi", ""),
            "top_predictions": [
                {
                    "class": FRESHNESS_CLASSES[idx],
                    "confidence": round(float(probs[idx]), 4),
                    "hindi": FRESHNESS_HINDI.get(FRESHNESS_CLASSES[idx], ""),
                }
                for idx in top_indices
            ],
            "recommendations": recommendations,
            "model_type": self._model_type,
            "inference_time_ms": inference_ms,
        }

    def _infer_onnx(self, input_array: np.ndarray) -> np.ndarray:
        """Run ONNX inference."""
        input_name = self._onnx_session.get_inputs()[0].name
        outputs = self._onnx_session.run(None, {input_name: input_array.astype(np.float32)})
        return outputs[0]

    def _infer_pytorch(self, input_array: np.ndarray) -> np.ndarray:
        """Run PyTorch inference."""
        import torch
        with torch.no_grad():
            tensor = torch.from_numpy(input_array).float()
            logits = self._torch_model(tensor)
            return logits.numpy()

    # ── Quality metrics ───────────────────────────────────────────

    def _compute_quality_metrics(
        self, freshness: str, confidence: float, probs: np.ndarray
    ) -> Tuple[str, int, int]:
        """
        Compute quality grade, freshness score (0-100), and damage score (0-100).
        """
        if freshness == "fresh":
            if confidence > 0.9:
                grade = "excellent"
                freshness_score = int(85 + confidence * 15)
            elif confidence > 0.7:
                grade = "good"
                freshness_score = int(70 + confidence * 15)
            elif confidence > 0.5:
                grade = "good"
                freshness_score = int(55 + confidence * 20)
            else:
                grade = "average"
                freshness_score = int(40 + confidence * 30)
            damage_score = max(0, 100 - freshness_score)
        else:
            if confidence > 0.9:
                grade = "poor"
                freshness_score = int(5 + (1 - confidence) * 15)
            elif confidence > 0.7:
                grade = "poor"
                freshness_score = int(15 + (1 - confidence) * 25)
            else:
                grade = "average"
                freshness_score = int(30 + (1 - confidence) * 30)
            damage_score = min(100, 100 - freshness_score + 10)

        freshness_score = max(0, min(100, freshness_score))
        damage_score = max(0, min(100, damage_score))

        return grade, freshness_score, damage_score

    def _detect_defects(
        self, freshness: str, confidence: float,
        probs: np.ndarray, top_indices: np.ndarray
    ) -> List[str]:
        """Infer defects from model predictions."""
        defects = []

        if freshness == "rotten":
            if confidence > 0.85:
                defects.extend(["visible spoilage", "discoloration"])
            elif confidence > 0.6:
                defects.append("early signs of spoilage")
            else:
                defects.append("minor quality issues")

        # Check if rotten classes have significant probability even if fresh wins
        if freshness == "fresh":
            total_rotten_prob = sum(
                probs[i] for i, cls in enumerate(FRESHNESS_CLASSES) if cls.startswith("rotten_")
            )
            if total_rotten_prob > 0.3:
                defects.append("borderline freshness — inspect closely")

        return defects

    def _estimate_ripeness(self, freshness: str, confidence: float) -> str:
        """Estimate ripeness level from freshness prediction."""
        if freshness == "fresh":
            if confidence > 0.85:
                return "ripe"
            elif confidence > 0.6:
                return "ripe"
            else:
                return "slightly overripe"
        else:
            if confidence > 0.8:
                return "overripe"
            else:
                return "overripe"

    # ── Farmer recommendations ────────────────────────────────────

    def _generate_farmer_recommendations(
        self, freshness: str, crop: str, confidence: float
    ) -> Dict[str, str]:
        """Generate actionable recommendations in Hindi + English."""
        if freshness == "fresh":
            if confidence > 0.8:
                return {
                    "action": "sell_at_premium",
                    "urgency": "low",
                    "english": (
                        f"Your {crop} is in excellent fresh condition! "
                        f"You can command premium prices at the mandi. "
                        f"Consider selling within 2-3 days for best returns."
                    ),
                    "hindi": (
                        f"आपका {crop} बहुत ताज़ा है! "
                        f"मंडी में अच्छे दाम मिल सकते हैं। "
                        f"2-3 दिन में बेचने पर सबसे अच्छा मुनाफ़ा होगा।"
                    ),
                }
            else:
                return {
                    "action": "sell_soon",
                    "urgency": "medium",
                    "english": (
                        f"Your {crop} appears fresh but may be approaching peak ripeness. "
                        f"Consider selling within 1-2 days."
                    ),
                    "hindi": (
                        f"आपका {crop} ताज़ा लगता है लेकिन जल्दी बेचना बेहतर होगा। "
                        f"1-2 दिन के अंदर बेच दें।"
                    ),
                }
        else:
            if confidence > 0.8:
                return {
                    "action": "sell_immediately",
                    "urgency": "critical",
                    "english": (
                        f"Your {crop} shows signs of spoilage. "
                        f"Sell immediately at reduced price or to processing units. "
                        f"Separate from fresh produce to prevent spread."
                    ),
                    "hindi": (
                        f"आपके {crop} में खराबी के लक्षण हैं। "
                        f"तुरंत कम दाम पर बेचें या प्रोसेसिंग यूनिट को बेचें। "
                        f"ताज़ी फसल से अलग करें।"
                    ),
                }
            else:
                return {
                    "action": "inspect_and_sell",
                    "urgency": "high",
                    "english": (
                        f"Your {crop} may be showing early signs of quality decline. "
                        f"Inspect closely and sell within today if deteriorating."
                    ),
                    "hindi": (
                        f"आपके {crop} में खराबी शुरू हो सकती है। "
                        f"ध्यान से जांचें और आज ही बेचने की कोशिश करें।"
                    ),
                }

    # ── Bedrock AI Recommendations (English + Hindi) ─────────────

    async def _generate_bedrock_recommendations(
        self, assessment: Dict[str, Any], crop_name: str
    ) -> Dict[str, Any]:
        """
        Use Amazon Bedrock Nova Lite to generate personalised farmer
        recommendations in both English and Hindi based on the quality
        assessment results.

        Called *after* the quality assessment is complete — works with
        results from any backend (SageMaker, Bedrock vision, Rekognition, etc.).

        Returns a dict with keys:
            recommendation_en, recommendation_hi, storage_tips_en,
            storage_tips_hi, selling_strategy_en, selling_strategy_hi,
            urgency, action
        """
        from app.core.aws_clients import get_bedrock_runtime

        try:
            client = get_bedrock_runtime()

            quality_score = assessment.get("quality_score", 50)
            freshness_status = assessment.get("freshness_status", "unknown")
            grade = assessment.get("overall_grade", "average")
            defects = assessment.get("defects_detected", [])
            ripeness = assessment.get("ripeness_level", "ripe")
            damage_score = assessment.get("damage_score", 0)

            defects_str = ", ".join(defects) if defects else "none detected"

            prompt = (
                f"You are an expert Indian agricultural advisor helping a farmer.\n\n"
                f"QUALITY ASSESSMENT RESULTS:\n"
                f"- Crop: {crop_name}\n"
                f"- Freshness: {freshness_status}\n"
                f"- Quality Score: {quality_score}/100\n"
                f"- Grade: {grade}\n"
                f"- Damage Score: {damage_score}/100\n"
                f"- Ripeness: {ripeness}\n"
                f"- Defects: {defects_str}\n\n"
                f"Based on these results, provide practical farmer recommendations.\n"
                f"Return ONLY a JSON object (no markdown fences) with these keys:\n"
                f'{{\n'
                f'  "recommendation_en": "2-3 sentence actionable advice in English",\n'
                f'  "recommendation_hi": "Same advice in Hindi (Devanagari script)",\n'
                f'  "storage_tips_en": "1-2 sentence storage advice in English",\n'
                f'  "storage_tips_hi": "Same storage advice in Hindi",\n'
                f'  "selling_strategy_en": "1-2 sentence selling strategy in English",\n'
                f'  "selling_strategy_hi": "Same selling strategy in Hindi",\n'
                f'  "urgency": "low" | "medium" | "high" | "critical",\n'
                f'  "action": "sell_at_premium" | "sell_soon" | "sell_immediately" | "process_or_discard"\n'
                f'}}\n\n'
                f"IMPORTANT:\n"
                f"- Hindi text MUST be in Devanagari script (हिंदी), not transliteration\n"
                f"- Be specific to the crop type ({crop_name})\n"
                f"- Include practical tips relevant to Indian farmers and mandis\n"
                f"- If quality is poor, suggest processing options (jam, pickle, juice, etc.)\n"
            )

            response = client.converse(
                modelId=settings.BEDROCK_MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={"maxTokens": 800, "temperature": 0.3},
            )

            reply = response["output"]["message"]["content"][0]["text"]
            parsed = self._parse_bedrock_vision_json(reply)

            # Validate required keys exist
            required_keys = [
                "recommendation_en", "recommendation_hi",
                "storage_tips_en", "storage_tips_hi",
                "selling_strategy_en", "selling_strategy_hi",
            ]
            for key in required_keys:
                if key not in parsed:
                    parsed[key] = ""

            if "urgency" not in parsed:
                # Derive from quality score
                if quality_score >= 80:
                    parsed["urgency"] = "low"
                elif quality_score >= 50:
                    parsed["urgency"] = "medium"
                elif quality_score >= 25:
                    parsed["urgency"] = "high"
                else:
                    parsed["urgency"] = "critical"

            if "action" not in parsed:
                if quality_score >= 80:
                    parsed["action"] = "sell_at_premium"
                elif quality_score >= 50:
                    parsed["action"] = "sell_soon"
                elif quality_score >= 25:
                    parsed["action"] = "sell_immediately"
                else:
                    parsed["action"] = "process_or_discard"

            parsed["source"] = "bedrock"
            return parsed

        except Exception as e:
            print(f"⚠ Bedrock recommendation generation failed ({e}), using static fallback")
            # Fall back to rule-based recommendations
            crop_key = crop_name.lower().replace(" ", "_")
            static = self._generate_farmer_recommendations(
                freshness_status or ("fresh" if quality_score >= 50 else "rotten"),
                crop_key,
                assessment.get("confidence", 0.7),
            )
            return {
                "recommendation_en": static.get("english", ""),
                "recommendation_hi": static.get("hindi", ""),
                "storage_tips_en": "",
                "storage_tips_hi": "",
                "selling_strategy_en": "",
                "selling_strategy_hi": "",
                "urgency": static.get("urgency", "medium"),
                "action": static.get("action", "sell_soon"),
                "source": "static_fallback",
            }

    # ── Bedrock Nova Lite vision fallback ──────────────────────────

    async def _assess_with_bedrock_vision(
        self, image_bytes: bytes, crop_name: str
    ) -> Dict[str, Any]:
        """
        Use Amazon Bedrock Nova Lite (multimodal) to analyse produce images.

        Sends the image together with a structured prompt and asks the LLM
        to return a JSON object with quality metrics.  Much more accurate
        than Rekognition for freshness/rot detection because the LLM
        actually *understands* what rotten produce looks like.
        """
        from app.core.aws_clients import get_bedrock_runtime

        start_time = time.time()
        client = get_bedrock_runtime()

        # Determine MIME type
        try:
            img = Image.open(io.BytesIO(image_bytes))
            fmt = (img.format or "JPEG").lower()
            mime_map = {"jpeg": "image/jpeg", "jpg": "image/jpeg",
                        "png": "image/png", "webp": "image/webp",
                        "gif": "image/gif"}
            media_type = mime_map.get(fmt, "image/jpeg")
            # Nova Lite needs jpeg/png/gif/webp
            if fmt not in ("jpeg", "jpg", "png", "gif", "webp"):
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG")
                image_bytes = buf.getvalue()
                media_type = "image/jpeg"
        except Exception:
            media_type = "image/jpeg"

        system_text = (
            "You are a strict agricultural produce quality inspector. "
            "You err on the side of caution — even small signs of decay "
            "should significantly reduce the quality score. "
            "Analyse the provided image and return ONLY a JSON "
            "object (no markdown fences, no explanation outside the JSON) "
            "with exactly these keys:\n"
            '{\n'
            '  "freshness_status": "fresh" or "rotten",\n'
            '  "quality_score": integer 0-100 (100 = perfect, 0 = completely spoiled),\n'
            '  "confidence": float 0-1,\n'
            '  "overall_grade": "excellent" | "good" | "average" | "poor",\n'
            '  "damage_score": integer 0-100 (100 = heavily damaged),\n'
            '  "ripeness_level": "unripe" | "ripe" | "slightly overripe" | "overripe",\n'
            '  "defects_detected": [list of strings],\n'
            '  "crop_type": "detected crop name",\n'
            '  "explanation": "1-2 sentence explanation"\n'
            '}\n\n'
            "Scoring guide (be strict — when in doubt, score LOWER):\n"
            "- Firm, vibrant colour, no blemishes at all → 85-100 (excellent)\n"
            "- Minor surface marks but otherwise firm and colourful → 60-84 (good)\n"
            "- Any browning, soft spots, wrinkling, dark patches → 25-59 (average/poor)\n"
            "- Mold, slime, heavy browning, collapse, black spots → 0-24 (poor)\n\n"
            "IMPORTANT: Any visible browning, dark spots, or soft/mushy areas "
            "means the produce is NOT fresh. Score it below 40 and set "
            'freshness_status to "rotten".\n'
        )

        response = client.converse(
            modelId=settings.BEDROCK_MODEL_ID,
            system=[{"text": system_text}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": media_type.split("/")[1],
                                "source": {"bytes": image_bytes},
                            }
                        },
                        {
                            "text": (
                                f"The farmer says this is: {crop_name}. "
                                "Analyse the image and return the JSON assessment."
                            )
                        },
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 600, "temperature": 0.0},
        )

        reply = response["output"]["message"]["content"][0]["text"]
        e2e_ms = round((time.time() - start_time) * 1000, 1)

        # Parse the JSON from the LLM response
        parsed = self._parse_bedrock_vision_json(reply)

        freshness_status = parsed.get("freshness_status", "fresh")
        quality_score = max(0, min(100, int(parsed.get("quality_score", 50))))
        confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.7))))
        grade = parsed.get("overall_grade", "average")
        damage_score = max(0, min(100, int(parsed.get("damage_score", 100 - quality_score))))
        ripeness = parsed.get("ripeness_level", "ripe")
        defects = parsed.get("defects_detected", [])
        crop_type = parsed.get("crop_type", crop_name)

        # Generate recommendations from parsed results
        recommendations = self._generate_farmer_recommendations(
            freshness_status, crop_type, confidence
        )

        return {
            "overall_grade": grade,
            "quality_score": quality_score,
            "freshness_score": quality_score,
            "damage_score": damage_score,
            "ripeness_level": ripeness,
            "freshness_status": freshness_status,
            "predicted_class": f"{freshness_status}_{crop_type}",
            "confidence": round(confidence, 4),
            "defects_detected": defects if isinstance(defects, list) else [],
            "analysis_summary": self._generate_summary(
                crop_name, grade, quality_score,
                defects if isinstance(defects, list) else [], ripeness,
            ),
            "analysis_summary_hindi": recommendations.get("hindi", ""),
            "explanation": parsed.get("explanation", ""),
            "recommendations": recommendations,
            "model_type": f"bedrock-vision ({settings.BEDROCK_MODEL_ID})",
            "inference_time_ms": e2e_ms,
        }

    @staticmethod
    def _parse_bedrock_vision_json(text: str) -> Dict[str, Any]:
        """Robustly extract JSON from LLM output (handles markdown fences, preamble, etc.)."""
        # Strip markdown code fences if present
        text = text.strip()
        fence_match = re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)
        else:
            # Try to find a raw JSON object
            brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if brace_match:
                text = brace_match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Last resort: return conservative defaults
            return {
                "freshness_status": "fresh",
                "quality_score": 50,
                "confidence": 0.5,
                "overall_grade": "average",
                "damage_score": 50,
                "ripeness_level": "ripe",
                "defects_detected": [],
                "explanation": f"Could not parse LLM response: {text[:200]}",
            }

    # ── Rekognition fallback ──────────────────────────────────────

    # Label mapping for Rekognition-based assessment
    QUALITY_LABELS = {
        "fresh": {"score_boost": 20, "grade_hint": "good"},
        "ripe": {"score_boost": 10, "grade_hint": "good"},
        "overripe": {"score_boost": -15, "grade_hint": "average"},
        "unripe": {"score_boost": -5, "grade_hint": "average"},
        "rotten": {"score_boost": -40, "grade_hint": "poor"},
        "damaged": {"score_boost": -30, "grade_hint": "poor"},
        "bruised": {"score_boost": -20, "grade_hint": "average"},
        "moldy": {"score_boost": -50, "grade_hint": "poor"},
        "wilted": {"score_boost": -25, "grade_hint": "poor"},
        "spotty": {"score_boost": -10, "grade_hint": "average"},
    }

    async def _assess_with_rekognition(
        self, image_bytes: bytes, crop_name: str
    ) -> Dict[str, Any]:
        """Fallback: Use Amazon Rekognition to detect labels and assess quality."""
        from app.core.aws_clients import get_rekognition_client

        client = get_rekognition_client()

        response = client.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=20,
            MinConfidence=50,
        )

        labels = response.get("Labels", [])

        base_score = 50
        defects = []
        ripeness = "ripe"

        for label in labels:
            name_lower = label["Name"].lower()
            confidence = label["Confidence"]

            if name_lower in self.QUALITY_LABELS:
                info = self.QUALITY_LABELS[name_lower]
                adjustment = info["score_boost"] * (confidence / 100)
                base_score += adjustment

                if info["score_boost"] < 0:
                    defects.append(f"{label['Name']} ({confidence:.0f}%)")

                if name_lower in ("overripe", "unripe", "ripe"):
                    ripeness = name_lower

        quality_score = max(0, min(100, round(base_score)))

        if quality_score >= 85:
            grade = "excellent"
        elif quality_score >= 65:
            grade = "good"
        elif quality_score >= 40:
            grade = "average"
        else:
            grade = "poor"

        freshness_score = min(100, max(0, quality_score + random.randint(-5, 10)))
        damage_score = max(0, 100 - quality_score + random.randint(-10, 5))

        return {
            "overall_grade": grade,
            "quality_score": quality_score,
            "freshness_score": freshness_score,
            "damage_score": min(100, max(0, damage_score)),
            "ripeness_level": ripeness,
            "defects_detected": defects,
            "analysis_summary": self._generate_summary(crop_name, grade, quality_score, defects, ripeness),
            "detected_labels": [{"name": l["Name"], "confidence": l["Confidence"]} for l in labels[:10]],
            "model_type": "rekognition",
        }

    # ── Simulation fallback ───────────────────────────────────────

    def _simulate_assessment(self, crop_name: str) -> Dict[str, Any]:
        """Simulated quality assessment for demo/testing."""
        random.seed(hash(crop_name + str(random.random())))

        quality_score = random.randint(45, 95)
        freshness_score = max(0, min(100, quality_score + random.randint(-10, 15)))
        damage_score = max(0, min(100, 100 - quality_score + random.randint(-15, 10)))

        if quality_score >= 85:
            grade = "excellent"
            ripeness = "ripe"
            defects = []
        elif quality_score >= 65:
            grade = "good"
            ripeness = "ripe"
            defects = random.choice([[], ["minor spots"]])
        elif quality_score >= 40:
            grade = "average"
            ripeness = random.choice(["overripe", "ripe"])
            defects = random.choice([["some bruising"], ["slight discoloration"], ["minor damage"]])
        else:
            grade = "poor"
            ripeness = "overripe"
            defects = random.choice([["significant bruising", "soft spots"], ["mold detected"], ["extensive damage"]])

        # Normalize crop name for recommendations
        crop_key = CROP_ALIASES.get(crop_name.lower(), crop_name.lower())
        freshness_status = "fresh" if quality_score >= 50 else "rotten"

        return {
            "overall_grade": grade,
            "quality_score": quality_score,
            "freshness_score": freshness_score,
            "damage_score": max(0, damage_score),
            "ripeness_level": ripeness,
            "freshness_status": freshness_status,
            "defects_detected": defects,
            "analysis_summary": self._generate_summary(crop_name, grade, quality_score, defects, ripeness),
            "recommendations": self._generate_farmer_recommendations(
                freshness_status, crop_name, quality_score / 100.0
            ),
            "model_type": "simulated",
        }

    # ── Summary generation ────────────────────────────────────────

    def _generate_summary(
        self, crop_name: str, grade: str, score: float,
        defects: List[str], ripeness: str
    ) -> str:
        """Generate a human-readable quality summary."""
        summary = f"Your {crop_name} has been assessed as '{grade}' quality (score: {score}/100). "
        summary += f"Ripeness level: {ripeness}. "

        if defects:
            summary += f"Defects detected: {', '.join(defects)}. "

        if grade == "excellent":
            summary += "This produce is in excellent condition and can command premium prices."
        elif grade == "good":
            summary += "Good quality — suitable for direct market sale."
        elif grade == "average":
            summary += "Average quality — consider selling quickly or to processing units."
        else:
            summary += "Poor quality — consider immediate sale at local market or for processing."

        return summary

    # ── Model status ──────────────────────────────────────────────

    def get_model_status(self) -> Dict[str, Any]:
        """Return current model status for health checks."""
        return {
            "model_loaded": self._model_loaded,
            "model_type": self._model_type,
            "supported_crops": list(set(
                cls.split("_", 1)[1] for cls in FRESHNESS_CLASSES
            )),
            "num_classes": len(FRESHNESS_CLASSES),
        }


# Singleton
quality_service = QualityService()
