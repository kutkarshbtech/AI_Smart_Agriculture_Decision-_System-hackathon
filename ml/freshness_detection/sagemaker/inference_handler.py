"""
SageMaker inference handler for the SwadeshAI Freshness Detection model.

This script is packaged inside model.tar.gz and executed by the SageMaker
PyTorch serving container.  It implements the four SageMaker contract functions:
    model_fn   — load the ONNX model
    input_fn   — deserialize incoming image bytes / JSON
    predict_fn — run ONNX inference, returns CV-only structured JSON
    output_fn  — serialize the response as JSON

CV output is intentionally free of pre-baked recommendations.
Pass the returned JSON directly to Amazon Bedrock (Claude) to obtain
insights, causal explanations, and farmer-friendly recommendations.

Supports:
    - image/jpeg, image/png  → raw image bytes (fastest path)
    - application/json       → base64-encoded image in {"image": "..."} payload
    - application/x-npy      → pre-processed numpy array

Output schema (all fields are Bedrock-prompt-friendly):
    {
        "predicted_class":   str,    # e.g. "fresh_tomato"
        "freshness_status":  str,    # "fresh" | "rotten"
        "crop_type":         str,    # e.g. "tomato"
        "hindi_label":       str,    # Devanagari name
        "confidence":        float,  # 0-1
        "quality_score":     int,    # 0-100
        "freshness_score":   int,    # 0-100
        "damage_score":      int,    # 0-100
        "ripeness_level":    int,    # 0-100
        "quality_grade":     str,    # A / B / C / D
        "top_predictions":   list,
        "inference_time_ms": float,
        "bedrock_context":   str     # ready-to-inject plain-text summary
    }
"""

import io
import os
import json
import base64
import time
from typing import Any, Dict, Tuple

import numpy as np
from PIL import Image

# ── Constants ────────────────────────────────────────────────────

IMAGE_SIZE = 224
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

CLASS_NAMES = [
    "fresh_apple", "fresh_banana", "fresh_bell_pepper", "fresh_bitter_gourd",
    "fresh_capsicum", "fresh_carrot", "fresh_cucumber", "fresh_mango",
    "fresh_okra", "fresh_orange", "fresh_potato", "fresh_strawberry", "fresh_tomato",
    "rotten_apple", "rotten_banana", "rotten_bell_pepper", "rotten_bitter_gourd",
    "rotten_capsicum", "rotten_carrot", "rotten_cucumber", "rotten_mango",
    "rotten_okra", "rotten_orange", "rotten_potato", "rotten_strawberry", "rotten_tomato",
]

HINDI_NAMES = {
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

# ── SageMaker contract functions ─────────────────────────────────


def model_fn(model_dir: str) -> Any:
    """
    Load the ONNX model from the SageMaker model directory.

    SageMaker unpacks model.tar.gz into `model_dir`.
    We expect: model_dir/freshness_v1_best.onnx
    """
    import onnxruntime as ort

    onnx_path = os.path.join(model_dir, "freshness_v1_best.onnx")

    if not os.path.exists(onnx_path):
        # Try class_mapping.json to discover model name
        for f in os.listdir(model_dir):
            if f.endswith(".onnx"):
                onnx_path = os.path.join(model_dir, f)
                break

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = 4

    session = ort.InferenceSession(
        onnx_path,
        sess_options=sess_options,
        providers=["CPUExecutionProvider"],
    )

    print(f"✓ Loaded ONNX model from {onnx_path}")
    print(f"  Input:  {session.get_inputs()[0].name} → {session.get_inputs()[0].shape}")
    print(f"  Output: {session.get_outputs()[0].name} → {session.get_outputs()[0].shape}")

    return session


def input_fn(request_body: bytes, content_type: str) -> np.ndarray:
    """
    Deserialize and preprocess the incoming request.

    Supports:
        - image/jpeg, image/png  → raw image bytes
        - application/json       → {"image": "<base64>"} or {"image_url": "..."}
        - application/x-npy      → pre-processed numpy array
    """
    if content_type in ("image/jpeg", "image/png", "image/webp"):
        return _preprocess_image_bytes(request_body)

    elif content_type == "application/json":
        payload = json.loads(request_body)
        if "image" in payload:
            img_bytes = base64.b64decode(payload["image"])
            return _preprocess_image_bytes(img_bytes)
        else:
            raise ValueError("JSON payload must contain 'image' key with base64 data")

    elif content_type == "application/x-npy":
        return np.load(io.BytesIO(request_body))

    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data: np.ndarray, model: Any) -> Dict[str, Any]:
    """
    Run inference and return structured results.
    """
    start = time.time()

    input_name = model.get_inputs()[0].name
    logits = model.run(None, {input_name: input_data.astype(np.float32)})[0]

    # Softmax
    exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs = (exp_logits / np.sum(exp_logits, axis=1, keepdims=True))[0]

    # Top-5 predictions
    top_indices = np.argsort(probs)[::-1][:5]
    predicted_idx = top_indices[0]
    predicted_class = CLASS_NAMES[predicted_idx]
    confidence = float(probs[predicted_idx])

    # Parse
    freshness_status = "fresh" if predicted_class.startswith("fresh_") else "rotten"
    crop_type = predicted_class.split("_", 1)[1]

    # Quality metrics
    freshness_score, damage_score, ripeness = _compute_metrics(
        freshness_status, confidence, probs
    )
    quality_score = int(freshness_score * 0.5 + (100 - damage_score) * 0.3 + ripeness * 0.2)

    inference_ms = round((time.time() - start) * 1000, 1)

    crop_display = crop_type.replace("_", " ").title()
    hindi_label = HINDI_NAMES.get(predicted_class, "")

    # Plain-text summary for direct injection into a Bedrock prompt.
    # Keeps the LLM context concise and deterministic.
    bedrock_context = (
        f"Crop: {crop_display} ({hindi_label})\n"
        f"Freshness Status: {freshness_status.upper()}\n"
        f"Confidence: {round(confidence * 100, 1)}%\n"
        f"Quality Grade: {_grade(quality_score)} (score {quality_score}/100)\n"
        f"Freshness Score: {freshness_score}/100\n"
        f"Damage Score: {damage_score}/100\n"
        f"Ripeness Level: {ripeness}/100\n"
        f"Top alternative predictions: "
        + ", ".join(
            f"{CLASS_NAMES[i]} ({round(float(probs[i]) * 100, 1)}%)"
            for i in top_indices[1:3]
        )
    )

    return {
        "predicted_class": predicted_class,
        "freshness_status": freshness_status,
        "crop_type": crop_type,
        "hindi_label": hindi_label,
        "confidence": round(confidence, 4),
        "quality_score": quality_score,
        "freshness_score": freshness_score,
        "damage_score": damage_score,
        "ripeness_level": ripeness,
        "quality_grade": _grade(quality_score),
        "top_predictions": [
            {
                "class": CLASS_NAMES[i],
                "confidence": round(float(probs[i]), 4),
                "hindi": HINDI_NAMES.get(CLASS_NAMES[i], ""),
            }
            for i in top_indices
        ],
        "inference_time_ms": inference_ms,
        "bedrock_context": bedrock_context,
    }


def output_fn(prediction: Dict[str, Any], accept: str) -> Tuple[str, str]:
    """Serialize the prediction result to JSON."""
    return json.dumps(prediction, ensure_ascii=False), "application/json"


# ── Helpers ───────────────────────────────────────────────────────


def _preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Preprocess raw image bytes → model-ready numpy array (1, 3, 224, 224)."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((256, 256), Image.BILINEAR)
    left = (256 - IMAGE_SIZE) // 2
    top = (256 - IMAGE_SIZE) // 2
    image = image.crop((left, top, left + IMAGE_SIZE, top + IMAGE_SIZE))

    img_array = np.array(image, dtype=np.float32) / 255.0
    img_array = (img_array - IMAGENET_MEAN) / IMAGENET_STD
    img_array = np.transpose(img_array, (2, 0, 1))
    return np.expand_dims(img_array, axis=0)


def _compute_metrics(status: str, conf: float, probs: np.ndarray) -> Tuple[int, int, int]:
    """Derive freshness / damage / ripeness scores from model output."""
    fresh_sum = float(np.sum(probs[:13]))
    rotten_sum = float(np.sum(probs[13:]))

    if status == "fresh":
        freshness = int(70 + conf * 30)
        damage = int(max(0, (1 - conf) * 40 + rotten_sum * 30))
        ripeness = int(60 + conf * 35)
    else:
        freshness = int(max(5, (1 - conf) * 55))
        damage = int(min(100, 40 + conf * 55))
        ripeness = int(max(10, 80 - conf * 60))

    return (
        min(100, max(0, freshness)),
        min(100, max(0, damage)),
        min(100, max(0, ripeness)),
    )


def _grade(score: int) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"