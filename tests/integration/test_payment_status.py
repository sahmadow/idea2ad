"""Tests for /meta/payment-status endpoint"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient


class TestPaymentStatusEndpoint:
    """Tests for /meta/payment-status endpoint"""

    @pytest.fixture
    def mock_fb_session(self):
        """Mock Facebook session with access token"""
        return {
            "access_token": "test_token",
            "fb_user_id": "123",
            "selectedAdAccountId": "act_default"
        }

    @pytest.mark.asyncio
    async def test_uses_query_param_over_session(self, client: AsyncClient, mock_fb_session):
        """Should use ad_account_id from query param, not session"""
        mock_account_data = {
            "funding_source": "123456",
            "account_status": 1
        }

        with patch("app.routers.facebook.get_fb_session", AsyncMock(return_value=mock_fb_session)):
            with patch("facebook_business.api.FacebookAdsApi") as MockApi:
                with patch("facebook_business.adobjects.adaccount.AdAccount") as MockAdAccount:
                    mock_instance = MagicMock()
                    mock_instance.api_get.return_value = mock_account_data
                    MockAdAccount.return_value = mock_instance

                    # Pass different account than session default
                    response = await client.get("/meta/payment-status?ad_account_id=act_selected")

                    # Verify it used the query param account
                    MockAdAccount.assert_called_with("act_selected")
                    assert response.status_code == 200
                    assert response.json()["has_payment_method"] == True

    @pytest.mark.asyncio
    async def test_falls_back_to_session_when_no_param(self, client: AsyncClient, mock_fb_session):
        """Should fall back to session selectedAdAccountId when no query param"""
        with patch("app.routers.facebook.get_fb_session", AsyncMock(return_value=mock_fb_session)):
            with patch("facebook_business.api.FacebookAdsApi") as MockApi:
                with patch("facebook_business.adobjects.adaccount.AdAccount") as MockAdAccount:
                    mock_instance = MagicMock()
                    mock_instance.api_get.return_value = {"funding_source": "123", "account_status": 1}
                    MockAdAccount.return_value = mock_instance

                    response = await client.get("/meta/payment-status")

                    # Should use session's default account
                    MockAdAccount.assert_called_with("act_default")
                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_401_when_not_connected(self, client: AsyncClient):
        """Should return 401 when no Facebook session"""
        with patch("app.routers.facebook.get_fb_session", AsyncMock(return_value=None)):
            response = await client.get("/meta/payment-status?ad_account_id=act_123")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_false_when_no_ad_account(self, client: AsyncClient):
        """Should return has_payment_method=False when no ad account selected"""
        mock_session = {
            "access_token": "test_token",
            "fb_user_id": "123",
            "selectedAdAccountId": None
        }

        with patch("app.routers.facebook.get_fb_session", AsyncMock(return_value=mock_session)):
            response = await client.get("/meta/payment-status")
            assert response.status_code == 200
            data = response.json()
            assert data["has_payment_method"] == False
            assert "error" in data
