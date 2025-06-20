from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import Settings
from app.routes.v1 import health_route  
from app.routes.v1.authentication import authentication_route 
from app.routes.v1 import user_route
from app.routes.v1 import presentation_route
from app.routes.v1 import training_route
from app.websockets import signaling
from app.routes.v1 import recordings_route

settings = Settings()

app = FastAPI(
    title="PitchPilot API",
    description="API backend for the PitchPilot presentation training platform.",
    version="1.0.0",
)

# ───────────────────────────────────────────────
# CORS middleware
# ───────────────────────────────────────────────
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
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
app.include_router(presentation_route.router, prefix="/api/v1/presentations", tags=["Presentations"])
app.include_router(training_route.router, prefix="/api/v1/trainings", tags=["Trainings"])
app.include_router(signaling.router, prefix="/api/v1/signaling", tags=["Signaling"], include_in_schema=False)
app.include_router(recordings_route.router, prefix="/api/v1/recordings", tags=["Recordings"])



