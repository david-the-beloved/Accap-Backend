from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Accountability Reader API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/accountability"
    supabase_database_url: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    google_client_id: str = ""

    allowed_origins: str = "http://localhost:3000"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"

    resend_api_key: str = ""
    resend_from_email: str = "noreply@example.com"

    scheduler_timezone: str = "UTC"

    @property
    def effective_database_url(self) -> str:
        return self.supabase_database_url or self.database_url

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


settings = Settings()
