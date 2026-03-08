# Pricing Intelligence API

**Prefix:** `/api/v1/pricing`

Market intelligence, AI-powered price recommendations, forecasts, what-if analysis, and live mandi prices from [data.gov.in](https://data.gov.in).

---

## Market Prices

### `GET /api/v1/pricing/market/{crop_name}`

Get recent market prices for a crop.

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `crop_name` | path | string | — | Crop name (e.g., `tomato`) |
| `days` | query | int | 7 | Number of days of price history |

### Response

```json
{
  "crop_name": "tomato",
  "mandi_name": "Azadpur",
  "prices": [
    {
      "date": "2026-03-07",
      "mandi_name": "Azadpur",
      "min_price": 18.0,
      "max_price": 32.0,
      "modal_price": 25.0
    }
  ],
  "trend": "rising",
  "avg_price_7d": 24.5
}
```

---

## Price Recommendations

### `GET /api/v1/pricing/recommend/{batch_id}`

AI-powered price recommendation for an existing batch. Uses XGBoost model with quality, spoilage, and market factors.

### `POST /api/v1/pricing/recommend`

Direct price recommendation without a batch.

#### Request Body

```json
{
  "crop_name": "tomato",
  "quantity_kg": 200,
  "quality_grade": "good",
  "spoilage_risk": "medium",
  "remaining_shelf_life_days": 4,
  "harvest_date": "2026-03-05",
  "storage_type": "ambient",
  "storage_temp": 28,
  "storage_humidity": 65,
  "farmer_location_lat": 18.52,
  "farmer_location_lng": 73.86
}
```

#### Response

```json
{
  "crop_name": "tomato",
  "quantity_kg": 200,
  "ideal_price": 28.5,
  "recommended_min_price": 24.2,
  "recommended_max_price": 32.8,
  "floor_price": 19.95,
  "sellable": true,
  "action": "sell_now",
  "recommendation_text": "Market prices are good. Sell now for ₹28.5/kg.",
  "confidence_score": 0.82,
  "price_source": "data.gov.in",
  "factors": {
    "quality_factor": 0.9,
    "freshness_factor": 0.85,
    "market_trend_factor": 1.05,
    "seasonal_factor": 1.02
  }
}
```

> **Floor price protection:** The API never recommends a price below 70% of market rate or government MSP.

---

## Price Forecasts

### `GET /api/v1/pricing/forecast/{crop_name}`

Price forecast for the next N days using trend extrapolation.

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `crop_name` | path | string | — | Crop name |
| `days_ahead` | query | int | 3 | 1–7 days |

### `GET /api/v1/pricing/weather-forecast/{crop_name}` ⭐

Weather-aware price & crop health forecast. Uses OpenWeatherMap 5-day forecast to predict how weather affects crop health, spoilage, and prices.

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `crop_name` | path | string | — | Crop name |
| `days_ahead` | query | int | 5 | 1–5 days |
| `city` | query | string | `Delhi` | City for weather data |
| `quality_grade` | query | string | — | Current quality grade |
| `storage_type` | query | string | `ambient` | Storage type |
| `harvest_days_ago` | query | int | 1 | Days since harvest |

```
GET /api/v1/pricing/weather-forecast/tomato?city=Mumbai&quality_grade=good&storage_type=cold
```

---

## Trends

### `GET /api/v1/pricing/trends/{crop_name}`

14-day price trend analysis with 7-day and 14-day moving averages.

---

## Feature Importance

### `GET /api/v1/pricing/feature-importance`

Get the ML model's feature importances. Shows which factors most affect price predictions.

---

## Live Mandi Prices (data.gov.in)

### `GET /api/v1/pricing/mandi/prices/{commodity}`

Fetch live daily mandi prices from the government data.gov.in API.

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `commodity` | path | string | — | Crop name (e.g., `tomato`) |
| `state` | query | string | — | Filter by state |
| `district` | query | string | — | Filter by district |
| `market` | query | string | — | Filter by market name |
| `limit` | query | int | 30 | Max records |

```
GET /api/v1/pricing/mandi/prices/onion?state=Maharashtra
GET /api/v1/pricing/mandi/prices/potato?state=Uttar+Pradesh&market=Agra
```

### Response

```json
{
  "commodity": "tomato",
  "records": [
    {
      "state": "Maharashtra",
      "district": "Pune",
      "market": "Pune",
      "commodity": "Tomato",
      "variety": "Other",
      "arrival_date": "08/03/2026",
      "min_price": 1200,
      "max_price": 2800,
      "modal_price": 2000,
      "min_price_per_kg": 12.0,
      "max_price_per_kg": 28.0,
      "modal_price_per_kg": 20.0
    }
  ],
  "total": 15,
  "source": "data.gov.in"
}
```

> Prices from data.gov.in are in ₹/quintal. The API normalizes them to ₹/kg automatically.

---

### `GET /api/v1/pricing/mandi/summary/{commodity}`

Aggregated price summary across mandis. Returns avg, min, max, median price in ₹/kg.

```
GET /api/v1/pricing/mandi/summary/tomato
GET /api/v1/pricing/mandi/summary/onion?state=Maharashtra
```

---

### `GET /api/v1/pricing/mandi/compare/{commodity}` ⭐

Cross-state mandi price comparison. Pass states as comma-separated.

| Parameter | Location | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `commodity` | path | string | — | Crop name |
| `states` | query | string | — | Comma-separated states |
| `limit_per_state` | query | int | 10 | Max mandis per state |

```
GET /api/v1/pricing/mandi/compare/tomato?states=Maharashtra,Karnataka,Andhra+Pradesh
```

### Response

```json
{
  "commodity": "tomato",
  "states_compared": ["Maharashtra", "Karnataka", "Andhra Pradesh"],
  "state_summaries": [
    {
      "state": "Maharashtra",
      "num_mandis": 8,
      "avg_price_per_kg": 22.5,
      "min_price_per_kg": 15.0,
      "max_price_per_kg": 32.0,
      "markets": [
        { "market": "Pune", "modal_price_per_kg": 28.0 },
        { "market": "Mumbai", "modal_price_per_kg": 25.0 }
      ]
    }
  ],
  "best_market": {
    "market": "Pune",
    "state": "Maharashtra",
    "modal_price_per_kg": 32.0
  }
}
```
