"""Carousel ad generation service.

Generates value prop carousel ads from AnalysisResult:
- Hook card: brand background + headline + hero product image
- Value prop cards: gradient bg + auto-matched icon + text
- CTA card: price/CTA text + tap to shop

Dynamic card count: min 3, max 5.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

from google import genai

from app.models import (
    AnalysisResult,
    CarouselCard,
    CarouselAd,
)
from app.services.template_renderer import get_template_renderer, AD_DIMENSIONS

logger = logging.getLogger(__name__)

# Max retries for LLM calls
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]

# =====================================
# ICON LIBRARY (Inline SVG for rendering)
# =====================================
# Lucide-style icons, keyed by semantic category.
# Each icon is a simple SVG string that renders at any size.

ICON_LIBRARY: Dict[str, str] = {
    "speed": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    "money": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "time": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "security": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "growth": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "quality": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "automation": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
    "support": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "ease": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "analytics": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "integration": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "team": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "customize": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "global": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "rocket": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>',
}

# Default fallback icon
DEFAULT_ICON = ICON_LIBRARY["quality"]

# Keyword-to-icon mapping for auto-matching
ICON_KEYWORDS: Dict[str, List[str]] = {
    "speed": ["fast", "speed", "quick", "instant", "rapid", "performance", "efficient", "lightning"],
    "money": ["save", "cost", "price", "affordable", "budget", "revenue", "profit", "roi", "money", "cheap", "free", "discount"],
    "time": ["time", "schedule", "hours", "minutes", "deadline", "clock", "calendar", "productivity"],
    "security": ["secur", "safe", "protect", "privacy", "encrypt", "trust", "reliable", "compliance", "gdpr"],
    "growth": ["grow", "scale", "increase", "boost", "improve", "expand", "progress", "results", "success"],
    "quality": ["quality", "premium", "best", "top", "excellent", "superior", "professional", "crafted"],
    "automation": ["automat", "ai", "smart", "intelligent", "machine", "workflow", "process", "bot"],
    "support": ["support", "help", "assist", "chat", "service", "customer", "care", "responsive"],
    "ease": ["easy", "simple", "intuitive", "effortless", "seamless", "user-friendly", "straightforward", "convenient"],
    "analytics": ["analy", "data", "insight", "report", "metric", "dashboard", "track", "measure", "monitor"],
    "integration": ["integrat", "connect", "api", "plugin", "sync", "compatible", "platform", "tool"],
    "team": ["team", "collaborat", "together", "share", "group", "organization", "company", "workplace"],
    "customize": ["custom", "configur", "personal", "tailor", "flexible", "adapt", "option", "setting"],
    "global": ["global", "world", "international", "anywhere", "remote", "location", "country", "language"],
    "heart": ["love", "passion", "care", "wellness", "health", "happy", "joy", "satisfaction"],
    "rocket": ["launch", "start", "deploy", "ship", "release", "go live", "begin", "power"],
}


def match_icon(text: str) -> Tuple[str, str]:
    """Match a value prop text to the best icon from the library.

    Returns:
        Tuple of (icon_name, icon_svg)
    """
    text_lower = text.lower()
    best_match = None
    best_score = 0

    for icon_name, keywords in ICON_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = icon_name

    if best_match and best_score > 0:
        return best_match, ICON_LIBRARY[best_match]

    return "quality", DEFAULT_ICON


async def match_icons_with_llm(
    value_props: List[str],
    available_icons: List[str],
) -> List[str]:
    """Use Gemini to match value props to icons for better semantic matching.

    Falls back to keyword matching on failure.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return [match_icon(vp)[0] for vp in value_props]

    client = genai.Client(api_key=api_key)

    prompt = f"""Match each value proposition to the BEST icon from this list.

Available icons: {', '.join(available_icons)}

Value propositions:
{chr(10).join(f'{i+1}. {vp}' for i, vp in enumerate(value_props))}

Return a JSON array of icon names, one per value prop. Use ONLY icons from the list above.
Example: ["speed", "money", "security"]"""

    try:
        result = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        icons = json.loads(result.text)
        if isinstance(icons, list) and len(icons) == len(value_props):
            # Validate all icons exist in library
            validated = []
            for icon in icons:
                if icon in ICON_LIBRARY:
                    validated.append(icon)
                else:
                    validated.append(match_icon(value_props[len(validated)])[0])
            return validated
    except Exception as e:
        logger.warning(f"LLM icon matching failed, using keyword fallback: {e}")

    return [match_icon(vp)[0] for vp in value_props]


def _get_text_color(bg_color: str) -> str:
    """Return white or black text based on background luminance."""
    try:
        hex_color = bg_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#ffffff"
    except Exception:
        return "#ffffff"


def _darken_color(hex_color: str, factor: float = 0.15) -> str:
    """Darken a hex color by a factor (0-1)."""
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        r = max(0, int(int(hex_color[0:2], 16) * (1 - factor)))
        g = max(0, int(int(hex_color[2:4], 16) * (1 - factor)))
        b = max(0, int(int(hex_color[4:6], 16) * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def _build_card_gradient(primary: str, secondary: str) -> str:
    """Build a subtle gradient for value prop cards."""
    darkened = _darken_color(primary, 0.08)
    return f"linear-gradient(160deg, {primary}, {darkened})"


async def generate_carousel(
    analysis: AnalysisResult,
    scraped_data: Dict[str, Any],
    product_image_url: Optional[str] = None,
    destination_url: str = "",
) -> Tuple[CarouselAd, Dict[str, Any]]:
    """Generate a complete carousel ad from analysis results.

    Args:
        analysis: AnalysisResult from the extraction pipeline.
        scraped_data: Raw scraped data containing CSS assets.
        product_image_url: Optional product image URL for the hook card.
        destination_url: Landing page URL for card links.

    Returns:
        Tuple of (CarouselAd, meta_carousel_json).
    """
    # Extract key data from analysis
    usp = analysis.unique_selling_proposition
    cta_text = analysis.call_to_action or "Learn More"
    sg = analysis.styling_guide

    primary_color = sg.primary_colors[0] if sg.primary_colors else "#ffffff"
    accent_color = sg.secondary_colors[0] if sg.secondary_colors else "#0066ff"
    font_family = sg.font_families[0] if sg.font_families else "Inter"
    text_color = _get_text_color(primary_color)
    accent_text_color = _get_text_color(accent_color)

    # Get brand assets
    css_assets = scraped_data.get("css_assets", {})
    logo_url = analysis.logo.url if analysis.logo else None

    # Build gradient
    gradient_css = None
    if analysis.design_tokens and analysis.design_tokens.gradients:
        grad = analysis.design_tokens.gradients[0]
        colors = grad.get("colors", [])
        if len(colors) >= 2:
            gradient_css = f"linear-gradient(135deg, {colors[0]}, {colors[1]})"

    button_styles = css_assets.get("button_styles", {})
    border_radius = "12px"
    if analysis.design_tokens and analysis.design_tokens.border_radius:
        border_radius = analysis.design_tokens.border_radius

    # Determine value props (from USP + pain points + keywords)
    value_props = _extract_value_props(analysis)
    # Clamp to 1-3 value props (total cards: hook + 1-3 value + cta = 3-5)
    value_props = value_props[:3]
    if not value_props:
        value_props = [usp]

    # Match icons to value props
    available_icons = list(ICON_LIBRARY.keys())
    icon_names = await match_icons_with_llm(
        [vp["title"] for vp in value_props], available_icons
    )

    # Build font faces and css variables for template context
    font_faces = css_assets.get("font_faces", [])
    css_variables = css_assets.get("css_variables", {})

    # Render all cards
    renderer = get_template_renderer()
    s3_service = _get_s3_service()
    cards: List[CarouselCard] = []

    # --- Card 1: Hook ---
    hook_context = {
        "font_faces": font_faces,
        "css_variables": css_variables,
        "primary_color": primary_color,
        "accent_color": accent_color,
        "text_color": text_color,
        "font_family": font_family,
        "gradient": gradient_css,
        "logo_url": logo_url,
        "headline": usp,
        "product_image_url": product_image_url,
    }
    hook_image_url = await _render_and_upload(
        renderer, s3_service, "carousel/hook_card.html", hook_context
    )
    cards.append(CarouselCard(
        card_type="hook",
        headline=usp,
        image_url=hook_image_url,
        link_url=destination_url,
    ))

    # --- Cards 2-N: Value Props ---
    for i, vp in enumerate(value_props):
        icon_name = icon_names[i] if i < len(icon_names) else "quality"
        icon_svg = ICON_LIBRARY.get(icon_name, DEFAULT_ICON)

        card_gradient = _build_card_gradient(primary_color, accent_color)

        vp_context = {
            "font_faces": font_faces,
            "css_variables": css_variables,
            "primary_color": primary_color,
            "accent_color": accent_color,
            "text_color": text_color,
            "accent_text_color": accent_text_color,
            "font_family": font_family,
            "card_gradient": card_gradient,
            "card_index": i + 1,
            "icon_svg": icon_svg,
            "value_prop_title": vp["title"],
            "value_prop_desc": vp.get("description"),
        }
        vp_image_url = await _render_and_upload(
            renderer, s3_service, "carousel/value_prop_card.html", vp_context
        )
        cards.append(CarouselCard(
            card_type="value_prop",
            headline=vp["title"],
            description=vp.get("description"),
            icon_name=icon_name,
            image_url=vp_image_url,
            link_url=destination_url,
        ))

    # --- Final Card: CTA ---
    # Build CTA headline from price or summary
    cta_headline = _build_cta_headline(analysis)
    cta_subtext = "Start your journey today"
    cta_button_text_color = _get_text_color(accent_color)

    cta_context = {
        "font_faces": font_faces,
        "css_variables": css_variables,
        "primary_color": primary_color,
        "accent_color": accent_color,
        "text_color": text_color,
        "cta_button_text_color": cta_button_text_color,
        "font_family": font_family,
        "gradient": gradient_css,
        "border_radius": border_radius,
        "button_styles": button_styles,
        "logo_url": logo_url,
        "cta_headline": cta_headline,
        "cta_subtext": cta_subtext,
        "cta_text": cta_text,
    }
    cta_image_url = await _render_and_upload(
        renderer, s3_service, "carousel/cta_card.html", cta_context
    )
    cards.append(CarouselCard(
        card_type="cta",
        headline=cta_headline,
        description=cta_subtext,
        image_url=cta_image_url,
        link_url=destination_url,
    ))

    # Build primary text (shown above carousel in feed)
    primary_text = _build_primary_text(analysis)

    # Determine brand name
    brand_name = _extract_brand_name(analysis)

    carousel_ad = CarouselAd(
        cards=cards,
        primary_text=primary_text,
        aspect_ratio="1:1",
        brand_name=brand_name,
        destination_url=destination_url,
    )

    # Build Meta API JSON
    meta_json = build_meta_carousel_json(carousel_ad)

    return carousel_ad, meta_json


def _extract_value_props(analysis: AnalysisResult) -> List[Dict[str, str]]:
    """Extract structured value props from analysis data.

    Combines USP fragments, pain points (reframed as benefits), and keywords
    into a list of {title, description} dicts.
    """
    props = []

    # Use pain points reframed as benefits
    for pp in analysis.pain_points[:4]:
        # Reframe pain as benefit
        if len(pp) < 60:
            title = pp
            desc = None
        else:
            # Split long text: first sentence as title, rest as desc
            parts = pp.split(". ", 1)
            title = parts[0]
            desc = parts[1] if len(parts) > 1 else None

        props.append({"title": title, "description": desc})

    # If we don't have enough from pain points, add from keywords
    if len(props) < 2:
        keyword_benefits = [
            kw.title() for kw in analysis.keywords[:3]
            if len(kw) > 3
        ]
        for kb in keyword_benefits:
            if len(props) >= 3:
                break
            props.append({"title": kb, "description": None})

    return props[:3]


def _build_cta_headline(analysis: AnalysisResult) -> str:
    """Build a compelling CTA headline."""
    cta = analysis.call_to_action
    if cta and len(cta) < 40:
        return cta

    # Fall back to a shortened USP
    usp = analysis.unique_selling_proposition
    if len(usp) <= 50:
        return usp

    return usp[:47] + "..."


def _build_primary_text(analysis: AnalysisResult) -> str:
    """Build the primary ad text shown above the carousel."""
    summary = analysis.summary
    usp = analysis.unique_selling_proposition
    cta = analysis.call_to_action

    # Combine into a concise primary text
    text = f"{usp}\n\n{summary[:200]}"
    if cta:
        text += f"\n\n{cta}"

    return text


def _extract_brand_name(analysis: AnalysisResult) -> Optional[str]:
    """Try to extract brand name from analysis keywords."""
    # Keywords often include the brand name as the first keyword
    if analysis.keywords:
        # Brand names are usually short, capitalized single words
        for kw in analysis.keywords[:3]:
            if len(kw.split()) == 1 and len(kw) < 20:
                return kw.title()
    return None


async def _render_and_upload(
    renderer,
    s3_service,
    template_name: str,
    context: Dict[str, Any],
    aspect_ratio: str = "1:1",
) -> Optional[str]:
    """Render a carousel card template and upload to S3.

    Returns the S3 URL or None on failure.
    """
    import uuid

    dimensions = AD_DIMENSIONS.get(aspect_ratio, (1080, 1080))

    try:
        image_bytes = await renderer.render_template(
            template_name, context, dimensions
        )

        campaign_id = f"carousel_{uuid.uuid4().hex[:8]}"
        result = s3_service.upload_image(image_bytes, campaign_id)
        if result.get("success"):
            logger.info(f"Carousel card uploaded: {template_name}")
            return result["url"]
        else:
            logger.warning(f"S3 upload failed for {template_name}: {result.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Failed to render carousel card {template_name}: {e}")
        return None


def _get_s3_service():
    """Lazy import to avoid circular dependency."""
    from app.services.s3 import get_s3_service
    return get_s3_service()


# =====================================
# META API CAROUSEL JSON FORMAT
# =====================================

def build_meta_carousel_json(carousel: CarouselAd) -> Dict[str, Any]:
    """Build Meta Ads API carousel creative format.

    Returns a dict matching the Meta Marketing API `object_story_spec.link_data`
    format for carousel ads.

    See: https://developers.facebook.com/docs/marketing-api/reference/ad-creative
    """
    child_attachments = []
    for card in carousel.cards:
        attachment: Dict[str, Any] = {
            "name": card.headline[:25] if card.headline else "",
            "description": card.description[:30] if card.description else "",
            "link": card.link_url or carousel.destination_url,
        }
        if card.image_url:
            attachment["picture"] = card.image_url

        child_attachments.append(attachment)

    return {
        "object_story_spec": {
            "link_data": {
                "message": carousel.primary_text,
                "link": carousel.destination_url,
                "child_attachments": child_attachments,
                "multi_share_optimized": True,
            }
        },
        "degrees_of_freedom_spec": {
            "creative_features_spec": {
                "standard_enhancements": {
                    "enroll_status": "OPT_OUT",
                }
            }
        },
    }
