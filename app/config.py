from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://localhost:5432/idea2ad"

    # JWT Auth
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Google
    google_api_key: str = ""
    google_cloud_project: str = ""
    google_application_credentials: Optional[str] = None

    # Meta
    meta_access_token: str = ""
    meta_app_secret: str = ""
    meta_app_id: str = ""
    meta_ad_account_id: str = ""
    meta_default_page_id: str = ""

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "idea2ad-images"
    aws_region: str = "us-east-1"

    # Sentry
    sentry_dsn: Optional[str] = None

    # Environment
    environment: str = "development"
    debug: bool = True

    # Optional Meta parent business (for 2-tier mode)
    meta_parent_business_id: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
