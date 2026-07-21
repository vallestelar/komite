from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", API_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Komite API", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")

    postgres_db: str = Field(default="komite_db", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=1, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    ai_provider: str | None = Field(default=None, alias="AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_model: str | None = Field(default=None, alias="AI_MODEL")
    ai_base_url: str | None = Field(default=None, alias="AI_BASE_URL")
    ai_temperature: float = Field(default=0.2, alias="AI_TEMPERATURE")
    ai_max_tokens: int = Field(default=2000, alias="AI_MAX_TOKENS")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    deepseek_reasoning_model: str = Field(default="deepseek-v4-pro", alias="DEEPSEEK_REASONING_MODEL")
    transcription_provider: str = Field(default="local_whisper", alias="TRANSCRIPTION_PROVIDER")
    local_whisper_model: str = Field(default="small", alias="LOCAL_WHISPER_MODEL")
    local_whisper_device: str = Field(default="cpu", alias="LOCAL_WHISPER_DEVICE")
    local_whisper_compute_type: str = Field(default="int8", alias="LOCAL_WHISPER_COMPUTE_TYPE")
    openai_transcription_model: str = Field(default="gpt-4o-transcribe", alias="OPENAI_TRANSCRIPTION_MODEL")
    openai_draft_model: str = Field(default="gpt-5.5", alias="OPENAI_DRAFT_MODEL")
    upload_dir: str = Field(default="storage/uploads", alias="UPLOAD_DIR")
    private_upload_dir: str = Field(default="storage/private", alias="PRIVATE_UPLOAD_DIR")
    max_audio_upload_mb: int = Field(default=25, alias="MAX_AUDIO_UPLOAD_MB")
    max_evidence_image_mb: int = Field(default=2, alias="MAX_EVIDENCE_IMAGE_MB")
    max_evidence_image_px: int = Field(default=1800, alias="MAX_EVIDENCE_IMAGE_PX")
    evidence_image_quality: int = Field(default=82, alias="EVIDENCE_IMAGE_QUALITY")
    storage_provider: str = Field(default="local", alias="STORAGE_PROVIDER")
    storage_public_base_url: str | None = Field(default=None, alias="STORAGE_PUBLIC_BASE_URL")
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_acl: str | None = Field(default="public-read", alias="S3_ACL")

    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="no-reply@komite.cl", alias="SMTP_FROM")

    seed_admin_email: str = Field(default="admin@komite.cl", alias="SEED_ADMIN_EMAIL")
    seed_admin_password: str = Field(default="admin1234", alias="SEED_ADMIN_PASSWORD")
    seed_admin_full_name: str = Field(default="Administrador Komite", alias="SEED_ADMIN_FULL_NAME")


settings = Settings()
