import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Set test environment before importing app
import os
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["GOOGLE_API_KEY"] = "test_key"
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_APP_SECRET"] = "test_secret"
os.environ["META_APP_ID"] = "test_app_id"
os.environ["META_AD_ACCOUNT_ID"] = "act_test"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    """Mock Prisma database client"""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.execute_raw = AsyncMock(return_value=1)

    # Mock user operations
    mock.user.find_unique = AsyncMock(return_value=None)
    mock.user.create = AsyncMock()

    # Mock campaign operations
    mock.campaign.find_unique = AsyncMock(return_value=None)
    mock.campaign.create = AsyncMock()
    mock.campaign.update = AsyncMock()

    # Mock imagebrief operations
    mock.imagebrief.find_unique = AsyncMock(return_value=None)
    mock.imagebrief.update = AsyncMock()

    return mock


@pytest.fixture
async def client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with mocked database"""
    with patch("app.db.db", mock_db):
        with patch("app.db.connect_db", AsyncMock()):
            with patch("app.db.disconnect_db", AsyncMock()):
                from app.main import app

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac


@pytest.fixture
def mock_playwright():
    """Mock Playwright for scraper tests"""
    mock_page = MagicMock()
    mock_page.title = AsyncMock(return_value="Test Title")
    mock_page.evaluate = AsyncMock(side_effect=[
        "Test description",  # description
        "https://example.com/image.png",  # og:image
        ["Header 1", "Header 2"],  # headers
        "Test body content with enough text to pass the filter.",  # body_text
        {"colors": ["#ffffff", "#000000"], "fonts": ["Arial"]},  # styling
    ])
    mock_page.goto = AsyncMock()
    mock_page.set_extra_http_headers = AsyncMock()

    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright = MagicMock()
    mock_playwright.chromium = mock_chromium

    return mock_playwright


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return {
        "summary": "Test product summary",
        "unique_selling_proposition": "Best test product",
        "pain_points": ["Problem 1", "Problem 2"],
        "call_to_action": "Buy Now",
        "buyer_persona": {
            "age_range": [25, 45],
            "gender": "All",
            "interests": ["technology"]
        },
        "keywords": ["test", "product", "best"],
        "styling_guide": {
            "primary_colors": ["#ff0000"],
            "secondary_colors": ["#00ff00"],
            "font_families": ["Arial"],
            "design_style": "modern",
            "mood": "professional"
        }
    }


@pytest.fixture
def sample_campaign_draft():
    """Sample campaign draft for testing"""
    return {
        "project_url": "https://example.com",
        "analysis": {
            "summary": "Test product",
            "unique_selling_proposition": "Best product",
            "pain_points": ["Problem 1"],
            "call_to_action": "Buy Now",
            "buyer_persona": {"age_range": [25, 45]},
            "keywords": ["test", "product"],
            "styling_guide": {
                "primary_colors": ["#ff0000"],
                "secondary_colors": ["#00ff00"],
                "font_families": ["Arial"],
                "design_style": "modern",
                "mood": "professional"
            }
        },
        "targeting": {
            "age_min": 25,
            "age_max": 45,
            "genders": ["male", "female"],
            "geo_locations": ["US"],
            "interests": ["test"]
        },
        "suggested_creatives": [
            {
                "type": "headline",
                "content": "Test Headline",
                "headline": "Test Headline",
                "primary_text": "Test primary text"
            }
        ],
        "image_briefs": [
            {
                "approach": "product-focused",
                "visual_description": "Product on white background",
                "styling_notes": "Modern, clean",
                "text_overlays": [],
                "meta_best_practices": [],
                "rationale": "Focus on product",
                "image_url": "https://s3.example.com/image.png"
            }
        ],
        "status": "ANALYZED"
    }


@pytest.fixture
def auth_headers():
    """Generate auth headers for protected endpoints"""
    from app.auth.jwt import create_access_token
    token = create_access_token("test-user-id")
    return {"Authorization": f"Bearer {token}"}
