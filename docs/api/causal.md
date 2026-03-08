# Causal Inference API

**Prefix:** `/api/v1/causal`

Statistical causal analysis using the [DoWhy](https://github.com/py-why/dowhy) library. Answers "does X cause Y?" questions with Average Treatment Effect (ATE) estimates and refutation tests. These are proper causal inferences, not just correlations.

---

## `GET /api/v1/causal/storage-spoilage`

Analyze the causal effect of cold storage on spoilage rates.

**Question answered:** *"Does cold storage actually reduce spoilage?"*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `crop_name` | string | `tomato` | Crop name |
| `quality_grade` | string | `good` | Quality grade |

```
GET /api/v1/causal/storage-spoilage?crop_name=tomato&quality_grade=good
```

### Response

```json
{
  "success": true,
  "analysis": {
    "treatment": "cold_storage",
    "outcome": "spoilage_rate",
    "ate": -0.34,
    "ate_interpretation": "Cold storage reduces spoilage rate by 34 percentage points",
    "confidence_interval": [-0.42, -0.26],
    "p_value": 0.001,
    "refutation_tests": {
      "placebo_treatment": { "new_ate": 0.002, "passed": true },
      "random_common_cause": { "new_ate": -0.33, "passed": true }
    },
    "recommendation": "Cold storage is highly effective for tomatoes. Expected shelf life increase: 3-5 days."
  }
}
```

---

## `GET /api/v1/causal/weather-prices`

Analyze the causal effect of weather conditions on market prices.

**Question answered:** *"Does bad weather actually drive prices up?"*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `crop_name` | string | `tomato` | Crop name |
| `location` | string | `Lucknow` | Location for context |

```
GET /api/v1/causal/weather-prices?crop_name=onion&location=Delhi
```

### Response

```json
{
  "success": true,
  "analysis": {
    "treatment": "extreme_weather",
    "outcome": "price_change",
    "ate": 4.2,
    "ate_interpretation": "Extreme weather increases prices by ₹4.2/kg on average",
    "confidence_interval": [2.8, 5.6],
    "p_value": 0.003,
    "refutation_tests": {
      "placebo_treatment": { "new_ate": 0.1, "passed": true },
      "random_common_cause": { "new_ate": 4.1, "passed": true }
    }
  }
}
```

---

## `GET /api/v1/causal/quality-premium`

Analyze the causal effect of produce quality on price premium.

**Question answered:** *"Does better quality actually get higher prices?"*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `crop_name` | string | `tomato` | Crop name |

```
GET /api/v1/causal/quality-premium?crop_name=mango
```

### Response

```json
{
  "success": true,
  "analysis": {
    "treatment": "high_quality",
    "outcome": "price_premium",
    "ate": 6.8,
    "ate_interpretation": "High quality mangoes command ₹6.8/kg premium over average quality",
    "confidence_interval": [4.5, 9.1],
    "p_value": 0.0001,
    "refutation_tests": {
      "placebo_treatment": { "new_ate": 0.05, "passed": true },
      "random_common_cause": { "new_ate": 6.7, "passed": true }
    }
  }
}
```

---

## Error Handling

If the causal analysis fails (insufficient data, model convergence issues), the API returns a fallback response:

```json
{
  "success": false,
  "error": "Insufficient data for causal estimation",
  "message": "Causal analysis failed. Using fallback data."
}
```
