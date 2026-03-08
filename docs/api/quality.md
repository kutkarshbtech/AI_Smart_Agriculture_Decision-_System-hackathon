# Quality Assessment API

**Prefix:** `/api/v1/quality`

Image-based produce quality analysis using a custom MobileNetV2 freshness detection model. Falls back to Amazon Rekognition → simulation when the model is unavailable. Includes an integrated quality → price recommendation pipeline.

---

## `GET /api/v1/quality/model-status`

Check which freshness detection model is loaded.

### Response

```json
{
  "model_type": "onnx",
  "supported_crops": ["tomato", "mango", "banana", "apple", "potato", "capsicum"],
  "model_path": "ml/models/freshness_model.onnx"
}
```

---

## `POST /api/v1/quality/assess/{batch_id}`

Upload a produce image and get AI quality/freshness assessment for an existing batch.

### Parameters

| Parameter | Location | Type | Description |
|-----------|----------|------|-------------|
| `batch_id` | path | int | Produce batch ID |

### Request

`multipart/form-data` with field `file` (JPEG/PNG, max 10MB)

### Response

```json
{
  "batch_id": 1,
  "crop_name": "Tomato",
  "freshness_status": "fresh",
  "freshness_confidence": 0.89,
  "overall_grade": "good",
  "quality_score": 72,
  "damage_detected": false,
  "recommendations": {
    "en": "Good quality produce. Sell within 3-4 days for best returns.",
    "hi": "अच्छी गुणवत्ता। बेहतर रिटर्न के लिए 3-4 दिन में बेचें।"
  },
  "model_used": "onnx_mobilenetv2"
}
```

---

## `POST /api/v1/quality/assess-standalone`

Quick quality check without registering a batch. Just upload a photo and crop name.

### Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `crop_name` | query | string | ✅ | e.g., `tomato`, `mango`, `apple` |

### Request

`multipart/form-data` with field `file` (JPEG/PNG, max 10MB)

```bash
curl -X POST "/api/v1/quality/assess-standalone?crop_name=tomato" \
  -F "file=@tomato.jpg"
```

---

## `POST /api/v1/quality/assess-and-price` ⭐

**Standalone integrated pipeline** — the most commonly used endpoint in the React frontend.

Upload a photo + crop name → freshness detection → mandi-grounded price recommendation. No batch required.

### Parameters

| Parameter | Location | Type | Required | Default | Description |
|-----------|----------|------|----------|---------|-------------|
| `crop_name` | query | string | ✅ | — | Crop name |
| `quantity_kg` | query | float | ❌ | 100 | Quantity in kg |
| `storage_type` | query | string | ❌ | `ambient` | `ambient`, `cold`, `controlled` |
| `state` | query | string | ❌ | — | State for mandi price lookup |

### Request

`multipart/form-data` with field `file` (JPEG/PNG, max 10MB)

```bash
curl -X POST "/api/v1/quality/assess-and-price?crop_name=tomato&quantity_kg=100&storage_type=ambient" \
  -F "file=@tomato.jpg"
```

### Response

```json
{
  "crop_name": "tomato",
  "quantity_kg": 100,
  "quality_assessment": {
    "freshness_status": "fresh",
    "freshness_confidence": 0.89,
    "overall_grade": "good",
    "quality_score": 72,
    "damage_detected": false,
    "recommendations": {
      "en": "Good quality produce...",
      "hi": "अच्छी गुणवत्ता..."
    }
  },
  "price_recommendation": {
    "ideal_price": 28.5,
    "recommended_min_price": 24.2,
    "recommended_max_price": 32.8,
    "floor_price": 19.95,
    "sellable": true,
    "action": "sell_now",
    "recommendation_text": "Good quality tomatoes — sell within 2-3 days...",
    "quality_based_note": "Good quality produce. Based on live mandi data, recommended price is ₹28.5/kg.",
    "price_source": "data.gov.in"
  },
  "mandi_prices": {
    "records": [...],
    "total_mandis": 5,
    "source": "data.gov.in"
  },
  "created_at": "2026-03-08T12:00:00+00:00"
}
```

---

## `POST /api/v1/quality/assess-and-price/{batch_id}`

Same integrated pipeline but linked to an existing batch. Updates the batch with quality data.

---

## `GET /api/v1/quality/simulate/{crop_name}`

Simulated quality assessment (no image upload needed). Useful for demos.

```
GET /api/v1/quality/simulate/tomato
```

---

## `GET /api/v1/quality/simulate-and-price/{crop_name}`

Simulated quality → price recommendation pipeline (no image needed).

### Parameters

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `crop_name` | path | string | — | Crop name |
| `quantity_kg` | query | float | 100 | Quantity |
| `storage_type` | query | string | `ambient` | Storage type |
| `state` | query | string | — | State for mandi prices |

```
GET /api/v1/quality/simulate-and-price/mango?quantity_kg=200&state=Maharashtra
```
