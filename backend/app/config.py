from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_name: str = "Task Manager API"
    environment: str = "development"
    backend_port: int = 8000

    supabase_url: str
    supabase_service_role_key: str
    cors_origins: str = "http://localhost:5173"

    auth_required: bool = False
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    manager_username: str = "manager"
    manager_password: str = "manager123"

    demo_username: str = "admin"
    demo_password: str = "admin123"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
