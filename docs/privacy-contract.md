# FlowShield Privacy Contract

This document outlines the strict identity separation and AI consent contract required to protect worker data, specifically for interactions with Member 3 (AI Engine).

## 1. The Anonymization Contract

### Internal Identity
The authentication module (Member 1) maintains the linkage between the user's login identity and their worker profile.
- `users` table: Contains `email`, `password_hash`, `ai_consent`, etc.
- `workers` table: Contains the public `worker_id` (UUID), `occupation`.

### AI Handoff
When data is sent to the AI Engine (Member 3) or requested by other modules for risk assessment, **ONLY** the `worker_id` is used.

**Allowed Payload to AI:**
```json
{
  "worker_id": "83d4c389-1383-4318-ba98-a3f290d2681a",
  "income_data": "...",
  "consent_version": "v1"
}
```

**STRICTLY PROHIBITED:**
The following fields must never be passed to the AI Engine or embedded in the JWT claims accessible to third-party services:
- `name`
- `email`
- `phone`
- `password` or `password_hash`
- `address`

## 2. AI Consent Contract

Worker consent for AI processing is explicitly tracked and versioned.

### Source of Truth
The `users` table is the definitive source of truth for:
- `ai_consent`: boolean (true/false)
- `consent_version`: string (e.g., "v1", "v2")

### JWT Representation
To minimize database lookups for microservices, the consent version is embedded in the JWT:
```json
{
  "ai_consent_version": "v1"
}
```

### Revocation
If a worker revokes consent (i.e., `ai_consent = false`):
1. The backend will update the database.
2. If Member 3 (AI Engine) attempts to process data for a `worker_id` where consent is `false`, it must immediately halt processing.
3. Any active JWTs may be invalidated or the consent version updated to signal revocation.
