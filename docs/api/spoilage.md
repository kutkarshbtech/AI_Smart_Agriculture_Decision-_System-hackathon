# Spoilage Prediction API

**Prefix:** `/api/v1/spoilage`

Predicts spoilage risk using a Q10 temperature-based degradation model with humidity, transport damage, and sigmoid decay curves.

---

## `POST /api/v1/spoilage/assess`

Assess spoilage risk for an existing produce batch.

### Request Body

```json
{
  "batch_id": 1,
  "current_temp": 32,
  "current_humidity": 75,
  "transport_hours": 4
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batch_id` | int | ✅ | Produce batch ID |
| `current_temp` | float | ❌ | Current temperature (°C). Auto-fetched from weather if location available |
| `current_humidity` | float | ❌ | Current humidity (%). Auto-fetched if location available |
| `transport_hours` | float | ❌ | Hours in transit (default: 0) |

### Response

```json
{
  "batch_id": 1,
  "crop_name": "Tomato",
  "spoilage_risk": "high",
  "spoilage_probability": 0.72,
  "estimated_shelf_life_days": 2,
  "days_since_harvest": 3,
  "risk_factors": [
    "Temperature 32°C is 17°C above optimal for Tomato",
    "Humidity 75% accelerates fungal growth",
    "4 hours of transport causes mechanical damage"
  ],
  "recommendations": [
    "Move to cold storage immediately",
    "Sell within 24 hours if cold storage unavailable",
    "Consider processing into paste/sauce"
  ],
  "causal_explanations": {
    "temperature_impact": "Each 10°C above optimal doubles decay rate (Q10 rule)",
    "humidity_impact": "High humidity promotes microbial growth"
  },
  "weather_context": {
    "current_temp": 32,
    "current_humidity": 75,
    "weather_risk": "high",
    "advisory": "High temperature today accelerating spoilage"
  }
}
```

### Risk Levels

| Level | Probability | Action |
|-------|-------------|--------|
| `low` | 0–30% | Store normally |
| `medium` | 30–60% | Monitor closely |
| `high` | 60–80% | Sell soon |
| `critical` | 80–100% | Sell immediately |

---

## `GET /api/v1/spoilage/batch/{batch_id}`

Get current spoilage status of a batch without updating sensor data.

```
GET /api/v1/spoilage/batch/1
```

---

## `GET /api/v1/spoilage/weather-impact`

Check how current weather affects spoilage for a specific crop at a location.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `crop_name` | string | ✅ | Crop name |
| `lat` | float | ✅ | Latitude |
| `lng` | float | ✅ | Longitude |

```
GET /api/v1/spoilage/weather-impact?crop_name=tomato&lat=18.52&lng=73.86
```

### Response

```json
{
  "crop_name": "tomato",
  "current_temp": 32,
  "current_humidity": 75,
  "optimal_temp_range": "10-15°C",
  "weather_risk": "high",
  "impact_summary": "Temperature is 17°C above optimal — accelerated spoilage expected",
  "advisory": "Move produce to cold storage or sell within 24 hours"
}
```
