from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.routes import router as workers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables (compatible with SQLite and Supabase PostgreSQL)
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Worker Stability & Risk Scoring Engine (Member 3) with Supabase / PostgreSQL support and strict Pydantic contracts.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(workers_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "service": settings.app_name,
        "environment": settings.environment,
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
