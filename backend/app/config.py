from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./incidents.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    cors_origins: list[str] = ["http://localhost:3001", "http://localhost:5173"]
    log_level: str = "INFO"


settings = Settings()
