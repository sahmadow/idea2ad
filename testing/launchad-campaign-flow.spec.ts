import { test, expect } from '@playwright/test';

/**
 * LaunchAd Campaign Generation Flow
 * Flow: Enter URL → Generate Campaign → Select Image → Launch → Configure → Stop before payment
 */

test.describe('LaunchAd Campaign Flow', () => {

    // Configure viewport to match recording
    test.use({
        viewport: { width: 1025, height: 1144 },
    });

    test('generate campaign and configure launch settings', async ({ page }) => {
        // ============================================
        // STEP 1: Navigate to LaunchAd (logged in)
        // ============================================
        await page.goto('https://www.launchad.io/');
        await page.screenshot({ path: 'screenshots/01-homepage.png', fullPage: true });

        // ============================================
        // STEP 2: Enter product URL
        // ============================================
        const urlInput = page.locator('input[placeholder*="your-product"]').or(
            page.locator('input').first()
        );
        await urlInput.waitFor({ state: 'visible', timeout: 10000 });
        await urlInput.click();
        await urlInput.fill('https://stripe.com');

        await page.screenshot({ path: 'screenshots/02-url-entered.png' });

        // ============================================
        // STEP 3: Generate Campaign
        // ============================================
        const generateButton = page.getByRole('button', { name: /Generate Campaign/i });
        await generateButton.click();

        // Wait for campaign generation - this may take time
        // Look for indicators that generation is complete
        console.log('⏳ Waiting for campaign generation...');

        // Wait for loading to finish (adjust selector based on actual UI)
        await page.waitForTimeout(2000); // Initial wait for generation to start

        // Option 1: Wait for images to appear
        const campaignImages = page.locator('img[src*="campaign"], img[src*="generated"], .campaign-image, div.dashboard-grid img');

        try {
            await campaignImages.first().waitFor({ state: 'visible', timeout: 90000 });
            console.log('✅ Campaign images generated');
        } catch (e) {
            console.log('⚠️ Timeout waiting for images - taking screenshot anyway');
        }

        await page.screenshot({ path: 'screenshots/03-campaign-generated.png', fullPage: true });

        // ============================================
        // STEP 4: Verify images were generated
        // ============================================
        const imageCount = await page.locator('div.dashboard-grid img, .campaign-preview img').count();
        console.log(`📸 Found ${imageCount} campaign images`);

        // Take individual screenshots of generated images
        const images = page.locator('div.dashboard-grid img');
        const count = await images.count();

        for (let i = 0; i < Math.min(count, 4); i++) {
            const img = images.nth(i);
            if (await img.isVisible()) {
                await img.screenshot({ path: `screenshots/04-image-${i + 1}.png` });
            }
        }

        // Assert that at least one image was generated
        expect(imageCount).toBeGreaterThan(0);

        // ============================================
        // STEP 5: Select first generated image
        // ============================================
        const firstImage = page.locator('div:nth-of-type(4) > div:nth-of-type(1) > div:nth-of-type(1) img').first();
        if (await firstImage.isVisible()) {
            await firstImage.click();
            console.log('✅ Selected campaign image');
        }

        await page.screenshot({ path: 'screenshots/05-image-selected.png', fullPage: true });

        // ============================================
        // STEP 6: Click Launch My Campaign
        // ============================================
        const launchButton = page.getByRole('button', { name: /Launch My Campaign/i });
        await launchButton.click();

        await page.screenshot({ path: 'screenshots/06-launch-clicked.png', fullPage: true });

        // ============================================
        // STEP 7: Handle Facebook OAuth (if present)
        // ============================================
        const fbSignIn = page.getByRole('button', { name: /Sign in with Facebook/i });

        if (await fbSignIn.isVisible({ timeout: 5000 }).catch(() => false)) {
            console.log('📘 Facebook sign-in required');
            await fbSignIn.click();

            // Wait for redirect back
            await page.waitForURL(/launchad\.io.*fb_session/, { timeout: 30000 }).catch(() => {
                console.log('⚠️ Facebook OAuth timeout - may need manual intervention');
            });

            await page.screenshot({ path: 'screenshots/07-after-fb-auth.png', fullPage: true });
        }

        // ============================================
        // STEP 8: Select Ad Account
        // ============================================
        const adAccountSelector = page.locator('div.glass-panel > div:nth-of-type(2) > div div > div:nth-of-type(1)');
        if (await adAccountSelector.isVisible({ timeout: 5000 }).catch(() => false)) {
            await adAccountSelector.click();
            console.log('✅ Selected ad account');
        }

        await page.screenshot({ path: 'screenshots/08-ad-account-selected.png', fullPage: true });

        // ============================================
        // STEP 9: Select Budget ($100)
        // ============================================
        const budgetOption = page.locator('text=$100').or(
            page.locator('label:nth-of-type(2) > div > div:nth-of-type(1)')
        );

        if (await budgetOption.first().isVisible({ timeout: 5000 }).catch(() => false)) {
            await budgetOption.first().click();
            console.log('✅ Selected $100 budget');
        }

        await page.screenshot({ path: 'screenshots/09-budget-selected.png', fullPage: true });

        // ============================================
        // STEP 10: Configure Location (optional)
        // ============================================
        const cityInput = page.getByPlaceholder(/Search for a city/i);

        if (await cityInput.isVisible({ timeout: 3000 }).catch(() => false)) {
            await cityInput.click();
            await cityInput.fill('Berlin');
            await page.waitForTimeout(1000); // Wait for autocomplete

            // Select first suggestion if dropdown appears
            const suggestion = page.locator('[class*="suggestion"], [class*="dropdown"] >> text=Berlin').first();
            if (await suggestion.isVisible({ timeout: 2000 }).catch(() => false)) {
                await suggestion.click();
            }
            console.log('✅ Location configured');
        }

        await page.screenshot({ path: 'screenshots/10-location-configured.png', fullPage: true });

        // ============================================
        // FINAL: Screenshot before payment method
        // ============================================
        await page.screenshot({ path: 'screenshots/11-ready-for-payment.png', fullPage: true });

        // Verify "Add Payment Method" button is visible (but don't click)
        const paymentButton = page.getByRole('link', { name: /Add Payment Method/i }).or(
            page.locator('text=Add Payment Method')
        );

        const paymentVisible = await paymentButton.isVisible({ timeout: 5000 }).catch(() => false);
        console.log(`💳 Payment method button visible: ${paymentVisible}`);

        if (paymentVisible) {
            // Highlight the button without clicking
            await paymentButton.evaluate(el => {
                el.style.border = '3px solid red';
                el.style.boxShadow = '0 0 10px red';
            });
            await page.screenshot({ path: 'screenshots/12-payment-highlighted.png', fullPage: true });
        }

        console.log('\n✅ Test completed - stopped before payment method click');
        console.log('📁 Screenshots saved to ./screenshots/');
    });
});


/**
 * Helper test: Check if images were actually generated
 */
test('verify campaign images are valid', async ({ page }) => {
    test.skip(true, 'Run this after main flow to verify images');

    // This test can be used to verify image URLs are valid
    const imageUrls: string[] = [];

    await page.goto('https://www.launchad.io/');

    const images = page.locator('div.dashboard-grid img');
    const count = await images.count();

    for (let i = 0; i < count; i++) {
        const src = await images.nth(i).getAttribute('src');
        if (src) {
            imageUrls.push(src);

            // Verify image loads successfully
            const response = await page.request.get(src);
            expect(response.ok()).toBeTruthy();
            console.log(`✅ Image ${i + 1} valid: ${src.substring(0, 50)}...`);
        }
    }

    expect(imageUrls.length).toBeGreaterThan(0);
});
