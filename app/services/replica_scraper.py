"""Replica scraper for extracting landing page elements for ad creative replication."""

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Dict, Any, List, Optional
import logging
import base64

from app.models import (
    ReplicaData, HeroData, FeatureItem, TestimonialItem
)
from app.services.scraper import validate_url, navigate_with_fallback

logger = logging.getLogger(__name__)


async def scrape_for_replica(url: str) -> ReplicaData:
    """
    Extract all elements needed for replica ad creatives.

    Extracts:
    - Hero section (headline, subheadline, background, CTA)
    - Logo
    - Brand assets (colors, fonts, CSS variables)
    - Features/benefits sections
    - Testimonials
    - Product screenshots
    - Before/after content
    """
    url = validate_url(url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })

            load_strategy = await navigate_with_fallback(page, url)
            logger.info(f"Page loaded via {load_strategy} for replica scrape: {url}")

            # Extract hero section
            hero_data = await _extract_hero(page)

            # Extract logo (reuse existing logic pattern)
            logo_url = await _extract_logo(page)

            # Extract brand assets
            brand_assets = await _extract_brand_assets(page)

            # Extract features/benefits
            features = await _extract_features(page)

            # Extract testimonials
            testimonials = await _extract_testimonials(page)

            # Extract product screenshots
            screenshots = await _extract_product_screenshots(page)

            # Extract before/after content
            before_after = await _extract_before_after(page)

            return ReplicaData(
                url=url,
                hero=hero_data,
                logo_url=logo_url,
                primary_color=brand_assets.get("primary_color", "#ffffff"),
                secondary_color=brand_assets.get("secondary_color", "#000000"),
                accent_color=brand_assets.get("accent_color", "#0066ff"),
                font_family=brand_assets.get("font_family", "Inter"),
                font_faces=brand_assets.get("font_faces", []),
                css_variables=brand_assets.get("css_variables", {}),
                features=features,
                testimonials=testimonials,
                product_screenshots=screenshots,
                before_after=before_after
            )

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout scraping {url} for replica: {e}")
            raise ValueError("Page load timeout")
        except Exception as e:
            logger.error(f"Error scraping {url} for replica: {e}", exc_info=True)
            raise ValueError(f"Failed to scrape URL: {str(e)}")
        finally:
            await browser.close()


async def _extract_hero(page) -> HeroData:
    """
    Extract hero section using multi-strategy approach:
    1. Find hero container (multiple selector strategies)
    2. Find headline (largest H1/H2 in viewport top half)
    3. Find subheadline (paragraph near headline)
    4. Find CTA (styled button with action text)
    5. Find background (img tag or CSS background)
    """
    hero_data = await page.evaluate('''() => {
        const data = {
            headline: "",
            subheadline: null,
            background_color: null,
            background_url: null,
            cta_text: "Learn More",
            cta_styles: {},
            headlineEl: null
        };

        // ============================================
        // STRATEGY 1: Hero Container Detection
        // ============================================
        const heroSelectors = [
            // Explicit hero classes
            'section[class*="hero"]', 'div[class*="hero"]',
            '[class*="Hero"]', '#hero',
            // Common landing page patterns
            'main > section:first-of-type',
            'main > div:first-of-type > section:first-of-type',
            // Header-adjacent content
            'header + section', 'header + div > section',
            // Banner patterns
            '[class*="banner"]', '[class*="Banner"]',
            '[class*="landing"]', '[class*="intro"]',
            // Viewport-height sections
            'section[style*="100vh"]', 'div[style*="100vh"]',
            // Fallbacks
            '.hero', '.banner'
        ];

        let heroSection = null;
        for (const selector of heroSelectors) {
            try {
                heroSection = document.querySelector(selector);
                if (heroSection) {
                    const rect = heroSection.getBoundingClientRect();
                    // Verify it's in viewport top area
                    if (rect.top < window.innerHeight * 0.5) break;
                    heroSection = null;
                }
            } catch (e) {}
        }

        // Fallback to first large section
        if (!heroSection) {
            const sections = document.querySelectorAll('section, main > div');
            for (const section of sections) {
                const rect = section.getBoundingClientRect();
                if (rect.height > 300 && rect.top < 200) {
                    heroSection = section;
                    break;
                }
            }
        }

        // Final fallback
        if (!heroSection) {
            heroSection = document.querySelector('main > *:first-child') || document.body;
        }

        // ============================================
        // STRATEGY 2: Headline Detection (DOM-wide search)
        // ============================================
        function findHeroHeadline() {
            // First pass: look for semantic heading tags
            const headings = document.querySelectorAll('h1, h2, [class*="heading"], [class*="title"], [class*="headline"]');
            let best = null;
            let bestScore = 0;

            for (const h of headings) {
                const rect = h.getBoundingClientRect();
                const styles = getComputedStyle(h);

                // Skip if below fold (below 60% of viewport)
                if (rect.top > window.innerHeight * 0.6) continue;
                // Skip if hidden
                if (rect.width === 0 || rect.height === 0) continue;
                // Skip if not visible
                if (styles.display === 'none' || styles.visibility === 'hidden') continue;
                // Skip navigation elements
                if (h.closest('nav, header nav, [class*="nav"], footer')) continue;

                // Score based on: font size, position, word count
                const fontSize = parseFloat(styles.fontSize) || 16;
                const positionScore = (1 - rect.top / window.innerHeight) * 30;
                const sizeScore = fontSize;
                const text = h.innerText.trim();
                const wordCount = text.split(/\\s+/).length;
                const wordScore = wordCount > 3 && wordCount < 30 ? 20 : 0;
                const tagScore = h.tagName === 'H1' ? 30 : (h.tagName === 'H2' ? 15 : 0);

                const score = positionScore + sizeScore + wordScore + tagScore;
                if (score > bestScore && text.length > 10) {
                    bestScore = score;
                    best = h;
                }
            }

            // If found a good heading with decent score, return it
            if (best && bestScore > 60) return { el: best, text: best.innerText.trim() };

            // Second pass: Look for large text elements (sites like Framer use <p> with large fonts)
            const largeTextEls = [];
            const allElements = document.querySelectorAll('p, span, div');
            for (const el of allElements) {
                const rect = el.getBoundingClientRect();
                const styles = getComputedStyle(el);
                const fontSize = parseFloat(styles.fontSize) || 16;

                // Only consider large text (>= 32px) in hero area
                if (fontSize < 32) continue;
                if (rect.top > window.innerHeight * 0.5) continue;
                if (rect.top < 50) continue; // Skip nav area
                if (rect.width === 0 || rect.height === 0) continue;
                if (styles.display === 'none' || styles.visibility === 'hidden') continue;
                if (el.closest('nav, footer, [class*="nav"]')) continue;

                const text = el.innerText?.trim();
                if (!text || text.length < 5) continue;

                // Check if this is a leaf-ish node (children don't have exact same text)
                const childTexts = [...el.children].map(c => c.innerText?.trim()).filter(Boolean);
                const isLeaf = childTexts.length === 0 || !childTexts.some(ct => ct === text);

                if (isLeaf) {
                    largeTextEls.push({
                        el: el,
                        text: text,
                        top: rect.top,
                        fontSize: fontSize
                    });
                }
            }

            // Sort by top position, then combine adjacent large text elements
            largeTextEls.sort((a, b) => a.top - b.top);

            if (largeTextEls.length > 0) {
                // Group elements that are close together (within 150px) and similar font size
                let combinedText = largeTextEls[0].text;
                let firstEl = largeTextEls[0].el;
                let lastTop = largeTextEls[0].top;
                let baseFontSize = largeTextEls[0].fontSize;

                for (let i = 1; i < largeTextEls.length && i < 4; i++) {
                    const curr = largeTextEls[i];
                    // Check if this element is close and similar font size
                    if (curr.top - lastTop < 150 && Math.abs(curr.fontSize - baseFontSize) < 10) {
                        // Don't duplicate if text is already included
                        if (!combinedText.includes(curr.text)) {
                            combinedText += ' ' + curr.text;
                        }
                        lastTop = curr.top;
                    } else {
                        break;
                    }
                }

                // If we found good large text, use it
                if (combinedText.length > 15) {
                    return { el: firstEl, text: combinedText };
                }
            }

            // Return original best if we have one
            return best ? { el: best, text: best.innerText.trim() } : null;
        }

        const headlineResult = findHeroHeadline();
        if (headlineResult) {
            data.headline = headlineResult.text;
            data._headlineEl = headlineResult.el;
        }

        // ============================================
        // STRATEGY 3: Subheadline Detection
        // ============================================
        function findSubheadline(headlineEl) {
            if (!headlineEl) return null;

            const headlineText = data.headline;
            const headlineRect = headlineEl.getBoundingClientRect();
            const headlineStyles = getComputedStyle(headlineEl);
            const headlineFontSize = parseFloat(headlineStyles.fontSize) || 32;

            // Helper: check if text is part of headline or vice versa
            function isHeadlineText(text) {
                if (text === headlineText) return true;
                // Check if text is contained in headline or contains headline
                if (headlineText.includes(text) || text.includes(headlineText)) return true;
                // Check significant word overlap (>50% of words match)
                const textWords = text.toLowerCase().split(/\\s+/).filter(w => w.length > 3);
                const headlineWords = headlineText.toLowerCase().split(/\\s+/).filter(w => w.length > 3);
                const overlap = textWords.filter(w => headlineWords.includes(w)).length;
                if (textWords.length > 0 && overlap / textWords.length > 0.5) return true;
                return false;
            }

            // Helper: validate subheadline candidate
            function isValidSubheadline(el, text) {
                if (!text || text.length < 25 || text.length > 400) return false;
                if (isHeadlineText(text)) return false;

                const rect = el.getBoundingClientRect();
                const styles = getComputedStyle(el);
                const fontSize = parseFloat(styles.fontSize) || 16;

                // Subheadline should have smaller font than headline
                if (fontSize >= headlineFontSize) return false;
                // Should be in reasonable position (not too far below)
                if (rect.top > window.innerHeight * 0.7) return false;

                return true;
            }

            // Strategy A: Look for elements positioned below the headline in hero section
            if (heroSection) {
                const candidates = [];
                const allText = heroSection.querySelectorAll('p, span, div, [class*="subtitle"], [class*="subhead"], [class*="description"], [class*="tagline"]');

                for (const el of allText) {
                    const rect = el.getBoundingClientRect();
                    const styles = getComputedStyle(el);
                    const fontSize = parseFloat(styles.fontSize) || 14;

                    // Skip elements above or at same level as headline
                    if (rect.top <= headlineRect.bottom + 20) continue;
                    // Skip if hidden
                    if (rect.width === 0 || rect.height === 0) continue;
                    if (styles.display === 'none' || styles.visibility === 'hidden') continue;

                    const text = el.innerText?.trim();

                    // Check if this is a leaf node (no children with same text)
                    const childTexts = [...el.children].map(c => c.innerText?.trim()).filter(Boolean);
                    const isLeaf = childTexts.length === 0 || !childTexts.some(ct => ct === text);

                    if (isLeaf && isValidSubheadline(el, text)) {
                        candidates.push({
                            el: el,
                            text: text,
                            top: rect.top,
                            fontSize: fontSize,
                            // Score: prefer larger text closer to headline
                            score: fontSize * 2 + (1000 - rect.top)
                        });
                    }
                }

                // Sort by score and return best candidate
                candidates.sort((a, b) => b.score - a.score);
                if (candidates.length > 0) {
                    return candidates[0].text;
                }
            }

            // Strategy B: Check siblings of headline element
            let sibling = headlineEl.nextElementSibling;
            let siblingCount = 0;
            while (sibling && siblingCount < 8) {
                siblingCount++;
                const text = sibling.innerText?.trim();
                if (isValidSubheadline(sibling, text)) {
                    return text;
                }
                sibling = sibling.nextElementSibling;
            }

            // Strategy C: Check parent's children
            const parent = headlineEl.parentElement;
            if (parent) {
                for (const child of parent.children) {
                    if (child === headlineEl) continue;
                    const text = child.innerText?.trim();
                    if (isValidSubheadline(child, text)) {
                        return text;
                    }
                }
            }

            return null;
        }

        data.subheadline = findSubheadline(data._headlineEl);

        // ============================================
        // STRATEGY 4: Background Image Detection
        // ============================================
        function findHeroBackground(heroSection) {
            if (!heroSection) return null;

            // Check hero and its ancestors for background
            let el = heroSection;
            let depth = 0;
            while (el && depth < 3) {
                const styles = getComputedStyle(el);
                const bgImage = styles.backgroundImage;
                if (bgImage && bgImage !== 'none') {
                    const urlMatch = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/);
                    if (urlMatch && !urlMatch[1].includes('gradient')) {
                        return urlMatch[1];
                    }
                }
                el = el.parentElement;
                depth++;
            }

            // Strategy B: Full-width <img> inside hero (common pattern)
            const imgs = heroSection.querySelectorAll('img');
            for (const img of imgs) {
                const rect = img.getBoundingClientRect();
                const className = img.className.toString().toLowerCase();
                // Check if image is large (likely a background)
                if (rect.width > window.innerWidth * 0.5 || rect.height > 300 ||
                    className.match(/bg|background|cover|hero|banner|full/)) {
                    return img.src;
                }
            }

            // Strategy C: Absolutely positioned images
            const absImgs = heroSection.querySelectorAll('img[style*="absolute"], img[style*="fixed"], [class*="background"] img, [class*="bg"] img');
            for (const img of absImgs) {
                if (img.src) return img.src;
            }

            // Strategy D: Picture/source elements
            const picture = heroSection.querySelector('picture source, picture img');
            if (picture) {
                return picture.srcset?.split(' ')[0] || picture.src;
            }

            // Strategy E: Video poster as background
            const video = heroSection.querySelector('video[poster]');
            if (video && video.poster) {
                return video.poster;
            }

            return null;
        }

        data.background_url = findHeroBackground(heroSection);

        // ============================================
        // STRATEGY 4b: Background Color Detection
        // ============================================
        function findHeroBackgroundColor(heroSection) {
            if (!heroSection) return null;

            const RGB_REGEX = /^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*[\\d.]+)?\\)$/;

            function rgbToHex(rgb) {
                const match = rgb.match(RGB_REGEX);
                if (!match) return null;
                const r = parseInt(match[1], 10);
                const g = parseInt(match[2], 10);
                const b = parseInt(match[3], 10);
                if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
                return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
            }

            function isTransparent(color) {
                if (!color) return true;
                if (color === 'rgba(0, 0, 0, 0)' || color === 'transparent') return true;
                const alphaMatch = color.match(/rgba\\([^)]+,\\s*([\\d.]+)\\)$/);
                if (alphaMatch && parseFloat(alphaMatch[1]) < 0.1) return true;
                return false;
            }

            // Check hero section and ancestors for background color
            let el = heroSection;
            let depth = 0;
            while (el && depth < 5) {
                const styles = getComputedStyle(el);
                const bgColor = styles.backgroundColor;

                if (!isTransparent(bgColor)) {
                    const hex = rgbToHex(bgColor);
                    if (hex) return hex;
                }
                el = el.parentElement;
                depth++;
            }

            // Fallback: check body/html background
            const bodyBg = getComputedStyle(document.body).backgroundColor;
            if (!isTransparent(bodyBg)) {
                const hex = rgbToHex(bodyBg);
                if (hex) return hex;
            }

            // Default to white if nothing found
            return '#ffffff';
        }

        data.background_color = findHeroBackgroundColor(heroSection);

        // ============================================
        // STRATEGY 5: CTA Button Detection
        // ============================================
        const ctaSelectors = [
            'a[class*="btn"]', 'a[class*="cta"]', 'a[class*="button"]',
            'button[class*="cta"]', 'button[class*="primary"]',
            'button', '[class*="button"]', 'a[href*="#"]'
        ];

        // Helper: check if color is dark
        function isDarkColor(color) {
            if (!color) return false;
            const match = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if (!match) return false;
            const r = parseInt(match[1], 10);
            const g = parseInt(match[2], 10);
            const b = parseInt(match[3], 10);
            // Calculate relative luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            return luminance < 0.5;
        }

        // Search in hero section first, then broader
        const searchContainers = [heroSection, document.body];

        for (const container of searchContainers) {
            if (!container) continue;

            for (const selector of ctaSelectors) {
                const ctas = container.querySelectorAll(selector);
                for (const cta of ctas) {
                    const rect = cta.getBoundingClientRect();
                    // Skip if below fold
                    if (rect.top > window.innerHeight * 0.7) continue;
                    // Skip if in nav
                    if (cta.closest('nav, header nav')) continue;

                    const text = cta.innerText.trim();
                    // Look for typical CTA text patterns
                    const ctaPatterns = /book|demo|start|try|get|sign|learn|contact|subscribe|register|buy|order|shop/i;

                    if (text && text.length > 2 && text.length < 50) {
                        const styles = window.getComputedStyle(cta);
                        const bgColor = styles.backgroundColor;

                        // Accept styled buttons OR CTA-like text
                        const hasBackground = bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent';
                        const hasCTAText = ctaPatterns.test(text);

                        if (hasBackground || hasCTAText) {
                            let textColor = styles.color;

                            // Fix: if background is dark and text color is also dark,
                            // use white (browser might return wrong computed color)
                            if (isDarkColor(bgColor) && isDarkColor(textColor)) {
                                textColor = 'rgb(255, 255, 255)';
                            }

                            data.cta_text = text;
                            data.cta_styles = {
                                backgroundColor: bgColor,
                                color: textColor,
                                padding: styles.padding,
                                borderRadius: styles.borderRadius,
                                fontFamily: styles.fontFamily,
                                fontSize: styles.fontSize,
                                fontWeight: styles.fontWeight,
                                textTransform: styles.textTransform,
                                boxShadow: styles.boxShadow !== 'none' ? styles.boxShadow : null
                            };
                            break;
                        }
                    }
                }
                if (data.cta_styles.backgroundColor) break;
            }
            if (data.cta_styles.backgroundColor) break;
        }

        // Clean up internal reference
        delete data._headlineEl;

        return data;
    }''')

    # Capture hero screenshot as fallback background
    hero_screenshot = None
    try:
        hero_locator = page.locator('[class*="hero"], .hero, header, main > section:first-child').first
        if await hero_locator.count() > 0:
            hero_bytes = await hero_locator.screenshot(type="png")
            hero_screenshot = base64.b64encode(hero_bytes).decode('utf-8')
    except Exception as e:
        logger.debug(f"Hero screenshot failed: {e}")
        # Fallback to viewport screenshot
        try:
            hero_bytes = await page.screenshot(
                type="png",
                clip={"x": 0, "y": 0, "width": 1440, "height": 900}
            )
            hero_screenshot = base64.b64encode(hero_bytes).decode('utf-8')
        except Exception:
            pass

    return HeroData(
        headline=hero_data.get("headline", ""),
        subheadline=hero_data.get("subheadline"),
        background_color=hero_data.get("background_color"),
        background_url=hero_data.get("background_url"),
        background_screenshot=hero_screenshot,
        cta_text=hero_data.get("cta_text", "Learn More"),
        cta_styles=hero_data.get("cta_styles", {})
    )


async def _extract_logo(page) -> Optional[str]:
    """Extract logo URL."""
    logo_data = await page.evaluate('''() => {
        const baseUrl = window.location.origin;

        function resolveUrl(url) {
            if (!url) return null;
            if (url.startsWith('data:')) return url;
            if (url.startsWith('http')) return url;
            return new URL(url, baseUrl).href;
        }

        // Try schema.org first
        const ldJsonScripts = document.querySelectorAll('script[type="application/ld+json"]');
        for (const script of ldJsonScripts) {
            try {
                const data = JSON.parse(script.textContent);
                const items = Array.isArray(data) ? data : [data];
                for (const item of items) {
                    if (item.logo) {
                        const logoUrl = typeof item.logo === 'string' ? item.logo : item.logo.url;
                        if (logoUrl) return resolveUrl(logoUrl);
                    }
                }
            } catch (e) {}
        }

        // Try header logo
        const logoSelectors = [
            'header a[href="/"] img',
            'header [class*="logo"] img',
            '[class*="logo"] img',
            'header img[alt*="logo" i]',
            'header img[src*="logo" i]'
        ];

        for (const selector of logoSelectors) {
            const el = document.querySelector(selector);
            if (el && el.src) {
                const rect = el.getBoundingClientRect();
                if (rect.top < 200 && rect.width > 20) {
                    return resolveUrl(el.src);
                }
            }
        }

        // Try SVG logo
        const svgLogo = document.querySelector('header svg, [class*="logo"] svg');
        if (svgLogo) {
            const rect = svgLogo.getBoundingClientRect();
            if (rect.top < 200 && rect.width > 20) {
                const serializer = new XMLSerializer();
                const svgStr = serializer.serializeToString(svgLogo);
                return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
            }
        }

        return null;
    }''')

    return logo_data


async def _extract_brand_assets(page) -> Dict[str, Any]:
    """Extract brand colors, fonts, and CSS variables."""
    return await page.evaluate('''() => {
        const assets = {
            primary_color: "#ffffff",
            secondary_color: "#000000",
            accent_color: "#0066ff",
            font_family: "Inter",
            font_faces: [],
            css_variables: {}
        };

        const RGB_REGEX = /^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*[\\d.]+)?\\)$/;

        function rgbToHex(rgb) {
            let match = rgb.match(RGB_REGEX);
            if (!match) return null;
            const r = parseInt(match[1], 10);
            const g = parseInt(match[2], 10);
            const b = parseInt(match[3], 10);
            if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
            return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
        }

        function isTransparent(color) {
            if (!color) return true;
            if (color === 'rgba(0, 0, 0, 0)' || color === 'transparent') return true;
            const alphaMatch = color.match(/rgba\\([^)]+,\\s*([\\d.]+)\\)$/);
            if (alphaMatch && parseFloat(alphaMatch[1]) < 0.1) return true;
            return false;
        }

        // Extract primary color from hero/header backgrounds
        const bgSelectors = ['[class*="hero"]', '.hero', 'header', 'main > section:first-child'];
        for (const selector of bgSelectors) {
            const el = document.querySelector(selector);
            if (el) {
                const styles = window.getComputedStyle(el);
                if (!isTransparent(styles.backgroundColor)) {
                    const hex = rgbToHex(styles.backgroundColor);
                    if (hex) {
                        assets.primary_color = hex;
                        break;
                    }
                }
            }
        }

        // Extract accent color from CTA buttons
        const ctaSelectors = ['button', '[class*="btn"]', '[class*="cta"]'];
        for (const selector of ctaSelectors) {
            const el = document.querySelector(selector);
            if (el) {
                const styles = window.getComputedStyle(el);
                if (!isTransparent(styles.backgroundColor)) {
                    const hex = rgbToHex(styles.backgroundColor);
                    if (hex && hex !== assets.primary_color) {
                        assets.accent_color = hex;
                        break;
                    }
                }
            }
        }

        // Extract secondary color from text
        const h1 = document.querySelector('h1');
        if (h1) {
            const styles = window.getComputedStyle(h1);
            const hex = rgbToHex(styles.color);
            if (hex) assets.secondary_color = hex;
        }

        // Extract font family
        const textEl = document.querySelector('h1, h2, p');
        if (textEl) {
            const styles = window.getComputedStyle(textEl);
            const fontFamily = styles.fontFamily.split(',')[0].trim().replace(/['"]/g, '');
            if (fontFamily && !['serif', 'sans-serif', 'monospace'].includes(fontFamily.toLowerCase())) {
                assets.font_family = fontFamily;
            }
        }

        // Extract @font-face rules
        for (const sheet of document.styleSheets) {
            try {
                for (const rule of sheet.cssRules) {
                    if (rule.type === CSSRule.FONT_FACE_RULE) {
                        assets.font_faces.push(rule.cssText);
                    }
                }
            } catch (e) {}
        }

        // Extract CSS variables
        const rootStyles = getComputedStyle(document.documentElement);
        for (const prop of rootStyles) {
            if (prop.startsWith('--')) {
                const value = rootStyles.getPropertyValue(prop).trim();
                if (value) assets.css_variables[prop] = value;
            }
        }

        return assets;
    }''')


async def _extract_features(page) -> List[FeatureItem]:
    """Extract features/benefits sections."""
    features_data = await page.evaluate('''() => {
        const features = [];

        // Feature section selectors
        const sectionSelectors = [
            '[class*="feature"]', '[class*="benefit"]',
            '[class*="step"]', '[class*="how"]',
            '[class*="service"]', '[class*="solution"]'
        ];

        // Find feature containers
        let featureContainers = [];
        for (const selector of sectionSelectors) {
            const els = document.querySelectorAll(selector);
            if (els.length > 0) {
                featureContainers = [...els];
                break;
            }
        }

        // If no specific feature sections, look for card-like structures
        if (featureContainers.length === 0) {
            const cards = document.querySelectorAll('[class*="card"], [class*="item"], [class*="box"]');
            featureContainers = [...cards].filter(card => {
                const rect = card.getBoundingClientRect();
                return rect.width > 100 && rect.height > 100 && rect.top > 500;
            });
        }

        // Extract up to 6 features
        for (const container of featureContainers.slice(0, 6)) {
            const feature = { title: "", description: null, icon_url: null };

            // Get title (h3, h4, or first strong text)
            const titleEl = container.querySelector('h3, h4, h5, strong, [class*="title"]');
            if (titleEl) {
                feature.title = titleEl.innerText.trim();
            }

            // Get description
            const descEl = container.querySelector('p, [class*="desc"]');
            if (descEl) {
                feature.description = descEl.innerText.trim().slice(0, 200);
            }

            // Get icon/image
            const iconEl = container.querySelector('img, svg');
            if (iconEl) {
                if (iconEl.tagName === 'IMG' && iconEl.src) {
                    feature.icon_url = iconEl.src;
                } else if (iconEl.tagName === 'SVG' || iconEl.tagName === 'svg') {
                    const serializer = new XMLSerializer();
                    const svgStr = serializer.serializeToString(iconEl);
                    feature.icon_url = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
                }
            }

            if (feature.title) {
                features.push(feature);
            }
        }

        return features;
    }''')

    return [FeatureItem(**f) for f in features_data]


async def _extract_testimonials(page) -> List[TestimonialItem]:
    """Extract testimonials/reviews."""
    testimonials_data = await page.evaluate('''() => {
        const testimonials = [];

        // Testimonial selectors
        const selectors = [
            '[class*="testimonial"]', '[class*="review"]',
            '[class*="quote"]', 'blockquote',
            '[class*="customer"]', '[class*="feedback"]'
        ];

        let containers = [];
        for (const selector of selectors) {
            const els = document.querySelectorAll(selector);
            if (els.length > 0) {
                containers = [...els];
                break;
            }
        }

        // Extract up to 4 testimonials
        for (const container of containers.slice(0, 4)) {
            const testimonial = { quote: "", author: null, company: null, avatar_url: null };

            // Get quote
            const quoteEl = container.querySelector('p, blockquote, [class*="text"], [class*="quote"]');
            if (quoteEl) {
                let quote = quoteEl.innerText.trim();
                // Clean up quote marks
                quote = quote.replace(/^["'""]+|["'""]+$/g, '');
                if (quote.length > 20) {
                    testimonial.quote = quote.slice(0, 300);
                }
            }

            // Get author
            const authorEl = container.querySelector('[class*="author"], [class*="name"], cite, strong');
            if (authorEl) {
                testimonial.author = authorEl.innerText.trim().slice(0, 50);
            }

            // Get company
            const companyEl = container.querySelector('[class*="company"], [class*="role"], [class*="title"]');
            if (companyEl && companyEl !== authorEl) {
                testimonial.company = companyEl.innerText.trim().slice(0, 50);
            }

            // Get avatar
            const avatarEl = container.querySelector('img[class*="avatar"], img[class*="photo"], img[class*="profile"]');
            if (avatarEl && avatarEl.src) {
                testimonial.avatar_url = avatarEl.src;
            }

            if (testimonial.quote) {
                testimonials.push(testimonial);
            }
        }

        return testimonials;
    }''')

    return [TestimonialItem(**t) for t in testimonials_data]


async def _extract_product_screenshots(page) -> List[str]:
    """Extract product screenshots as base64."""
    screenshots = []

    # Try to find product/app screenshots
    screenshot_selectors = [
        '[class*="screenshot"]', '[class*="product"]',
        '[class*="demo"]', '[class*="preview"]',
        '[class*="app"] img', '[class*="interface"]'
    ]

    for selector in screenshot_selectors:
        try:
            elements = await page.locator(selector).all()
            for el in elements[:3]:  # Max 3 screenshots
                try:
                    bbox = await el.bounding_box()
                    if bbox and bbox['width'] > 200 and bbox['height'] > 150:
                        screenshot_bytes = await el.screenshot(type="png")
                        screenshots.append(base64.b64encode(screenshot_bytes).decode('utf-8'))
                except Exception:
                    continue
            if screenshots:
                break
        except Exception:
            continue

    return screenshots[:3]


async def _extract_before_after(page) -> Optional[Dict[str, str]]:
    """Extract before/after or problem/solution content."""
    return await page.evaluate('''() => {
        // Look for before/after or problem/solution sections
        const selectors = [
            ['[class*="before"]', '[class*="after"]'],
            ['[class*="problem"]', '[class*="solution"]'],
            ['[class*="without"]', '[class*="with"]'],
            ['[class*="old"]', '[class*="new"]']
        ];

        for (const [beforeSel, afterSel] of selectors) {
            const beforeEl = document.querySelector(beforeSel);
            const afterEl = document.querySelector(afterSel);

            if (beforeEl && afterEl) {
                const beforeText = beforeEl.innerText.trim().slice(0, 200);
                const afterText = afterEl.innerText.trim().slice(0, 200);

                if (beforeText && afterText) {
                    return { before: beforeText, after: afterText };
                }
            }
        }

        return null;
    }''')
