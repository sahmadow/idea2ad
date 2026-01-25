from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Optional
import warnings


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
    meta_config_id: str = ""  # Facebook Login for Business config ID

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

    # Image generation (disable for testing to save costs)
    skip_image_generation: bool = False
    placeholder_image_url: str = "https://placehold.co/1080x1080/1a1a2e/white?text=Ad+Preview"

    # URLs (for OAuth callbacks and CORS)
    frontend_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000"

    # Optional Meta parent business (for 2-tier mode)
    meta_parent_business_id: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @model_validator(mode="after")
    def validate_production_config(self):
        """Validate critical env vars for production"""
        if self.environment == "production":
            errors = []

            # JWT secret must be changed
            if self.jwt_secret_key == "change-this-in-production":
                errors.append("JWT_SECRET_KEY must be set in production")

            # JWT secret should be strong (min 32 chars)
            if len(self.jwt_secret_key) < 32:
                errors.append("JWT_SECRET_KEY must be at least 32 characters")

            # Database URL should not be localhost
            if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                errors.append("DATABASE_URL should not use localhost in production")

            if errors:
                raise ValueError(f"Production config errors: {', '.join(errors)}")

            # Set production URL defaults if not explicitly configured
            if self.frontend_url == "http://localhost:5173":
                object.__setattr__(self, 'frontend_url', "https://launchad.io")

        elif self.environment == "staging":
            errors = []
            if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                errors.append("DATABASE_URL should not use localhost in staging")
            if len(self.jwt_secret_key) < 32:
                errors.append("JWT_SECRET_KEY must be at least 32 characters in staging")
            if errors:
                raise ValueError(f"Staging config errors: {', '.join(errors)}")

            # Set staging URL defaults if not explicitly configured
            if self.frontend_url == "http://localhost:5173":
                object.__setattr__(self, 'frontend_url', "https://idea2ad-staging.vercel.app")

        elif self.jwt_secret_key == "change-this-in-production":
            warnings.warn("Using default JWT_SECRET_KEY - change for production!")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
