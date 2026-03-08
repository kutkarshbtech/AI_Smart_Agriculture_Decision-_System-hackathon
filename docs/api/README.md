# SwadeshAI API Documentation

> **Base URL (Production):** `https://dw5xgq7c3nm84.cloudfront.net`  
> **Base URL (ALB Direct):** `http://swadesh-ai-alb-dev-426896629.ap-south-1.elb.amazonaws.com`  
> **Base URL (Local Dev):** `http://localhost:8000`  
> **Swagger Docs:** `{BASE_URL}/docs`

---

## API Modules

| Module | Prefix | Documentation |
|--------|--------|---------------|
| [Health](health.md) | `/health` | Server status check |
| [Authentication](authentication.md) | `/api/auth` | OTP login, registration, profile |
| [Produce](produce.md) | `/api/v1/produce` | Crop batch CRUD, 16 supported crops |
| [Quality Assessment](quality.md) | `/api/v1/quality` | Image-based freshness grading + pricing |
| [Pricing Intelligence](pricing.md) | `/api/v1/pricing` | Mandi prices, forecasts, recommendations |
| [Spoilage Prediction](spoilage.md) | `/api/v1/spoilage` | Risk assessment, weather impact |
| [Causal Inference](causal.md) | `/api/v1/causal` | DoWhy causal analysis |
| [Buyer Matching](buyers.md) | `/api/v1/buyers` | Find buyers, negotiation, offers |
| [AI Chatbot](chatbot.md) | `/api/v1/chatbot` | Text & voice chat in 9 languages |
| [Text-to-Speech](tts.md) | `/api/v1/tts` | Amazon Polly audio synthesis |
| [Weather](weather.md) | `/api/v1/weather` | Current weather & forecasts |
| [Logistics](logistics.md) | `/api/v1/logistics` | Vehicle recommendations, providers |
| [Alerts](alerts.md) | `/api/v1/alerts` | Spoilage & price notifications |
| [Dashboard](dashboard.md) | `/api/v1/dashboard` | Farmer summary & action items |

---

## Authentication

Most endpoints work without authentication for hackathon demo purposes. For protected endpoints, pass the JWT token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token via the [Authentication API](authentication.md).

---

## Common Response Patterns

### Success
```json
{
  "success": true,
  "data": { ... }
}
```

### Error
```json
{
  "detail": "Error message"
}
```

HTTP status codes follow standard REST conventions:
- `200` — Success
- `400` — Bad request / validation error
- `401` — Unauthorized
- `404` — Resource not found
- `502` — Upstream service error (e.g., mandi API down)

---

## Supported Crops (16)

| ID | English | Hindi | Category | Shelf Life (days) | Optimal Temp (°C) |
|----|---------|-------|----------|-------------------|--------------------|
| 1 | Tomato | टमाटर | Vegetable | 7 | 10–15 |
| 2 | Potato | आलू | Vegetable | 30 | 4–8 |
| 3 | Onion | प्याज | Vegetable | 30 | 0–4 |
| 4 | Banana | केला | Fruit | 5 | 13–15 |
| 5 | Mango | आम | Fruit | 5 | 10–13 |
| 6 | Apple | सेब | Fruit | 14 | 0–4 |
| 7 | Rice | चावल | Grain | 365 | 15–20 |
| 8 | Wheat | गेहूं | Grain | 180 | 15–20 |
| 9 | Cauliflower | फूलगोभी | Vegetable | 4 | 0–2 |
| 10 | Spinach | पालक | Vegetable | 2 | 0–2 |
| 11 | Capsicum | शिमला मिर्च | Vegetable | 5 | 7–10 |
| 12 | Okra | भिंडी | Vegetable | 3 | 7–10 |
| 13 | Brinjal | बैंगन | Vegetable | 5 | 10–12 |
| 14 | Guava | अमरूद | Fruit | 5 | 8–10 |
| 15 | Grape | अंगूर | Fruit | 3 | -1–0 |
| 16 | Carrot | गाजर | Vegetable | 7 | 0–2 |
