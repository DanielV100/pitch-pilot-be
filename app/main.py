from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.routes.v1 import health_route  
from app.routes.v1.authentication import authentication_route 
from app.routes.v1 import user_route

settings = Settings()

app = FastAPI(
    title="PitchPilot API",
    description="API backend for the PitchPilot presentation training platform.",
    version="1.0.0",
)

# ───────────────────────────────────────────────
# CORS middleware
# ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────
app.include_router(health_route.router, prefix="/api/v1", tags=["System"])
app.include_router(authentication_route.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_route.router, prefix="/api/v1/user", tags=["User"])


