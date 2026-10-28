from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env içinde VITE_BASE_PATH gibi frontend değişkenleri de bulunur
    )

    HOST: str = "127.0.0.1"
    PORT: int = 8001
    # Varsayılan kapalı/aynı origin; dev değerleri .env.example'da.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []
    FRAME_ANCESTORS: str = "'self'"
    ROOT_PATH: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("FRAME_ANCESTORS")
    @classmethod
    def _validate_frame_ancestors(cls, value: str) -> str:
        # CSP yönergesi/başlık enjeksiyonunu engeller.
        if ";" in value or "\r" in value or "\n" in value:
            raise ValueError("FRAME_ANCESTORS ';' veya satır sonu içeremez")
        return value.strip()


settings = Settings()
