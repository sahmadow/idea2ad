import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.scraper import validate_url, scrape_landing_page


class TestURLValidation:
    """Tests for URL validation and SSRF protection"""

    def test_adds_https_if_missing(self):
        """Should add https:// prefix to URLs without scheme"""
        assert validate_url("example.com") == "https://example.com"

    def test_preserves_https(self):
        """Should preserve existing https:// prefix"""
        assert validate_url("https://example.com") == "https://example.com"

    def test_preserves_http(self):
        """Should preserve existing http:// prefix"""
        assert validate_url("http://example.com") == "http://example.com"

    def test_rejects_localhost(self):
        """Should reject localhost to prevent SSRF"""
        with pytest.raises(ValueError, match="Internal"):
            validate_url("http://localhost:8000")

    def test_rejects_127_0_0_1(self):
        """Should reject 127.0.0.1 to prevent SSRF"""
        with pytest.raises(ValueError, match="Internal"):
            validate_url("http://127.0.0.1")

    def test_rejects_private_ip_10(self):
        """Should reject 10.x.x.x private IPs"""
        with pytest.raises(ValueError, match="Internal"):
            validate_url("http://10.0.0.1")

    def test_rejects_private_ip_192(self):
        """Should reject 192.168.x.x private IPs"""
        with pytest.raises(ValueError, match="Internal"):
            validate_url("http://192.168.1.1")

    def test_rejects_invalid_scheme(self):
        """Should reject non-http/https schemes"""
        with pytest.raises(ValueError, match="scheme|domain"):
            validate_url("ftp://example.com")

    def test_rejects_missing_domain(self):
        """Should reject URLs without domain"""
        with pytest.raises(ValueError, match="domain"):
            validate_url("https://")

    def test_accepts_valid_domain(self):
        """Should accept valid domain names"""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("https://sub.example.com") == "https://sub.example.com"

    def test_accepts_domain_with_path(self):
        """Should accept URLs with paths"""
        url = validate_url("https://example.com/path/to/page")
        assert url == "https://example.com/path/to/page"


class TestScraper:
    """Tests for landing page scraper"""

    @pytest.mark.skip(reason="Requires network access - run manually")
    @pytest.mark.asyncio
    async def test_scrape_returns_structured_data(self, mock_playwright):
        """Should return properly structured scraped data"""
        with patch("app.services.scraper.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright

            result = await scrape_landing_page("https://example.com")

            assert "title" in result
            assert "description" in result
            assert "headers" in result
            assert "styling" in result
            assert "full_text" in result

    @pytest.mark.asyncio
    async def test_scrape_validates_url(self):
        """Should validate URL before scraping"""
        with pytest.raises(ValueError):
            await scrape_landing_page("http://localhost:8000")

    @pytest.mark.skip(reason="Requires network access - run manually")
    @pytest.mark.asyncio
    async def test_scrape_handles_missing_protocol(self, mock_playwright):
        """Should add https to URLs without protocol"""
        with patch("app.services.scraper.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright

            result = await scrape_landing_page("example.com")

            # Should not raise error
            assert "title" in result
