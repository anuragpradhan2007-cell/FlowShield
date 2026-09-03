# FlowShield Authentication API (Member 1)

Base URL: `/api/v1`

## 1. Register Worker
`POST /auth/register`

Creates a new user and an associated worker profile.

**Request Body:**
```json
{
  "email": "worker@example.com",
  "password": "strong-password",
  "occupation": "delivery_worker"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid-of-user",
  "role": "worker",
  "worker": {
    "id": "uuid-of-worker",
    "occupation": "delivery_worker"
  }
}
```
**Errors:**
- `409 Conflict`: Email already exists.
- `400 Bad Request`: Validation errors.

---

## 2. Login Worker
`POST /auth/login`

Authenticates a worker and returns a JWT access token.

**Request Body:**
```json
{
  "email": "worker@example.com",
  "password": "strong-password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5c...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-of-user",
    "role": "worker"
  }
}
```
**Errors:**
- `401 Unauthorized`: Invalid credentials.

---

## 3. Get Current Worker Profile
`GET /me`

Requires `Authorization: Bearer <JWT>` header.
Retrieves the logged-in worker's full profile.

**Response (200 OK):**
```json
{
  "id": "uuid-of-user",
  "email": "worker@example.com",
  "role": "worker",
  "ai_consent": true,
  "consent_version": "v1",
  "worker": {
    "id": "uuid-of-worker",
    "occupation": "delivery_worker"
  }
}
```
**Errors:**
- `401 Unauthorized`: Missing or invalid token.

---

## 4. Get Worker by ID
`GET /workers/{worker_id}`

Requires `Authorization: Bearer <JWT>` header.
Workers can only fetch their own profile.

**Response (200 OK):**
```json
{
  "id": "uuid-of-worker",
  "user_id": "uuid-of-user",
  "occupation": "delivery_worker",
  "created_at": "2023-10-01T12:00:00",
  "updated_at": "2023-10-01T12:00:00"
}
```
**Errors:**
- `401 Unauthorized`: Missing or invalid token.
- `403 Forbidden`: Worker attempting to access another worker's profile.
- `404 Not Found`: Worker profile does not exist.
