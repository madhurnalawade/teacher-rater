from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Teacher Rating"
    debug: bool = True
    database_url: str = "sqlite:///./teacher_rating.db"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_discovery_url: str = "https://accounts.google.com/.well-known/openid-configuration"
    secret_key: str = "replace-me-with-a-secure-random-value"
    session_cookie_name: str = "teacher_rating_session"
    frontend_origin: str = "http://localhost:8000"
    admin_email: str = ""
    admin_google_sub: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
