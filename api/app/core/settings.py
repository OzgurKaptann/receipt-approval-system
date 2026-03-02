from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # REQUIRED (MVP boots with these)
    DATABASE_URL: str
    JWT_SECRET: str = Field(default="dev_jwt_secret_change_me")

    # Runtime paths
    STORAGE_DIR: str = Field(default="/storage")
    FX_PROVIDER: str = Field(default="TCMB")

    # Public base (needed when you generate public links; safe default for local)
    PUBLIC_BASE_URL: str = Field(default="http://localhost:8000")

    # Telegram (optional until you enable webhook flow)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_CB_SECRET: Optional[str] = None

    # Slack (optional until you enable interactive flow)
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None

    # Email (optional for MVP; we will audit failures)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # CRM/MT (optional - simulated if missing)
    CRM_MT_DEPOSIT_URL: Optional[str] = None
    CRM_MT_API_KEY: Optional[str] = None

settings = Settings()
