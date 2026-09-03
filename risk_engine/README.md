# Worker Stability & Risk Scoring Engine (Member 3)

A production-ready FastAPI scoring service with SQLAlchemy models and Pydantic validation contracts designed for Supabase (PostgreSQL) and gig-worker stability assessment.

---

## 🚀 Quickstart

### 1. Configure Supabase Connection
Copy `.env.example` to `.env` and provide your Supabase database connection URL:

```env
# Direct Supabase Connection (Port 5432)
DATABASE_URL=postgresql+psycopg2://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Or Supabase Transaction Pooler (Port 6543)
# DATABASE_URL=postgresql+psycopg2://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```
*(If left unset, the engine automatically defaults to local SQLite for offline development and testing).*

### 2. Run Database Schema on Supabase
You can let SQLAlchemy auto-create tables on startup, or paste [`supabase_schema.sql`](file:///C:/Users/DELL/.gemini/antigravity/scratch/worker_risk_engine/supabase_schema.sql) directly into the **Supabase Dashboard -> SQL Editor**.

### 3. Start the FastAPI Server
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Run Unit & Contract Tests
```powershell
python -m pytest tests/ -v
```

---

## 🗄️ Database Schema (`risk_scores`)

| Column | Type | Constraints / Description |
|---|---|---|
| `id` | `UUID` | Primary Key, auto-generated default |
| `worker_id` | `UUID` | Anonymous UUID referencing Member 1's worker schema, indexed |
| `stability_score` | `FLOAT` | Check constraint: strictly `0.0 <= stability_score <= 100.0` |
| `risk_tier` | `ENUM` | Enum: `'Stable'`, `'At Risk'`, `'Critical'` |
| `metrics_breakdown` | `JSONB` / `JSON` | Intermediate feature values, weights, and frontend tooltips |
| `created_at` | `TIMESTAMPTZ` | Timestamp in UTC, indexed with `worker_id` |

---

## 🛡️ Pydantic Contracts

- `RiskTier`: String Enum (`"Stable"`, `"At Risk"`, `"Critical"`).
- `stability_score`: Strictly bounded float `[0.0, 100.0]`. Out-of-bounds numbers trigger a `422 Unprocessable Entity`.
- `MetricsBreakdown`: Structured breakdown schema with sub-scores, weights, and Member 5 tooltip metadata.
