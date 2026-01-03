import pytest
from unittest.mock import patch

from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_token


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
