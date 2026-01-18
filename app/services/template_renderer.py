"""HTML template renderer for ad creatives using Jinja2 + Playwright."""

from jinja2 import Environment, PackageLoader, select_autoescape
from playwright.async_api import async_playwright
from typing import Optional, List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Supported ad dimensions
AD_DIMENSIONS = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
}

# Map approach names to template files
TEMPLATE_MAP = {
    "product-focused": "product_focused.html",
    "lifestyle": "lifestyle.html",
    "problem-solution": "problem_solution.html",
    "testimonial": "product_focused.html",  # Fallback
    "benefit-driven": "product_focused.html",  # Fallback
}


class TemplateRenderer:
    """Render HTML ad templates to PNG using Playwright."""

    def __init__(self):
        self._browser = None
        self._playwright = None
        self.env = Environment(
            loader=PackageLoader("app.templates", "ad_templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def _ensure_browser(self):
        """Lazy-initialize browser for reuse."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        dimensions: Tuple[int, int] = (1080, 1080),
        device_scale_factor: int = 2,
    ) -> bytes:
        """
        Render HTML template to PNG bytes.

        Args:
            template_name: Name of template file in ad_templates/
            context: Jinja2 template context variables
            dimensions: (width, height) tuple
            device_scale_factor: DPI multiplier (2 = retina quality)

        Returns:
            PNG image bytes
        """
        template = self.env.get_template(template_name)
        html = template.render(**context, width=dimensions[0], height=dimensions[1])

        browser = await self._ensure_browser()
        page = await browser.new_page(
            viewport={"width": dimensions[0], "height": dimensions[1]},
            device_scale_factor=device_scale_factor,
        )

        try:
            await page.set_content(html, wait_until="networkidle")
            # Wait for fonts to load
            try:
                await page.wait_for_function("document.fonts.ready", timeout=5000)
            except Exception:
                logger.warning("Font loading timeout, proceeding anyway")

            screenshot = await page.screenshot(type="png")
            logger.info(
                f"Rendered template {template_name}: {dimensions[0]}x{dimensions[1]}"
            )
            return screenshot
        finally:
            await page.close()

    async def render_ad_from_brief(
        self,
        brief: Any,  # ImageBrief
        brand_css: Dict[str, Any],
        logo_url: Optional[str] = None,
        design_tokens: Optional[Dict[str, Any]] = None,
        aspect_ratio: str = "1:1",
        pain_points: Optional[List[str]] = None,
        product_image_url: Optional[str] = None,
    ) -> bytes:
        """
        Render ad from ImageBrief using HTML template.

        Args:
            brief: ImageBrief object with text_overlays and approach
            brand_css: Dict with font_faces, css_variables, button_styles, colors
            logo_url: Optional logo URL to include
            design_tokens: Optional design tokens (gradients, border_radius)
            aspect_ratio: "1:1", "4:5", or "9:16"
            pain_points: List of pain points from analysis
            product_image_url: Optional URL to transparent product image

        Returns:
            PNG image bytes
        """
        # Select template based on approach
        template_name = TEMPLATE_MAP.get(brief.approach, "product_focused.html")
        dimensions = AD_DIMENSIONS.get(aspect_ratio, (1080, 1080))

        # Extract colors with fallbacks
        primary_colors = brand_css.get("primary_colors", ["#ffffff"])
        secondary_colors = brand_css.get("secondary_colors", ["#000000"])
        font_families = brand_css.get("font_families", ["Inter"])

        # Build gradient CSS if available
        gradient_css = None
        if design_tokens and design_tokens.get("gradients"):
            grad = design_tokens["gradients"][0]
            colors = grad.get("colors", [])
            if len(colors) >= 2:
                gradient_css = f"linear-gradient(135deg, {colors[0]}, {colors[1]})"

        # Extract headline and CTA from overlays
        headline = self._extract_headline(brief.text_overlays)
        subheadline = self._extract_subheadline(brief.text_overlays)
        cta_text = self._extract_cta(brief.text_overlays)

        # Build template context
        context = {
            # CSS injection
            "font_faces": brand_css.get("font_faces", []),
            "css_variables": brand_css.get("css_variables", {}),
            # Colors
            "primary_color": primary_colors[0] if primary_colors else "#ffffff",
            "accent_color": secondary_colors[0] if secondary_colors else "#000000",
            "text_color": self._get_text_color(primary_colors[0] if primary_colors else "#ffffff"),
            "gradient": gradient_css,
            # Typography
            "font_family": font_families[0] if font_families else "Inter",
            # Button styles
            "button_styles": brand_css.get("button_styles", {}),
            # Design tokens
            "border_radius": design_tokens.get("border_radius", "8px") if design_tokens else "8px",
            # Content
            "headline": headline,
            "subheadline": subheadline,
            "cta_text": cta_text,
            "logo_url": logo_url,
            "text_overlays": [o.model_dump() if hasattr(o, "model_dump") else o for o in brief.text_overlays],
            # Pain point (first from list)
            "pain_point": pain_points[0] if pain_points else None,
            # Product image
            "product_image_url": product_image_url,
        }

        return await self.render_template(template_name, context, dimensions)

    def _extract_headline(self, overlays: List[Any]) -> str:
        """Extract headline from text overlays (largest/first)."""
        for o in overlays:
            overlay = o if isinstance(o, dict) else (o.model_dump() if hasattr(o, "model_dump") else {"content": str(o)})
            font_size = overlay.get("font_size", "")
            if font_size in ["large", "xlarge", "xxlarge"]:
                return overlay.get("content", "")
        # Fallback to first overlay
        if overlays:
            first = overlays[0]
            if isinstance(first, dict):
                return first.get("content", "")
            elif hasattr(first, "content"):
                return first.content
        return ""

    def _extract_subheadline(self, overlays: List[Any]) -> Optional[str]:
        """Extract subheadline (medium-sized text), excluding CTA text."""
        cta_keywords = ["learn", "get", "try", "start", "buy", "shop", "sign", "join", "discover"]
        for o in overlays:
            overlay = o if isinstance(o, dict) else (o.model_dump() if hasattr(o, "model_dump") else {"content": str(o)})
            font_size = overlay.get("font_size", "")
            content = overlay.get("content", "")
            # Skip if this looks like a CTA
            if any(kw in content.lower() for kw in cta_keywords):
                continue
            if font_size in ["medium"]:
                return content
        return None

    def _extract_cta(self, overlays: List[Any]) -> str:
        """Extract CTA text from overlays."""
        cta_keywords = ["learn", "get", "try", "start", "buy", "shop", "sign", "join", "discover"]
        for o in overlays:
            overlay = o if isinstance(o, dict) else (o.model_dump() if hasattr(o, "model_dump") else {"content": str(o)})
            content = overlay.get("content", "").lower()
            if any(kw in content for kw in cta_keywords):
                return overlay.get("content", "Learn More")
        return "Learn More"

    def _get_text_color(self, bg_color: str) -> str:
        """Return white or black text based on background luminance."""
        try:
            # Parse hex color
            hex_color = bg_color.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join([c * 2 for c in hex_color])
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Calculate relative luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#ffffff"
        except Exception:
            return "#ffffff"

    async def close(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# Singleton instance
_renderer: Optional[TemplateRenderer] = None


def get_template_renderer() -> TemplateRenderer:
    """Get singleton TemplateRenderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer()
    return _renderer
