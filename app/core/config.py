from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    POSTGRES_URL: str
    DEBUG: bool = False
    JWT_SECRET: str
    JWT_ALGO: str = "HS256"
    RESEND_API_KEY: str
    RESEND_SENDER_MAIL: str = "onboarding@resend.dev"
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "pitchpilot"
    PRESENTATION_BATCH_SIZE: int = 2 
    PRESENTATION_MAX_WORKERS: int = 4
    OPENAI_API_KEY: str
    FINDING_WEIGHT_PREFLIGHT: float = 0.5
    FINDING_WEIGHT_ALTITUDE: float = 0.2
    FINDING_WEIGHT_FLIGHT_PATH: float = 0.2
    FINDING_WEIGHT_COCKPIT: float = 0.1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
