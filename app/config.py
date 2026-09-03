from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
DATA_DIR = ROOT_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
SEED_DIR = APP_DIR / "data"
STATIC_DIR = APP_DIR / "static"
TEMPLATE_DIR = APP_DIR / "templates"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_stt_model: str = "whisper-1"
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "nova"
    app_secret: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./data/hanashi.db"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def db_path(self) -> Path:
        raw = self.database_url
        if raw.startswith("sqlite:///"):
            path = raw.removeprefix("sqlite:///")
            p = Path(path)
            if not p.is_absolute():
                p = ROOT_DIR / p
            return p
        return ROOT_DIR / "data" / "hanashi.db"

    @property
    def sqlalchemy_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
