from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Worker Stability & Risk Scoring Engine"
    environment: str = "development"
    debug: bool = True

    # Database Configuration (Supabase PostgreSQL / SQLite fallback)
    database_url: str = Field(
        default="sqlite:///./risk_scores.db",
        description="Database URL for Supabase PostgreSQL or local SQLite",
        validation_alias="DATABASE_URL",
    )
    supabase_db_url: Optional[str] = Field(
        default=None,
        description="Optional explicit Supabase connection URL",
        validation_alias="SUPABASE_DB_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def effective_db_url(self) -> str:
        """
        Returns the resolved database connection URL.
        Normalizes postgres:// to postgresql+psycopg2:// for SQLAlchemy compatibility.
        """
        raw_url = self.supabase_db_url or self.database_url
        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
            return raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return raw_url


settings = Settings()
