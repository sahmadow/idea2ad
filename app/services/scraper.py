from playwright.async_api import async_playwright
from typing import Dict, Any
from urllib.parse import urlparse
import re
import logging

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
            
            # Wait for network to be idle to ensure JavaScript content loads
            await page.goto(url, timeout=30000, wait_until="networkidle")
            
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
                const colors = new Set();
                const fonts = new Set();
                
                // Helper to convert rgb to hex
                function rgbToHex(rgb) {
                    const match = rgb.match(/^rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)$/);
                    if (!match) return null;
                    const hex = (r, g, b) => '#' + [r, g, b].map(x => {
                        const hex = parseInt(x).toString(16);
                        return hex.length === 1 ? '0' + hex : hex;
                    }).join('');
                    return hex(match[1], match[2], match[3]);
                }
                
                // Extract colors and fonts from key elements
                const selectors = ['h1', 'h2', 'h3', 'p', 'button', 'a', '.cta', '[class*="button"]', '[class*="btn"]'];
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const styles = window.getComputedStyle(el);
                        
                        // Colors
                        const color = styles.color;
                        const bgColor = styles.backgroundColor;
                        if (color && color !== 'rgba(0, 0, 0, 0)') {
                            const hex = rgbToHex(color);
                            if (hex) colors.add(hex);
                        }
                        if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
                            const hex = rgbToHex(bgColor);
                            if (hex) colors.add(hex);
                        }
                        
                        // Fonts
                        const fontFamily = styles.fontFamily;
                        if (fontFamily) {
                            // Clean up font family string
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
                
                return {
                    colors: Array.from(colors).slice(0, 10),
                    fonts: Array.from(fonts).slice(0, 5)
                };
            }''')

            return {
                "title": title,
                "description": description,
                "og_image": og_image,
                "headers": headers,
                "styling": styling_data,
                # Combined context for the LLM
                "full_text": f"Title: {title}\nDescription: {description}\nHeaders: {headers}\nContent: {body_text}"
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}", exc_info=True)
            # Re-raise so the caller knows scraping failed
            raise ValueError(f"Failed to scrape URL: {str(e)}")
        finally:
            await browser.close()
