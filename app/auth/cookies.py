"""Cookie configuration for httpOnly auth tokens"""
from app.config import get_settings

COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 3600  # 1 hour (matches JWT expiration)


def get_cookie_settings() -> dict:
    """Get cookie settings based on environment"""
    settings = get_settings()
    is_prod = settings.environment == "production"

    return {
        "key": COOKIE_NAME,
        "httponly": True,
        "secure": is_prod,  # HTTPS only in production
        "samesite": "lax",  # CSRF protection
        "max_age": COOKIE_MAX_AGE,
        "path": "/",
    }
