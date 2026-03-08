# Authentication API

**Prefix:** `/api/auth`

Mobile-number + OTP login system supporting three user types: **seller** (farmer), **buyer** (wholesaler/retailer), and **logistic** (transport provider).

---

## `POST /api/auth/register`

Register a new user.

### Request Body

```json
{
  "mobile_number": "+919876543210",
  "user_type": "seller",
  "name": "Ravi Kumar",
  "business_name": "Kumar Farms",
  "city": "Pune",
  "state": "Maharashtra",
  "pincode": "411001",
  "vehicle_types": ["mini_truck"],
  "operating_states": ["Maharashtra", "Karnataka"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mobile_number` | string | ✅ | With country code (e.g., `+919876543210`) |
| `user_type` | string | ✅ | `buyer`, `seller`, or `logistic` |
| `name` | string | ✅ | Full name |
| `business_name` | string | ❌ | For buyers/logistics providers |
| `city` | string | ❌ | City name |
| `state` | string | ❌ | State name |
| `pincode` | string | ❌ | PIN code |
| `vehicle_types` | string[] | ❌ | For logistics providers |
| `operating_states` | string[] | ❌ | For logistics providers |

### Response (200)

```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "mobile_number": "+919876543210",
    "user_type": "seller",
    "name": "Ravi Kumar"
  }
}
```

---

## `POST /api/auth/login/request-otp`

Request an OTP for login.

### Request Body

```json
{
  "mobile_number": "+919876543210",
  "user_type": "seller"
}
```

### Response (200)

```json
{
  "success": true,
  "message": "OTP sent successfully",
  "otp_sent": true,
  "demo_otp": "012033"
}
```

> **Note:** `demo_otp` is only included in demo mode. Remove in production.

---

## `POST /api/auth/login/verify-otp`

Verify OTP and receive a JWT access token.

### Request Body

```json
{
  "mobile_number": "+919876543210",
  "user_type": "seller",
  "otp": "012033"
}
```

### Response (200)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "user_type": "seller",
  "name": "Ravi Kumar",
  "mobile_number": "+919876543210"
}
```

---

## `GET /api/auth/profile`

Get current user's profile. Requires authentication.

### Headers

```
Authorization: Bearer <access_token>
```

### Response (200)

```json
{
  "id": 1,
  "mobile_number": "+919876543210",
  "user_type": "seller",
  "name": "Ravi Kumar",
  "business_name": "Kumar Farms",
  "city": "Pune",
  "state": "Maharashtra"
}
```

---

## `PUT /api/auth/profile`

Update current user's profile. Requires authentication.

### Headers

```
Authorization: Bearer <access_token>
```

### Request Body (partial update)

```json
{
  "name": "Ravi Kumar Jr",
  "city": "Mumbai"
}
```

---

## `POST /api/auth/logout`

Invalidate the current session token. Requires authentication.

### Headers

```
Authorization: Bearer <access_token>
```

---

## `GET /api/auth/users/{user_type}`

List all users of a specific type (admin/demo endpoint).

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_type` | path | `buyer`, `seller`, or `logistic` |

### Example

```
GET /api/auth/users/seller
```
