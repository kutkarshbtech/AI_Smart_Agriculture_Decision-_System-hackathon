# Weather API

**Prefix:** `/api/v1/weather`

Current weather and forecasts powered by OpenWeatherMap. Used across the platform for spoilage prediction, price forecasting, and agricultural advisories.

---

## `GET /api/v1/weather/current`

Get current weather for a GPS location.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | ✅ | Latitude |
| `longitude` | float | ✅ | Longitude |

```
GET /api/v1/weather/current?latitude=18.52&longitude=73.86
```

### Response

```json
{
  "temperature": 32,
  "humidity": 65,
  "pressure": 1012,
  "wind_speed": 3.5,
  "description": "partly cloudy",
  "icon": "02d",
  "city": "Pune",
  "country": "IN"
}
```

---

## `GET /api/v1/weather/city/{city}`

Get current weather by city name.

```
GET /api/v1/weather/city/Delhi
GET /api/v1/weather/city/Mumbai
```

---

## `GET /api/v1/weather/forecast`

Get multi-day weather forecast for a GPS location.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `latitude` | float | — | Latitude |
| `longitude` | float | — | Longitude |
| `days` | int | 5 | Number of days (1–7) |

```
GET /api/v1/weather/forecast?latitude=18.52&longitude=73.86&days=5
```

---

## `GET /api/v1/weather/forecast/city/{city}`

Get multi-day weather forecast by city name with agricultural advisories.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `city` | path | — | City name |
| `days` | query | 5 | Number of days (1–7) |

```
GET /api/v1/weather/forecast/city/Hyderabad?days=5
```

### Response

```json
[
  {
    "date": "2026-03-09",
    "temp_min": 24,
    "temp_max": 36,
    "humidity": 55,
    "description": "clear sky",
    "wind_speed": 4.2,
    "rain_probability": 0.1,
    "agricultural_advisory": "High temperatures expected. Irrigate early morning or late evening."
  }
]
```
