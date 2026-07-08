from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Single source of truth for all configuration.
    Values are read from environment variables (set via docker-compose.yml / .env).
    Never hardcode secrets or connection strings elsewhere in the codebase --
    always import `settings` from here.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "StudyMate AI"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://studymate:studymate@localhost:5432/studymate"

    # --- Auth ---
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- AI / RAG (local, free stack) ---
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # --- Uploads ---
    UPLOAD_DIR: str = "/app/uploads"


settings = Settings()
