# Produce Management API

**Prefix:** `/api/v1/produce`

CRUD operations for crop batches, image upload, and listing. Supports 16 Indian crops with bilingual names (Hindi + English).

---

## `GET /api/v1/produce/crop-types`

List all 16 supported crop types with metadata.

### Response

```json
[
  {
    "id": 1,
    "name_en": "Tomato",
    "name_hi": "टमाटर",
    "category": "vegetable",
    "avg_shelf_life_days": 7,
    "optimal_temp_min": 10,
    "optimal_temp_max": 15
  },
  {
    "id": 4,
    "name_en": "Banana",
    "name_hi": "केला",
    "category": "fruit",
    "avg_shelf_life_days": 5,
    "optimal_temp_min": 13,
    "optimal_temp_max": 15
  }
]
```

---

## `POST /api/v1/produce/batches`

Register a new produce batch.

### Request Body

```json
{
  "farmer_id": 1,
  "crop_type_id": 1,
  "quantity_kg": 250,
  "harvest_date": "2026-03-06",
  "storage_type": "ambient",
  "storage_temp": 28,
  "storage_humidity": 65,
  "location_lat": 18.52,
  "location_lng": 73.86,
  "notes": "Fresh tomato harvest from Pune farm"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `farmer_id` | int | ✅ | Farmer's user ID |
| `crop_type_id` | int | ✅ | Crop type ID (1–16) |
| `quantity_kg` | float | ✅ | Quantity in kg |
| `harvest_date` | string | ✅ | ISO date (YYYY-MM-DD) |
| `storage_type` | string | ❌ | `ambient`, `cold_storage`, `controlled` |
| `storage_temp` | float | ❌ | Storage temperature (°C) |
| `storage_humidity` | float | ❌ | Storage humidity (%) |
| `location_lat` | float | ❌ | GPS latitude |
| `location_lng` | float | ❌ | GPS longitude |
| `notes` | string | ❌ | Freeform notes |

### Response (201)

```json
{
  "id": 1,
  "farmer_id": 1,
  "crop_name": "Tomato",
  "quantity_kg": 250,
  "harvest_date": "2026-03-06",
  "storage_type": "ambient",
  "quality_grade": null,
  "quality_score": null,
  "spoilage_risk": null,
  "is_sold": false,
  "created_at": "2026-03-08T12:00:00"
}
```

---

## `GET /api/v1/produce/batches/{farmer_id}`

Get all batches for a farmer.

```
GET /api/v1/produce/batches/1
```

### Response

```json
{
  "farmer_id": 1,
  "batches": [...],
  "total": 5,
  "active": 4,
  "sold": 1
}
```

---

## `PUT /api/v1/produce/batches/{batch_id}`

Update a batch (e.g., mark as sold, update storage conditions).

### Request Body (partial update)

```json
{
  "is_sold": true,
  "storage_temp": 12,
  "storage_humidity": 85,
  "notes": "Sold to Mumbai retailer at ₹28/kg"
}
```

---

## `POST /api/v1/produce/batches/{batch_id}/image`

Upload a produce photo for a batch. Triggers automatic quality assessment.

### Request

`multipart/form-data` with field `file` (JPEG/PNG, max 10MB)

---

## Demo Data

On server startup, 8 demo batches are pre-populated for `farmer_id=1` and `farmer_id=2` covering Tomato, Banana, Potato, Onion, Cauliflower, Mango, and Capsicum with varying quality grades and spoilage risk levels. This ensures the dashboard and other endpoints work immediately in a demo environment.
