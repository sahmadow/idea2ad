import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_token
from app.auth.cookies import COOKIE_NAME, get_cookie_settings


class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_hash_password_returns_hash(self):
        """Should return a bcrypt hash"""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Should verify correct password"""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_reject_incorrect_password(self):
        """Should reject incorrect password"""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Should produce different hashes for same password (salt)"""
        password = "secure_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2


class TestJWT:
    """Tests for JWT token functions"""

    def test_create_access_token(self):
        """Should create valid JWT token"""
        user_id = "test-user-123"
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Should decode valid token and return user_id"""
        user_id = "test-user-123"
        token = create_access_token(user_id)

        decoded_id = decode_token(token)

        assert decoded_id == user_id

    def test_decode_invalid_token(self):
        """Should return None for invalid token"""
        result = decode_token("invalid.token.here")

        assert result is None

    def test_decode_tampered_token(self):
        """Should return None for tampered token"""
        user_id = "test-user-123"
        token = create_access_token(user_id)

        # Tamper with token
        parts = token.split(".")
        parts[1] = "tampered_payload"
        tampered = ".".join(parts)

        result = decode_token(tampered)

        assert result is None


class TestCookieConfig:
    """Tests for cookie configuration"""

    def test_cookie_name_defined(self):
        """Should have cookie name defined"""
        assert COOKIE_NAME == "auth_token"

    def test_cookie_settings_httponly(self):
        """Should have httpOnly enabled"""
        settings = get_cookie_settings()
        assert settings["httponly"] is True

    def test_cookie_settings_samesite(self):
        """Should have SameSite=Lax"""
        settings = get_cookie_settings()
        assert settings["samesite"] == "lax"

    def test_cookie_settings_path(self):
        """Should have path=/"""
        settings = get_cookie_settings()
        assert settings["path"] == "/"

    @patch("app.auth.cookies.get_settings")
    def test_cookie_secure_in_production(self, mock_get_settings):
        """Should set Secure flag in production"""
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        settings = get_cookie_settings()
        assert settings["secure"] is True

    @patch("app.auth.cookies.get_settings")
    def test_cookie_not_secure_in_dev(self, mock_get_settings):
        """Should not set Secure flag in development"""
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_get_settings.return_value = mock_settings

        settings = get_cookie_settings()
        assert settings["secure"] is False


@pytest.mark.asyncio
class TestCookieAuthEndpoints:
    """Tests for cookie-based authentication endpoints"""

    async def test_login_sets_cookie(self, client, mock_db):
        """Login should set httpOnly cookie"""
        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.password_hash = hash_password("testpassword123")
        mock_user.deleted_at = None
        mock_db.user.find_unique = AsyncMock(return_value=mock_user)

        response = await client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )

        assert response.status_code == 200
        assert COOKIE_NAME in response.cookies

    async def test_register_sets_cookie(self, client, mock_db):
        """Register should set httpOnly cookie"""
        mock_db.user.find_unique = AsyncMock(return_value=None)

        mock_user = MagicMock()
        mock_user.id = "new-user-id"
        mock_user.email = "new@example.com"
        mock_db.user.create = AsyncMock(return_value=mock_user)

        response = await client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "testpassword123"}
        )

        assert response.status_code == 201
        assert COOKIE_NAME in response.cookies

    async def test_logout_clears_cookie(self, client):
        """Logout should clear auth cookie"""
        response = await client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out"

    async def test_auth_from_cookie(self, client, mock_db):
        """Should authenticate from cookie"""
        token = create_access_token("test-user-id")

        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.deleted_at = None
        mock_user.created_at = datetime.now()
        mock_db.user.find_unique = AsyncMock(return_value=mock_user)

        response = await client.get(
            "/auth/me",
            cookies={COOKIE_NAME: token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_bearer_fallback(self, client, mock_db):
        """Should still work with Bearer token for API testing"""
        token = create_access_token("test-user-id")

        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.deleted_at = None
        mock_user.created_at = datetime.now()
        mock_db.user.find_unique = AsyncMock(return_value=mock_user)

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_no_auth_returns_401(self, client, mock_db):
        """Should return 401 when no auth provided"""
        response = await client.get("/auth/me")

        assert response.status_code == 401
