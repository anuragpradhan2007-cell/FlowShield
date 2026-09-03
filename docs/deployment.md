# FlowShield Deployment Guide

This document outlines the deployment process for the FlowShield integrated application.

## 1. Environment Variables

### Backend (`backend/.env`)
Set these in your hosting provider (e.g. Render, Railway):
```env
DATABASE_URL=postgresql://postgres:<PASSWORD>@<SUPABASE-HOST>:5432/postgres
JWT_SECRET=supersecretkeythatshouldbechangedinproduction
JWT_ALGORITHM=HS256
MODEL_PATH=../risk_engine/app/ml/model.joblib
CORS_ORIGINS=https://your-live-frontend.vercel.app
```

### Frontend (`frontend/.env`)
Set these in your hosting provider (e.g. Vercel):
```env
VITE_API_URL=https://your-live-backend.onrender.com
```

## 2. Deploying Backend

We recommend **Render** as a hackathon-friendly platform:

1. Connect your GitHub repository to Render and create a new **Web Service**.
2. Root Directory: `backend`
3. Environment: `Python 3`
4. Build Command: `pip install -r requirements.txt && pip install -r ../risk_engine/requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add the environment variables from above.

*Note: Since the backend requires the `risk_engine` directory, make sure Render fetches the whole repository or keep the `backend` and `risk_engine` structured so `sys.path.append` works.*

## 3. Deploying Frontend

We recommend **Vercel**:

1. Connect your GitHub repository to Vercel.
2. Framework Preset: `Vite`
3. Root Directory: `frontend`
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Add the `VITE_API_URL` environment variable.

## 4. End-to-End Test (Live)

Once both are deployed, visit the live frontend URL:
1. Register a new worker account (`ravi@test.com`).
2. Log in and navigate to the dashboard.
3. Add mock earnings via API (or Postman pointing to live backend).
4. Refresh the dashboard to see the real Stability Score and Risk Level fetched from the trained ML model.
