"""E2E tests for authentication flow"""
import pytest
from playwright.async_api import Page, expect

BASE_URL = "http://localhost:5173"


@pytest.mark.asyncio
class TestAuthFlow:
    """Tests for user authentication"""

    async def test_home_page_loads(self, page: Page, frontend_url: str):
        """Home page should load without errors"""
        await page.goto(frontend_url)
        await page.wait_for_load_state("networkidle")

        # Check title
        await expect(page).to_have_title("LaunchAd - AI-Powered Ad Campaigns")

        # Check main elements exist
        await expect(page.locator("text=LaunchAd")).to_be_visible()

    async def test_sign_in_modal_opens(self, page: Page, frontend_url: str):
        """Sign in modal should open when clicking Sign In"""
        await page.goto(frontend_url)
        await page.wait_for_load_state("networkidle")

        # Click sign in button
        sign_in_btn = page.locator("text=Sign In").first
        if await sign_in_btn.is_visible():
            await sign_in_btn.click()

            # Modal should appear with login form
            await expect(page.locator("input[type='email']")).to_be_visible(timeout=5000)
            await expect(page.locator("input[type='password']")).to_be_visible()

    async def test_register_new_user(self, page: Page, frontend_url: str):
        """Should be able to register new user"""
        import uuid
        unique_email = f"test-{uuid.uuid4().hex[:8]}@launchad.io"

        await page.goto(frontend_url)
        await page.wait_for_load_state("networkidle")

        # Open auth modal
        sign_in_btn = page.locator("text=Sign In").first
        if await sign_in_btn.is_visible():
            await sign_in_btn.click()
            await page.wait_for_timeout(500)

            # Switch to sign up mode if needed
            signup_link = page.locator("text=Sign Up")
            if await signup_link.is_visible():
                await signup_link.click()
                await page.wait_for_timeout(300)

            # Fill form
            await page.fill("input[type='email']", unique_email)
            await page.fill("input[type='password']", "TestPass123!")

            # Submit
            await page.click("button[type='submit']")
            await page.wait_for_timeout(2000)

            # Should be logged in (modal closes)
            # Check for user indicator - "My Campaigns" button appears when logged in
            await expect(page.locator("text=My Campaigns")).to_be_visible(timeout=5000)

    async def test_login_existing_user(self, authenticated_page: Page):
        """Should be able to login with existing credentials"""
        # authenticated_page fixture handles login
        await expect(authenticated_page.locator("text=My Campaigns")).to_be_visible(timeout=5000)

    async def test_logout(self, authenticated_page: Page):
        """Should be able to logout"""
        # Click Sign Out button
        logout_btn = authenticated_page.locator("text=Sign Out")
        if await logout_btn.is_visible():
            await logout_btn.click()
            await authenticated_page.wait_for_timeout(1000)

            # Should see Sign In again
            await expect(authenticated_page.locator("text=Sign In")).to_be_visible(timeout=5000)

    async def test_cookie_persists_on_refresh(self, authenticated_page: Page, frontend_url: str):
        """Auth should persist after page refresh"""
        # Refresh page
        await authenticated_page.reload()
        await authenticated_page.wait_for_load_state("networkidle")

        # Should still be logged in
        await expect(authenticated_page.locator("text=My Campaigns")).to_be_visible(timeout=5000)
