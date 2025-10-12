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

    # CORS Settings - accepts comma-separated string or list
    allowed_origins: str = "http://localhost:3000,https://karmona.vercel.app,https://karmona-frontend.vercel.app,https://karmona.ai"

    def get_allowed_origins(self) -> list[str]:
        """Get allowed origins as a list."""
        if isinstance(self.allowed_origins, list):
            return self.allowed_origins
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # AWS Bedrock Settings
    aws_region: str = "us-east-2"  # Ohio region where model access is enabled
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    bedrock_agent_id: str | None = None
    bedrock_agent_alias_id: str | None = None
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # Knowledge Base Settings
    bedrock_knowledge_base_id: str = "ZDDIIWWBMV"
    bedrock_data_source_id: str = "GHIJ2U38LL"
    s3_astrology_bucket: str = "karmona-astrology-data-967392725523"

    # Supabase Settings
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str | None = None
    supabase_jwt_secret: str  # Required for JWT verification

    # Astrology API Settings
    aztro_api_url: str = "https://aztro.sameerkumar.website"


# Global settings instance
settings = Settings()
