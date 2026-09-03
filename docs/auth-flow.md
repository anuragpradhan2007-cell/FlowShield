# FlowShield Authentication Flow

This document describes the JSON Web Token (JWT) authentication flow for the FlowShield platform.

## 1. Login & Token Generation

1. The client (Member 5 Frontend) sends `email` and `password` to `POST /api/v1/auth/login`.
2. The server verifies the credentials against the hashed password in the `users` table.
3. Upon success, the server generates a JWT containing standard and custom claims.

### JWT Format

The JWT structure ensures no Personally Identifiable Information (PII) like name, email, or address is embedded in the token.

**Example Payload:**
```json
{
  "sub": "b2f6b8c9-4f7f-4131-bb6c-31b6e4e5cf42", // User UUID
  "role": "worker",
  "ai_consent_version": "v1",
  "worker_id": "83d4c389-1383-4318-ba98-a3f290d2681a", // Anonymous Worker UUID
  "exp": 1696172400 // Expiry timestamp
}
```

## 2. Securing Endpoints

For any protected route, the client must include the JWT in the `Authorization` header:

```http
Authorization: Bearer <JWT>
```

### Authentication Dependencies

The backend utilizes FastAPI dependencies to protect routes:

- `get_current_user()`: Validates the JWT, checks expiration, and ensures the user exists and is active.
- `require_worker()`: Built upon `get_current_user()`, specifically enforcing that the user has the `worker` role and resolving the associated `worker_id` for authorization context.

## 3. Authorization Checks

When accessing resources via identifiers (e.g., `/api/v1/workers/{worker_id}`), the server:
1. Extracts the `worker_id` from the JWT claims (or fetches it via the `user` relationship).
2. Compares the JWT's `worker_id` with the `{worker_id}` path parameter.
3. If they match, access is granted.
4. If they do not match, a `403 Forbidden` is returned.
