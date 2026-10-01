from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    superuser_telegram_id: int = Field(default=0, validation_alias="SUPERUSER_TELEGRAM_ID")
    database_url: str = Field(
        default="sqlite:///./community.db",
        validation_alias="DATABASE_URL",
    )
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    api_key: str = Field(default="", validation_alias="API_KEY")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        """Converts the supported sqlite URL into a local filesystem path."""
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("DATABASE_URL debe usar el formato sqlite:///ruta.db")
        return Path(self.database_url.removeprefix(prefix))


settings = Settings()
