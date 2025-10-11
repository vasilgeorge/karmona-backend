"""
Configuration management using Pydantic Settings.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    app_name: str = "Karmona API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # CORS Settings
    allowed_origins: list[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str] | None) -> list[str]:
        """Parse allowed_origins from comma-separated string or list."""
        if v is None:
            return ["http://localhost:3000", "https://karmona.vercel.app", "https://karmona.ai"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["http://localhost:3000", "https://karmona.vercel.app", "https://karmona.ai"]

    # AWS Bedrock Settings
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    bedrock_agent_id: str | None = None
    bedrock_agent_alias_id: str | None = None
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Supabase Settings
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str | None = None

    # JWT Settings (for token verification)
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"

    # Astrology API Settings
    aztro_api_url: str = "https://aztro.sameerkumar.website"


# Global settings instance
settings = Settings()
