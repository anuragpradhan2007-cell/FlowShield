from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from auth import router as auth_router
from users import router as users_router
from workers import router as workers_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlowShield Auth Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/api/v1", tags=["users"])
app.include_router(workers_router.router, prefix="/api/v1/workers", tags=["workers"])

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
