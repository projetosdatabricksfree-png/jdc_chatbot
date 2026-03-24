from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    telegram_token: str
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    whisper_model: str = "base"
    knowledge_base_path: Path = Field(
        default=Path("JORNADA_CONQUISTAS_LLM_BASE.md")
    )
    max_history_messages: int = 10
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
