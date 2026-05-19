from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- OpenAI (LLM) ---
    openai_api_key: str | None = None

    # --- Anthropic (LLM) ---
    anthropic_model: str = "claude-sonnet-4-5"

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

    # --- LangSmith ---
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "aimo-wiki-ingest"


settings = Settings()
