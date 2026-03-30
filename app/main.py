
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.db.base  # noqa: F401 - Import models to ensure they are registered
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Configuration
# Adjust ALLOWED_ORIGINS via environment variable in production
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://splitwise-frontend-demo.vercel.app" # Example frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For 100% free generic deployment, we allow all temporarily.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Splitwise Clone API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
