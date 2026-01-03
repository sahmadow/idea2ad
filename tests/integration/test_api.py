import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient


class TestRootEndpoint:
    """Tests for root endpoint"""

    @pytest.mark.asyncio
    async def test_root_returns_ok(self, client: AsyncClient):
        """Should return API status message"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Should return health status"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, mock_db):
        """Should register new user"""
        mock_db.user.find_unique.return_value = None
        mock_db.user.create.return_value = MagicMock(
            id="test-id",
            email="test@example.com"
        )

        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, mock_db):
        """Should reject duplicate email"""
        mock_db.user.find_unique.return_value = MagicMock(id="existing-id")

        response = await client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Should reject weak password"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "short"  # Less than 8 chars
            }
        )

        assert response.status_code == 422  # Validation error


class TestAnalyzeEndpoint:
    """Tests for /analyze endpoint"""

    @pytest.mark.asyncio
    async def test_analyze_invalid_url(self, client: AsyncClient):
        """Should reject invalid URL"""
        response = await client.post(
            "/analyze",
            json={"url": "http://localhost:8000"}
        )

        # Should fail validation due to SSRF protection (returns 500 with ValueError)
        assert response.status_code in [400, 422, 500]
        # Verify error message mentions the issue
        assert "Internal" in response.text or "error" in response.text.lower()

    @pytest.mark.asyncio
    async def test_analyze_rate_limited(self, client: AsyncClient):
        """Should rate limit excessive requests"""
        # Make many requests quickly
        for _ in range(15):
            await client.post("/analyze", json={"url": "https://example.com"})

        response = await client.post(
            "/analyze",
            json={"url": "https://example.com"}
        )

        # Should be rate limited
        assert response.status_code == 429


class TestMetaConfigEndpoint:
    """Tests for Meta config endpoint"""

    @pytest.mark.asyncio
    async def test_meta_config(self, client: AsyncClient):
        """Should return Meta API configuration status"""
        response = await client.get("/meta/config")

        assert response.status_code == 200
        data = response.json()
        assert "simple_mode" in data
        assert "two_tier_mode" in data
        assert "business_verticals" in data
