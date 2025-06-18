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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
