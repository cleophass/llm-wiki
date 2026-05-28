from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Anthropic (LLM) ---
    anthropic_api_key: str | None = None


    # --- Mistral (OCR uniquement) ---
    mistral_api_key: str | None = None

    # --- File upload limits ---
    max_file_size_mb: int = 20

    # --- Stockage local ---
    global_project_id: str = "global"
    wiki_dir: str = "./wiki"
    conversations_dir: str = "./conversations"
    ingestion_history_dir: str = "./ingestion_history"

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- MLflow ---
    mlflow_tracking_uri: str = "http://localhost:5001"


settings = Settings()
