# Dashboard API

**Prefix:** `/api/v1/dashboard`

Aggregated farmer view for decision-making. Provides summary metrics and prioritized action recommendations.

---

## `GET /api/v1/dashboard/summary/{farmer_id}`

Get a complete dashboard summary for a farmer.

| Parameter | Type | Description |
|-----------|------|-------------|
| `farmer_id` | int | Farmer/user ID (default: 1) |

```
GET /api/v1/dashboard/summary/1
```

### Response

```json
{
  "total_batches": 6,
  "active_batches": 5,
  "sold_batches": 1,
  "total_quantity_kg": 2130,
  "estimated_value": null,
  "avg_quality_score": 65.2,
  "high_risk_batches": 2,
  "pending_alerts": 3,
  "top_recommendation": "⚠️ 2 batch(es) at high spoilage risk. Sell Cauliflower (80 kg) immediately."
}
```

---

## `GET /api/v1/dashboard/actions/{farmer_id}`

Get personalized action recommendations. Returns three simple decisions per batch: what to sell, where, and at what price. Sorted by urgency (critical/high risk first).

| Parameter | Type | Description |
|-----------|------|-------------|
| `farmer_id` | int | Farmer/user ID (default: 1) |

```
GET /api/v1/dashboard/actions/1
```

### Response

```json
{
  "farmer_id": 1,
  "actions": [
    {
      "batch_id": 5,
      "crop_name": "Cauliflower",
      "quantity_kg": 80,
      "action": "sell_immediately",
      "recommended_price_range": {
        "min": 18.0,
        "max": 24.0
      },
      "spoilage_risk": "critical",
      "reason": "Critical spoilage risk — quality deteriorating rapidly. Sell today at any reasonable price."
    },
    {
      "batch_id": 4,
      "crop_name": "Onion",
      "quantity_kg": 300,
      "action": "sell_now",
      "recommended_price_range": {
        "min": 22.0,
        "max": 30.0
      },
      "spoilage_risk": "high",
      "reason": "High spoilage risk. Sell within 24 hours. Market price is ₹26/kg."
    },
    {
      "batch_id": 1,
      "crop_name": "Tomato",
      "quantity_kg": 250,
      "action": "sell_soon",
      "recommended_price_range": {
        "min": 24.0,
        "max": 32.0
      },
      "spoilage_risk": "medium",
      "reason": "Medium risk — sell within 2-3 days for best returns."
    }
  ],
  "total": 5
}
```
