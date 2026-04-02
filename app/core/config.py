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
        db_url = self.supabase_database_url or self.database_url

        if db_url.startswith("postgres://"):
            db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
        elif db_url.startswith("postgresql://"):
            db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]
        elif db_url.startswith("postgresql+psycopg2://"):
            db_url = "postgresql+psycopg://" + db_url[len("postgresql+psycopg2://"):]

        # Supabase pooler endpoint should use 6543, not 5432.
        if "pooler.supabase.com" in db_url and ":5432/" in db_url:
            db_url = db_url.replace(":5432/", ":6543/")

        # Supabase Postgres requires SSL in production connections.
        if "pooler.supabase.com" in db_url and "sslmode=" not in db_url.lower():
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}sslmode=require"

        return db_url

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


settings = Settings()
