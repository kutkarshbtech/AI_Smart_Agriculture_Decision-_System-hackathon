# Logistics API

**Prefix:** `/api/v1/logistics`

Transport vehicle recommendations, cost estimation, and logistics provider matching. Recommends the right vehicle based on distance, quantity, crop type, and urgency.

---

## `GET /api/v1/logistics/recommend`

Get optimal vehicle recommendation for a transport job.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `distance_km` | float | ✅ | — | Distance in km |
| `quantity_kg` | float | ✅ | — | Quantity in kg |
| `crop_name` | string | ❌ | `tomato` | Crop name |
| `urgency` | string | ❌ | `medium` | `low`, `medium`, `high` |

```
GET /api/v1/logistics/recommend?distance_km=150&quantity_kg=500&crop_name=tomato&urgency=high
```

### Response

```json
{
  "success": true,
  "recommended_vehicle": {
    "type": "mini_truck",
    "name": "Tata Ace / Ashok Leyland Dost",
    "capacity_kg": 750,
    "utilization_pct": 66.7
  },
  "cost_estimate": {
    "total_cost": 3500,
    "cost_per_kg": 7.0,
    "fuel_cost": 2100,
    "driver_cost": 800,
    "loading_cost": 600
  },
  "estimated_time": {
    "hours": 4.5,
    "arrival_by": "2026-03-08T16:30:00"
  },
  "notes": "High urgency — prioritize refrigerated vehicle if available"
}
```

---

## `GET /api/v1/logistics/providers`

Find logistics providers for a specific vehicle type and route.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vehicle_type` | string | `mini_truck` | Vehicle type ID |
| `source_state` | string | `Maharashtra` | Origin state |
| `destination_state` | string | `Karnataka` | Destination state |
| `min_rating` | float | 3.5 | Minimum provider rating (1–5) |

```
GET /api/v1/logistics/providers?vehicle_type=truck&source_state=Maharashtra&destination_state=Karnataka
```

### Response

```json
{
  "success": true,
  "providers": [
    {
      "id": 1,
      "name": "FastTrack Logistics",
      "rating": 4.5,
      "vehicle_types": ["mini_truck", "truck"],
      "operating_states": ["Maharashtra", "Karnataka", "Goa"],
      "contact": "+919876543210",
      "price_per_km": 18.0,
      "cold_chain_available": true
    }
  ],
  "total": 3
}
```

---

## `GET /api/v1/logistics/complete`

Complete logistics recommendation: vehicle + providers + cost breakdown for a specific route.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `seller_location` | string | ✅ | e.g., `Pune, Maharashtra` |
| `buyer_location` | string | ✅ | e.g., `Mumbai, Maharashtra` |
| `distance_km` | float | ✅ | Distance in km |
| `quantity_kg` | float | ✅ | Quantity in kg |
| `crop_name` | string | ❌ | Crop name (default: `tomato`) |
| `urgency` | string | ❌ | `low`, `medium`, `high` (default: `medium`) |

```
GET /api/v1/logistics/complete?seller_location=Pune,Maharashtra&buyer_location=Mumbai,Maharashtra&distance_km=150&quantity_kg=500&crop_name=tomato&urgency=high
```
