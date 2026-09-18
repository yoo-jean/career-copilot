from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "local"  # local | production

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    discord_bot_token: str | None = None
    discord_guild_id: int | None = None  # 지정 시 해당 서버에 슬래시 커맨드 즉시 동기화 (개발용)

    # 로컬: ./data 그대로 사용. 클라우드: 마운트된 볼륨 경로(예: /data)로 교체.
    data_dir: Path = Path("./data")
    database_url: str | None = None  # 지정 시 data_dir 기반 계산을 무시

    demo_mode: bool = False
    log_level: str = "INFO"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_name = "demo/career_copilot.db" if self.demo_mode else "career_copilot.db"
        db_path = self.data_dir / db_name
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    @property
    def chroma_persist_dir(self) -> Path:
        sub_dir = "demo/chroma" if self.demo_mode else "chroma"
        path = self.data_dir / sub_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
