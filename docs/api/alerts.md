# Alerts API

**Prefix:** `/api/v1/alerts`

Manage farmer notifications for spoilage warnings, price changes, and buyer events. Alerts are delivered via SMS (Amazon SNS) and in-app.

---

## `GET /api/v1/alerts/user/{user_id}`

Get all alerts for a user.

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | User ID |
| `unread_only` | bool | Only return unread alerts (default: `false`) |

```
GET /api/v1/alerts/user/1?unread_only=true
```

### Response

```json
{
  "alerts": [
    {
      "id": 1,
      "user_id": 1,
      "type": "spoilage_warning",
      "title": "⚠️ Spoilage Alert: Tomato",
      "message": "Your Tomato batch is at HIGH spoilage risk. Only 2 days remaining. Sell immediately!",
      "severity": "high",
      "crop_name": "Tomato",
      "batch_id": 1,
      "is_read": false,
      "created_at": "2026-03-08T10:00:00"
    }
  ],
  "total": 3,
  "unread_count": 2
}
```

---

## `POST /api/v1/alerts/{alert_id}/read`

Mark an alert as read.

```
POST /api/v1/alerts/1/read
```

### Response

```json
{
  "status": "ok"
}
```

---

## Test Endpoints (Demo)

### `POST /api/v1/alerts/test/spoilage`

Create a test spoilage alert for demo purposes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | int | 1 | User ID |
| `crop_name` | string | `Tomato` | Crop name |
| `risk_level` | string | `high` | `low`, `medium`, `high`, `critical` |
| `remaining_days` | int | 2 | Days remaining |
| `batch_id` | int | 1 | Batch ID |

```
POST /api/v1/alerts/test/spoilage?user_id=1&crop_name=tomato&risk_level=critical&remaining_days=1
```

### `POST /api/v1/alerts/test/price`

Create a test price alert.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | int | 1 | User ID |
| `crop_name` | string | `Onion` | Crop name |
| `trend` | string | `falling` | `rising` or `falling` |
| `current_price` | float | 18.5 | Current price in ₹/kg |
| `change_pct` | float | -8.5 | Percentage change |

```
POST /api/v1/alerts/test/price?crop_name=Onion&trend=rising&current_price=35&change_pct=12.5
```
