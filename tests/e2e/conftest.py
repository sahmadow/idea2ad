"""E2E test fixtures using Playwright"""
import pytest
from playwright.async_api import async_playwright, Browser, Page

# Test configuration
BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"
TEST_USER_EMAIL = "e2e-test@launchad.io"
TEST_USER_PASSWORD = "e2eTestPass123!"


@pytest.fixture
async def browser():
    """Launch browser for E2E tests"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser):
    """Create new page for each test"""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()


@pytest.fixture
async def authenticated_page(browser: Browser):
    """Create authenticated page with user session"""
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to app
    await page.goto(BASE_URL)
    await page.wait_for_load_state("networkidle")

    # Click sign in
    sign_in_btn = page.locator("text=Sign In").first
    if await sign_in_btn.is_visible():
        await sign_in_btn.click()
        await page.wait_for_timeout(500)

        # Modal starts in login mode - try login first
        await page.fill("input[type='email']", TEST_USER_EMAIL)
        await page.fill("input[type='password']", TEST_USER_PASSWORD)
        await page.click("button[type='submit']")

        # Wait for either modal to close (success) or error to appear
        try:
            # Wait for My Campaigns button to appear (login success)
            await page.locator("text=My Campaigns").wait_for(timeout=5000)
        except Exception:
            # Login failed, try registration
            error_visible = await page.locator("text=Invalid").is_visible()
            if error_visible:
                # Switch to sign up mode
                signup_btn = page.locator("button[type='button']:has-text('Sign Up')")
                await signup_btn.click(force=True)
                await page.wait_for_timeout(300)

                # Fill registration form (name field appears in signup mode)
                name_input = page.locator("input[type='text']")
                if await name_input.is_visible():
                    await name_input.fill("E2E Test User")
                await page.fill("input[type='email']", TEST_USER_EMAIL)
                await page.fill("input[type='password']", TEST_USER_PASSWORD)
                await page.click("button[type='submit']")
                await page.wait_for_timeout(2000)

    yield page
    await context.close()


@pytest.fixture
def frontend_url():
    """Return base URL for frontend"""
    return BASE_URL


@pytest.fixture
def backend_url():
    """Return base URL for API"""
    return API_URL
