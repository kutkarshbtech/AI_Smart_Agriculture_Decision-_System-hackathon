# Buyer Matching API

**Prefix:** `/api/v1/buyers`

Find verified buyers near a farmer, view active demands, create sell offers, and manage negotiations. Uses multi-factor scoring (distance, rating, capacity, payment speed, demand urgency, reliability).

---

## Matching

### `POST /api/v1/buyers/match`

Find and rank buyers for an existing batch.

#### Request Body

```json
{
  "batch_id": 1,
  "farmer_lat": 18.52,
  "farmer_lng": 73.86,
  "max_distance_km": 100,
  "buyer_type": "wholesaler",
  "min_rating": 4.0,
  "sort_by": "score"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `batch_id` | int | ✅ | — | Produce batch ID |
| `farmer_lat` | float | ✅ | — | Farmer's latitude |
| `farmer_lng` | float | ✅ | — | Farmer's longitude |
| `max_distance_km` | float | ❌ | 100 | Search radius |
| `buyer_type` | string | ❌ | — | `retailer`, `wholesaler`, `aggregator` |
| `min_rating` | float | ❌ | — | Minimum buyer rating |
| `sort_by` | string | ❌ | `score` | `score`, `distance`, `rating` |

### `GET /api/v1/buyers/nearby`

Find buyers without a batch (standalone).

```
GET /api/v1/buyers/nearby?crop_name=tomato&lat=18.52&lng=73.86&quantity_kg=200&max_distance_km=50
```

### Response

```json
{
  "crop_name": "tomato",
  "matched_buyers": [
    {
      "buyer_id": 1,
      "name": "Fresh Mart",
      "buyer_type": "retailer",
      "distance_km": 12.5,
      "rating": 4.5,
      "composite_score": 0.87,
      "demand_quantity_kg": 500,
      "offered_price_per_kg": 26.0,
      "payment_terms": "cash_on_delivery",
      "contact": "+919876543210"
    }
  ],
  "total_matches": 5
}
```

---

## Active Demands

### `GET /api/v1/buyers/demands`

View what buyers are currently looking for.

| Parameter | Type | Description |
|-----------|------|-------------|
| `crop_name` | string | Filter by crop |
| `lat` | float | Farmer latitude |
| `lng` | float | Farmer longitude |
| `max_distance_km` | float | Search radius (default: 100) |

```
GET /api/v1/buyers/demands?crop_name=mango&lat=19.08&lng=72.88
```

---

## Offers & Negotiation

### `POST /api/v1/buyers/offers`

Send a sell offer from a farmer to a buyer.

#### Request Body

```json
{
  "farmer_id": 1,
  "buyer_id": 3,
  "crop_name": "tomato",
  "quantity_kg": 200,
  "asking_price_per_kg": 28.0,
  "batch_id": 1,
  "notes": "Fresh harvest, grade A quality"
}
```

### `GET /api/v1/buyers/offers/{offer_id}`

Get details of a specific offer.

### `PUT /api/v1/buyers/offers/{offer_id}`

Update offer status: accept, reject, or counter-offer.

#### Request Body

```json
{
  "status": "counter_offer",
  "counter_price_per_kg": 25.0
}
```

| Status | Description |
|--------|-------------|
| `accepted` | Buyer accepts the offer |
| `rejected` | Buyer rejects the offer |
| `counter_offer` | Buyer proposes a different price |

### `GET /api/v1/buyers/offers`

List all offers for a farmer.

```
GET /api/v1/buyers/offers?farmer_id=1&status=pending
```
