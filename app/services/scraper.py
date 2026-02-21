from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Dict, Any
from urllib.parse import urlparse
import re
import logging
import base64

logger = logging.getLogger(__name__)

# Blocked hosts for SSRF protection
BLOCKED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.",  # Link-local
    "10.",       # Private
    "172.16.",   # Private
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.", # Private
]


def validate_url(url: str) -> str:
    """
    Validate and sanitize URL input.
    Raises ValueError if URL is invalid or blocked.
    Returns sanitized URL.
    """
    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # Validate scheme
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Only http/https allowed.")

    # Validate netloc (domain)
    if not parsed.netloc:
        raise ValueError("Invalid URL: missing domain")

    # Extract domain (remove port if present)
    domain = parsed.netloc.lower().split(":")[0]

    # SSRF protection - block internal/private addresses (check BEFORE domain format)
    for blocked in BLOCKED_HOSTS:
        if domain.startswith(blocked) or domain == blocked.rstrip("."):
            raise ValueError("Internal addresses not allowed")

    # Basic domain validation (after SSRF check)
    if not re.match(r"^[\w.-]+\.[a-zA-Z]{2,}$", domain):
        raise ValueError("Invalid domain format")

    return url


async def navigate_with_fallback(page, url: str) -> str:
    """Navigate with fallback for sites that never reach networkidle."""
    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
    except PlaywrightTimeoutError:
        # Retry once with shorter timeout, no networkidle attempt
        logger.warning(f"Initial load timeout for {url}, retrying...")
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        return "domcontentloaded_retry"

    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
        return "networkidle"
    except PlaywrightTimeoutError:
        logger.debug(f"networkidle timeout for {url}, proceeding")

    try:
        await page.wait_for_load_state("load", timeout=5000)
        return "load"
    except PlaywrightTimeoutError:
        pass

    return "domcontentloaded"


async def scrape_landing_page(url: str) -> Dict[str, Any]:
    """
    Scrapes a landing page URL for text content and metadata using Playwright.
    Returns a dictionary with title, description, headers, and body text.
    """
    # Validate and sanitize URL
    url = validate_url(url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Set a generic user agent to avoid basic bot blocking
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            # Navigate with tiered fallback for sites that never reach networkidle
            load_strategy = await navigate_with_fallback(page, url)
            logger.info(f"Page loaded via {load_strategy} for {url}")
            
            # Extract html lang attribute
            html_lang = await page.evaluate("() => document.documentElement.lang || ''")

            # Extract basic metadata
            title = await page.title()
            
            # description
            description = await page.evaluate('''() => {
                const meta = document.querySelector('meta[name="description"]');
                return meta ? meta.content : "";
            }''')
            
            # og:image
            og_image = await page.evaluate('''() => {
                const meta = document.querySelector('meta[property="og:image"]');
                return meta ? meta.content : "";
            }''')
            
            # Main Headers (H1, H2)
            headers = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('h1, h2')).map(h => h.innerText);
            }''')
            
            # Body Text (Simplified extraction)
            # We grab all paragraph text, filtering out short/empty ones
            # Also include divs with text content for SPA sites
            body_text = await page.evaluate('''() => {
                const texts = [];
                const seen = new Set();

                // Get text from various elements (SPAs often use divs)
                const elements = document.querySelectorAll('p, li, span, div, article, section');
                elements.forEach(el => {
                    // Skip if element has many children (container divs)
                    if (el.children.length > 3) return;

                    const text = el.innerText?.trim();
                    // Lower threshold for more content, deduplicate
                    if (text && text.length > 20 && !seen.has(text)) {
                        seen.add(text);
                        texts.push(text);
                    }
                });

                // Take more chunks but limit total characters
                return texts.slice(0, 30).join('\\n').slice(0, 6000);
            }''')

            logger.debug(f"Scraped body text length: {len(body_text)} chars")
            
            # Extract Styling Information
            styling_data = await page.evaluate('''() => {
                const backgrounds = new Set();
                const textColors = new Set();
                const accents = new Set();
                const fonts = new Set();

                // Pre-compile regex outside hot loop for performance
                const RGB_REGEX = /^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*[\\d.]+)?\\)$/;

                // Helper to convert rgb/rgba to hex
                function rgbToHex(rgb) {
                    let match = rgb.match(RGB_REGEX);
                    if (!match) return null;
                    const r = parseInt(match[1], 10);
                    const g = parseInt(match[2], 10);
                    const b = parseInt(match[3], 10);
                    // Validate parsed values to prevent NaN hex
                    if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
                    const hex = (r, g, b) => '#' + [r, g, b].map(x => {
                        const h = x.toString(16);
                        return h.length === 1 ? '0' + h : h;
                    }).join('');
                    return hex(r, g, b);
                }

                // Check if color is transparent or nearly transparent
                function isTransparent(color) {
                    if (!color) return true;
                    if (color === 'rgba(0, 0, 0, 0)' || color === 'transparent') return true;
                    const alphaMatch = color.match(/rgba\\([^)]+,\\s*([\\d.]+)\\)$/);
                    if (alphaMatch && parseFloat(alphaMatch[1]) < 0.1) return true;
                    return false;
                }

                // Convert hex to HSL for color analysis (only need S and L for scoring)
                function hexToHSL(hex) {
                    // Guard: validate hex format
                    if (!hex || hex.length !== 7 || hex[0] !== '#') return { s: 0, l: 0.5 };
                    const r = parseInt(hex.slice(1,3), 16) / 255;
                    const g = parseInt(hex.slice(3,5), 16) / 255;
                    const b = parseInt(hex.slice(5,7), 16) / 255;
                    if (isNaN(r) || isNaN(g) || isNaN(b)) return { s: 0, l: 0.5 };
                    const max = Math.max(r, g, b), min = Math.min(r, g, b);
                    let s, l = (max + min) / 2;
                    if (max === min) { s = 0; }
                    else { const d = max - min; s = l > 0.5 ? d / (2 - max - min) : d / (max + min); }
                    return { s, l };
                }

                // Score colors by visual prominence (vibrant first, dark/white last)
                // Returns 0-1.1 where higher = more visually prominent
                function colorScore(hex) {
                    const { s, l } = hexToHSL(hex);
                    // lightnessScore: 1 for mid-range (15-85%), 0.1 for near-black/white
                    // This deprioritizes pure black text and white backgrounds
                    const lightnessScore = (l > 0.15 && l < 0.85) ? 1 : 0.1;
                    // Final score: saturation + 0.1 baseline, scaled by lightness
                    // +0.1 prevents zero score for achromatic colors (grays)
                    return (s + 0.1) * lightnessScore;
                }

                // Helper to check if we have enough colors
                function hasEnoughColors() {
                    return backgrounds.size >= 5 && textColors.size >= 5 && accents.size >= 5;
                }

                // Extract background colors from container elements
                const bgSelectors = ['body', 'main', 'section', 'header', '.hero', '[class*="hero"]', '[class*="banner"]', '[class*="header"]', '[class*="section"]'];
                bgSelectors.forEach(selector => {
                    if (hasEnoughColors()) return;
                    document.querySelectorAll(selector).forEach(el => {
                        if (hasEnoughColors()) return;
                        const styles = window.getComputedStyle(el);
                        const bgColor = styles.backgroundColor;
                        if (!isTransparent(bgColor)) {
                            const hex = rgbToHex(bgColor);
                            if (hex) backgrounds.add(hex);
                        }
                    });
                });

                // Extract text colors from content elements
                const textSelectors = ['h1', 'h2', 'h3', 'p', 'span', 'li'];
                textSelectors.forEach(selector => {
                    if (hasEnoughColors()) return;
                    document.querySelectorAll(selector).forEach(el => {
                        if (hasEnoughColors()) return;
                        const styles = window.getComputedStyle(el);
                        const color = styles.color;
                        if (!isTransparent(color)) {
                            const hex = rgbToHex(color);
                            if (hex) textColors.add(hex);
                        }

                        // Fonts
                        const fontFamily = styles.fontFamily;
                        if (fontFamily) {
                            const cleanFonts = fontFamily.split(',').map(f =>
                                f.trim().replace(/['"]/g, '')
                            );
                            cleanFonts.forEach(f => {
                                if (f && !f.includes('serif') && !f.includes('sans-serif') && !f.includes('monospace')) {
                                    fonts.add(f);
                                }
                            });
                        }
                    });
                });

                // Extract accent colors from CTAs/buttons
                const accentSelectors = ['button', 'a.cta', '.cta', '[class*="button"]', '[class*="btn"]', 'a[href]'];
                accentSelectors.forEach(selector => {
                    if (hasEnoughColors()) return;
                    document.querySelectorAll(selector).forEach(el => {
                        if (hasEnoughColors()) return;
                        const styles = window.getComputedStyle(el);
                        const bgColor = styles.backgroundColor;
                        const color = styles.color;
                        if (!isTransparent(bgColor)) {
                            const hex = rgbToHex(bgColor);
                            if (hex) accents.add(hex);
                        }
                        if (!isTransparent(color)) {
                            const hex = rgbToHex(color);
                            // Only add text color if it's not black/white (likely styled)
                            if (hex && hex !== '#000000' && hex !== '#ffffff') {
                                accents.add(hex);
                            }
                        }
                    });
                });

                // Sort backgrounds by visual prominence (vibrant colors first)
                const sortedBgs = Array.from(backgrounds)
                    .map(c => ({ hex: c, score: colorScore(c) }))
                    .sort((a, b) => b.score - a.score)
                    .map(c => c.hex);

                // Sort accents by visual prominence too
                const sortedAccents = Array.from(accents)
                    .map(c => ({ hex: c, score: colorScore(c) }))
                    .sort((a, b) => b.score - a.score)
                    .map(c => c.hex);

                return {
                    backgrounds: sortedBgs.slice(0, 5),
                    text: Array.from(textColors).slice(0, 5),
                    accents: sortedAccents.slice(0, 5),
                    // Keep legacy 'colors' for backward compatibility
                    colors: [...new Set([...sortedBgs, ...textColors, ...sortedAccents])].slice(0, 10),
                    fonts: Array.from(fonts).slice(0, 5)
                };
            }''')

            # Extract logo with multi-phase detection
            logo_data = await page.evaluate('''() => {
                const candidates = [];
                const baseUrl = window.location.origin;

                // Helper: resolve relative URLs
                function resolveUrl(url) {
                    if (!url) return null;
                    if (url.startsWith('data:')) return url;
                    if (url.startsWith('http')) return url;
                    return new URL(url, baseUrl).href;
                }

                // Helper: get element position
                function getPosition(el) {
                    const rect = el.getBoundingClientRect();
                    return { top: rect.top, left: rect.left, width: rect.width, height: rect.height };
                }

                // Helper: calculate logo score
                function scoreLogo(el, pos, src, source) {
                    let score = 0;

                    // Position score (30pts): top < 200px, left < 50%
                    if (pos.top < 200) score += 20;
                    if (pos.top < 100) score += 10;
                    if (pos.left < window.innerWidth / 2) score += 10;

                    // Size score (30pts): 50-400px width, 20-150px height
                    if (pos.width >= 50 && pos.width <= 400) score += 15;
                    if (pos.height >= 20 && pos.height <= 150) score += 15;

                    // Naming score (20pts): 'logo' or 'brand' in src/alt/class
                    const searchStr = (src + (el.alt || '') + (el.className || '')).toLowerCase();
                    if (searchStr.includes('logo')) score += 15;
                    if (searchStr.includes('brand')) score += 5;

                    // Format score (20pts): SVG > PNG > JPEG
                    if (el.tagName === 'SVG' || src.endsWith('.svg')) score += 20;
                    else if (src.includes('.png')) score += 15;
                    else if (src.includes('.jpg') || src.includes('.jpeg')) score += 10;

                    // Source priority bonus
                    if (source === 'schema') score += 30;
                    else if (source === 'header') score += 15;
                    else if (source === 'favicon') score += 5;

                    return score;
                }

                // Phase 1: Schema.org Detection (high confidence)
                try {
                    const ldJsonScripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of ldJsonScripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            const items = Array.isArray(data) ? data : [data];
                            for (const item of items) {
                                if (item.logo) {
                                    const logoUrl = typeof item.logo === 'string' ? item.logo : item.logo.url;
                                    if (logoUrl) {
                                        candidates.push({
                                            url: resolveUrl(logoUrl),
                                            source: 'schema',
                                            confidence: 'high',
                                            score: 100
                                        });
                                    }
                                }
                            }
                        } catch (e) {}
                    }
                } catch (e) {}

                // Phase 2: Header Image Detection (medium confidence)
                const headerSelectors = [
                    'header a[href="/"] img',
                    'header a[href="./"] img',
                    'header [class*="logo"] img',
                    '[class*="logo"] img',
                    'header img[alt*="logo" i]',
                    'header img[src*="logo" i]',
                    'a[href="/"] img[src*="logo" i]',
                    'header svg',
                    '[class*="logo"] svg'
                ];

                for (const selector of headerSelectors) {
                    const els = document.querySelectorAll(selector);
                    for (const el of els) {
                        const pos = getPosition(el);
                        if (pos.top > 300 || pos.width < 20) continue;

                        let src = '';
                        let type = 'unknown';

                        if (el.tagName === 'IMG') {
                            src = el.src;
                            type = src.split('.').pop()?.split('?')[0] || 'png';
                        } else if (el.tagName === 'SVG' || el.tagName === 'svg') {
                            // Serialize SVG
                            const serializer = new XMLSerializer();
                            const svgStr = serializer.serializeToString(el);
                            src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
                            type = 'svg';
                        }

                        if (src) {
                            candidates.push({
                                url: resolveUrl(src),
                                source: 'header',
                                confidence: 'medium',
                                type: type,
                                width: Math.round(pos.width),
                                height: Math.round(pos.height),
                                score: scoreLogo(el, pos, src, 'header')
                            });
                        }
                    }
                }

                // Phase 3: Favicon Fallback (low confidence)
                const faviconSelectors = [
                    'link[rel="icon"][sizes="180x180"]',
                    'link[rel="apple-touch-icon"]',
                    'link[rel="icon"][sizes="192x192"]',
                    'link[rel="icon"][sizes="96x96"]',
                    'link[rel="icon"]'
                ];

                for (const selector of faviconSelectors) {
                    const link = document.querySelector(selector);
                    if (link && link.href) {
                        candidates.push({
                            url: resolveUrl(link.href),
                            source: 'favicon',
                            confidence: 'low',
                            type: link.href.split('.').pop()?.split('?')[0] || 'ico',
                            score: 10
                        });
                        break; // Only take first/best favicon
                    }
                }

                // Return best candidate
                if (candidates.length === 0) return null;

                candidates.sort((a, b) => b.score - a.score);
                const best = candidates[0];

                return {
                    url: best.url,
                    type: best.type || best.url?.split('.').pop()?.split('?')[0] || 'unknown',
                    source: best.source,
                    confidence: best.confidence,
                    width: best.width || null,
                    height: best.height || null,
                    score: best.score
                };
            }''')

            # Extract CSS assets for HTML template rendering
            css_assets = await page.evaluate('''() => {
                const assets = {
                    font_faces: [],
                    css_variables: {},
                    button_styles: {}
                };

                // 1. Extract @font-face rules
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.type === CSSRule.FONT_FACE_RULE) {
                                assets.font_faces.push(rule.cssText);
                            }
                        }
                    } catch (e) {} // CORS restrictions on external stylesheets
                }

                // 2. Extract CSS custom properties from :root
                const rootStyles = getComputedStyle(document.documentElement);
                for (const prop of rootStyles) {
                    if (prop.startsWith('--')) {
                        const value = rootStyles.getPropertyValue(prop).trim();
                        if (value) {
                            assets.css_variables[prop] = value;
                        }
                    }
                }

                // 3. Extract CTA/button computed styles
                const ctaSelectors = [
                    'button.cta', '.cta', '[class*="btn-primary"]',
                    'a.cta', '[class*="hero"] button', 'button',
                    '[class*="btn"]', 'a[class*="button"]'
                ];

                // Helper to check if element looks like a styled button
                function isStyledButton(el) {
                    const styles = getComputedStyle(el);
                    const bgColor = styles.backgroundColor;
                    const padding = styles.padding;
                    const borderRadius = styles.borderRadius;

                    // Has visible background (not transparent)
                    const hasBg = bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent';
                    // Has meaningful padding (indicates button styling)
                    const hasPadding = padding && !padding.match(/^0(px)?$/);
                    // Has border radius (common for buttons)
                    const hasBorderRadius = borderRadius && borderRadius !== '0px';

                    return hasBg || (hasPadding && hasBorderRadius);
                }

                for (const selector of ctaSelectors) {
                    const ctas = document.querySelectorAll(selector);
                    for (const cta of ctas) {
                        if (isStyledButton(cta)) {
                            const styles = getComputedStyle(cta);
                            assets.button_styles = {
                                backgroundColor: styles.backgroundColor,
                                color: styles.color,
                                padding: styles.padding,
                                borderRadius: styles.borderRadius,
                                fontFamily: styles.fontFamily,
                                fontSize: styles.fontSize,
                                fontWeight: styles.fontWeight,
                                textTransform: styles.textTransform,
                                boxShadow: styles.boxShadow !== 'none' ? styles.boxShadow : null,
                                border: styles.border !== 'none' ? styles.border : null
                            };
                            break; // Found a valid CTA
                        }
                    }
                    if (Object.keys(assets.button_styles).length > 0) break;
                }

                return assets;
            }''')

            # Extract design tokens (gradients, shadows, border-radius)
            design_tokens = await page.evaluate('''() => {
                const tokens = {
                    gradients: [],
                    border_radius: null,
                    box_shadow: null,
                    common_radius: {}
                };

                // Helper to parse gradient
                function parseGradient(bg) {
                    if (!bg || !bg.includes('gradient')) return null;
                    const match = bg.match(/(linear|radial)-gradient\\(([^)]+)\\)/);
                    if (!match) return null;

                    // Extract colors from gradient
                    const colorMatches = bg.match(/(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}|rgba?\\([^)]+\\))/g);
                    return {
                        type: match[1],
                        raw: bg,
                        colors: colorMatches || []
                    };
                }

                // Scan key elements for design tokens
                const selectors = ['header', '.hero', '[class*="hero"]', 'section', 'main', 'button', '[class*="btn"]'];
                const radiusCounts = {};

                for (const selector of selectors) {
                    const els = document.querySelectorAll(selector);
                    for (const el of els) {
                        const styles = window.getComputedStyle(el);

                        // Gradients
                        const bg = styles.backgroundImage;
                        const gradient = parseGradient(bg);
                        if (gradient && tokens.gradients.length < 3) {
                            tokens.gradients.push(gradient);
                        }

                        // Border radius (track most common)
                        const radius = styles.borderRadius;
                        if (radius && radius !== '0px') {
                            radiusCounts[radius] = (radiusCounts[radius] || 0) + 1;
                        }

                        // Box shadow (first non-none found)
                        const shadow = styles.boxShadow;
                        if (!tokens.box_shadow && shadow && shadow !== 'none') {
                            tokens.box_shadow = shadow;
                        }
                    }
                }

                // Find most common border radius
                let maxCount = 0;
                for (const [radius, count] of Object.entries(radiusCounts)) {
                    if (count > maxCount) {
                        maxCount = count;
                        tokens.border_radius = radius;
                    }
                }

                return tokens;
            }''')

            # Capture hero screenshot (ephemeral - in memory only)
            hero_screenshot = None
            try:
                # Try to capture hero section
                hero_locator = page.locator('header, .hero, [class*="hero"], main > section:first-child').first
                if await hero_locator.count() > 0:
                    hero_screenshot = await hero_locator.screenshot(type="png")
                    hero_screenshot = base64.b64encode(hero_screenshot).decode('utf-8')
                    logger.debug("Captured hero screenshot")
            except Exception as e:
                logger.debug(f"Hero screenshot capture failed: {e}")
                # Fallback: capture viewport
                try:
                    hero_screenshot = await page.screenshot(type="png", clip={"x": 0, "y": 0, "width": 1200, "height": 800})
                    hero_screenshot = base64.b64encode(hero_screenshot).decode('utf-8')
                    logger.debug("Captured viewport screenshot as fallback")
                except Exception as e2:
                    logger.debug(f"Viewport screenshot failed: {e2}")

            return {
                "title": title,
                "description": description,
                "og_image": og_image,
                "headers": headers,
                "styling": styling_data,
                "logo": logo_data,
                "design_tokens": design_tokens,
                "css_assets": css_assets,  # For HTML template rendering
                "hero_screenshot": hero_screenshot,  # Base64 encoded, ephemeral
                "language": html_lang.split("-")[0].lower() if html_lang else None,
                # Combined context for the LLM
                "full_text": f"Title: {title}\nDescription: {description}\nHeaders: {headers}\nContent: {body_text}"
            }
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Total timeout scraping {url}: {e}")
            raise ValueError("Page load timeout: The URL took too long to respond")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}", exc_info=True)
            raise ValueError(f"Failed to scrape URL: {str(e)}")
        finally:
            await browser.close()
