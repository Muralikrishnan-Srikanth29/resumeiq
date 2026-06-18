"""
Centralized configuration. All secrets come from environment variables —
never hardcoded. Render/Vercel inject these at deploy time; locally use .env.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "ResumeIQ"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str  # backend-only, full table access, never sent to client
    SUPABASE_STORAGE_BUCKET: str = "resumes"

    # --- Gemini ---
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 4096

    # --- Rate limiting ---
    RATE_LIMIT_ANALYSIS_PER_HOUR: int = 10
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 20

    # --- File upload constraints ---
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_FILE_EXTENSIONS: tuple = (".pdf", ".docx")
    MAX_RESUME_TEXT_CHARS: int = 50_000
    MAX_JD_TEXT_CHARS: int = 20_000
    MIN_RESUME_TEXT_CHARS: int = 200

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
