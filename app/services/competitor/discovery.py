"""
Competitor Discovery Service
Resolves competitor names to URLs, finds Facebook Page IDs, and scrapes positioning data.
"""

import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

# SSRF protection - same as main scraper
BLOCKED_HOSTS = [
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.", "10.", "172.16.", "172.17.", "172.18.",
    "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
    "172.29.", "172.30.", "172.31.", "192.168.",
]


def _validate_url(url: str) -> str:
    """Validate and sanitize URL."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    hostname = parsed.hostname or ""
    for blocked in BLOCKED_HOSTS:
        if hostname.startswith(blocked) or hostname == blocked:
            raise ValueError(f"Blocked host: {hostname}")

    return url


async def discover_competitor(name_or_url: str) -> Dict[str, Any]:
    """
    Discover a competitor from a name or URL.
    Scrapes their website for positioning, claims, pricing, and differentiators.

    Args:
        name_or_url: Competitor name (e.g., "Mailchimp") or URL

    Returns:
        Dict with url, name, positioning, claims, pricing, differentiators
    """
    # Determine if input is a URL or name
    url = None
    name = name_or_url

    if re.match(r"https?://", name_or_url) or "." in name_or_url:
        url = _validate_url(name_or_url)
        parsed = urlparse(url)
        name = parsed.hostname.replace("www.", "").split(".")[0].capitalize()
    else:
        # Resolve name to URL by trying common patterns
        url = await _resolve_name_to_url(name_or_url)
        if not url:
            return {
                "name": name_or_url,
                "url": None,
                "error": f"Could not resolve URL for '{name_or_url}'",
            }

    logger.info(f"Discovering competitor: {name} at {url}")

    # Scrape the competitor's website
    try:
        scraped = await _scrape_competitor(url)
    except Exception as e:
        logger.error(f"Failed to scrape competitor {url}: {e}")
        return {
            "name": name,
            "url": url,
            "positioning": "",
            "claims": [],
            "pricing": None,
            "differentiators": [],
            "error": str(e),
        }

    return {
        "name": name,
        "url": url,
        "positioning": scraped.get("positioning", ""),
        "claims": scraped.get("claims", []),
        "pricing": scraped.get("pricing"),
        "differentiators": scraped.get("differentiators", []),
        "full_text": scraped.get("full_text", ""),
    }


async def _resolve_name_to_url(name: str) -> Optional[str]:
    """Try to resolve a company name to its website URL."""
    # Try common TLDs
    candidates = [
        f"https://www.{name.lower().replace(' ', '')}.com",
        f"https://{name.lower().replace(' ', '')}.com",
        f"https://www.{name.lower().replace(' ', '')}.io",
        f"https://{name.lower().replace(' ', '')}.io",
    ]

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for candidate in candidates:
            try:
                resp = await client.head(candidate)
                if resp.status_code < 400:
                    logger.info(f"Resolved '{name}' to {candidate}")
                    return candidate
            except Exception:
                continue

    logger.warning(f"Could not resolve URL for '{name}'")
    return None


async def resolve_facebook_page_id(
    url: str, access_token: Optional[str] = None
) -> Optional[str]:
    """
    Try to find a Facebook Page ID for a given website URL.
    Uses the Graph API page search if access_token is provided.

    Args:
        url: Website URL to look up
        access_token: Meta API access token (optional)

    Returns:
        Facebook Page ID or None
    """
    if not access_token:
        return None

    parsed = urlparse(url)
    domain = parsed.hostname.replace("www.", "") if parsed.hostname else ""

    try:
        async with httpx.AsyncClient() as client:
            # Search for pages matching the domain
            resp = await client.get(
                "https://graph.facebook.com/v18.0/pages/search",
                params={
                    "q": domain,
                    "fields": "id,name,website,link",
                    "access_token": access_token,
                },
                timeout=15.0,
            )
            data = resp.json()

            if "error" in data:
                logger.warning(f"FB page search error: {data['error']}")
                return None

            # Try to match by website URL
            for page in data.get("data", []):
                page_website = (page.get("website") or "").lower()
                if domain.lower() in page_website:
                    logger.info(f"Found FB page for {domain}: {page['id']}")
                    return page["id"]

            # Return first result as best guess
            if data.get("data"):
                first = data["data"][0]
                logger.info(f"Best guess FB page for {domain}: {first['id']} ({first.get('name')})")
                return first["id"]

    except Exception as e:
        logger.warning(f"Failed to resolve FB page for {url}: {e}")

    return None


async def _scrape_competitor(url: str) -> Dict[str, Any]:
    """Scrape competitor website for positioning data."""
    url = _validate_url(url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.set_extra_http_headers({
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            })

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Extract key data
            data = await page.evaluate("""() => {
                const getText = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.textContent.trim() : '';
                };

                // Get all heading text
                const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
                    .map(h => h.textContent.trim())
                    .filter(t => t.length > 3 && t.length < 200);

                // Get meta description
                const metaDesc = document.querySelector('meta[name="description"]');
                const description = metaDesc ? metaDesc.content : '';

                // Get page title
                const title = document.title || '';

                // Get all visible text (first 5000 chars)
                const body = document.body.innerText || '';
                const fullText = body.substring(0, 5000);

                // Look for pricing indicators
                const pricingKeywords = ['pricing', 'plans', 'free', '/month', '/year', '$'];
                const hasPricing = pricingKeywords.some(k =>
                    fullText.toLowerCase().includes(k)
                );

                return {
                    title,
                    description,
                    headings,
                    fullText,
                    hasPricing
                };
            }""")

            # Extract positioning from title + description + h1
            positioning = data.get("description", "") or data.get("title", "")
            claims = [h for h in data.get("headings", []) if len(h) > 10][:10]

            return {
                "positioning": positioning,
                "claims": claims,
                "pricing": "detected" if data.get("hasPricing") else None,
                "differentiators": claims[:5],
                "full_text": data.get("fullText", ""),
            }

        except PlaywrightTimeoutError:
            logger.error(f"Timeout scraping {url}")
            raise ValueError(f"Page load timeout for {url}")
        finally:
            await browser.close()
