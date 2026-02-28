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
    # SaaS-specific templates
    "person-centric": "person_centric.html",
    "brand-centric": "brand_centric.html",
}

# Replica template map
REPLICA_TEMPLATE_MAP = {
    "hero": "replica/hero_replica.html",
    "features": "replica/features_replica.html",
    "screenshot": "replica/screenshot_replica.html",
    "before_after": "replica/before_after_replica.html",
    "testimonial": "replica/testimonial_replica.html",
}

# Carousel template map
CAROUSEL_TEMPLATE_MAP = {
    "hook": "carousel/hook_card.html",
    "value_prop": "carousel/value_prop_card.html",
    "cta": "carousel/cta_card.html",
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
        # Select template based on creative_type first, then approach
        creative_type = getattr(brief, 'creative_type', None)
        approach = brief.approach

        # Try creative_type first, then approach, then default
        template_name = TEMPLATE_MAP.get(creative_type) or TEMPLATE_MAP.get(approach, "product_focused.html")
        dimensions = AD_DIMENSIONS.get(aspect_ratio, (1080, 1080))

        logger.info(f"Rendering ad: creative_type={creative_type}, approach={approach}, template={template_name}")

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

        # Compute contrast-safe colors
        primary_color = primary_colors[0] if primary_colors else "#ffffff"
        accent_color = secondary_colors[0] if secondary_colors else "#000000"
        text_color = self._get_text_color(primary_color)

        button_styles = brand_css.get("button_styles", {})
        cta_bg = button_styles.get("backgroundColor") or accent_color
        cta_text_fallback = button_styles.get("color") or primary_color
        cta_text_color = self._get_cta_text_color(cta_bg, cta_text_fallback)

        # Solution section text (problem_solution template)
        solution_text_color = self._get_text_color(accent_color)

        # Build template context
        context = {
            # CSS injection
            "font_faces": brand_css.get("font_faces", []),
            "css_variables": brand_css.get("css_variables", {}),
            # Colors — all contrast-checked
            "primary_color": primary_color,
            "accent_color": accent_color,
            "text_color": text_color,
            "secondary_text_color": self._get_secondary_text_color(primary_color, text_color),
            "muted_text_color": self._get_muted_text_color(primary_color, text_color),
            "cta_text_color": cta_text_color,
            "solution_text_color": solution_text_color,
            "solution_secondary_color": self._get_secondary_text_color(accent_color, solution_text_color),
            "solution_muted_color": self._get_muted_text_color(accent_color, solution_text_color),
            # Adaptive text shadows
            "text_shadow": self._get_text_shadow(text_color),
            "headline_text_shadow": self._get_headline_text_shadow(text_color),
            "gradient": gradient_css,
            # Typography
            "font_family": font_families[0] if font_families else "Inter",
            # Button styles
            "button_styles": button_styles,
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

    # ── Contrast & color utilities ──────────────────────────────

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to (r, g, b) tuple. Handles hex, rgb(), and fallback."""
        import re

        if not hex_color or not isinstance(hex_color, str):
            return (128, 128, 128)

        color = hex_color.strip()

        # Handle rgb()/rgba()
        m = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)", color)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

        # Handle lab(), oklch(), hsl() etc. — can't easily convert, fallback
        if not color.startswith("#"):
            return (128, 128, 128)

        hex_str = color.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join([c * 2 for c in hex_str])
        if len(hex_str) < 6:
            return (128, 128, 128)

        try:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        except ValueError:
            return (128, 128, 128)

    def _relative_luminance(self, r: int, g: int, b: int) -> float:
        """WCAG 2.0 relative luminance (sRGB linearized)."""
        def linearize(v):
            v = v / 255.0
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    def _contrast_ratio(self, color1: str, color2: str) -> float:
        """WCAG contrast ratio between two hex colors."""
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        l1 = self._relative_luminance(r1, g1, b1)
        l2 = self._relative_luminance(r2, g2, b2)
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def _blend_color(self, text_color: str, bg_color: str, factor: float) -> str:
        """Blend text toward background by factor (0 = text, 1 = bg)."""
        r1, g1, b1 = self._hex_to_rgb(text_color)
        r2, g2, b2 = self._hex_to_rgb(bg_color)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text_color(self, bg_color: str) -> str:
        """Return white or black text – whichever has higher WCAG contrast."""
        try:
            white_cr = self._contrast_ratio(bg_color, "#ffffff")
            black_cr = self._contrast_ratio(bg_color, "#000000")
            return "#000000" if black_cr >= white_cr else "#ffffff"
        except Exception:
            return "#ffffff"

    def _get_secondary_text_color(self, bg_color: str, text_color: str) -> str:
        """Muted text (subheadlines) that keeps WCAG AA contrast (>= 4.5:1)."""
        for factor in [0.25, 0.20, 0.15, 0.10, 0.05, 0.0]:
            blended = self._blend_color(text_color, bg_color, factor)
            if self._contrast_ratio(bg_color, blended) >= 4.5:
                return blended
        return text_color

    def _get_muted_text_color(self, bg_color: str, text_color: str) -> str:
        """Heavily muted text (pain points) that keeps >= 3:1 contrast (WCAG large text)."""
        for factor in [0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.0]:
            blended = self._blend_color(text_color, bg_color, factor)
            if self._contrast_ratio(bg_color, blended) >= 3.0:
                return blended
        return text_color

    def _get_cta_text_color(self, button_bg: str, fallback_text: str) -> str:
        """Ensure CTA text contrasts with button bg (>= 4.5:1)."""
        try:
            if self._contrast_ratio(button_bg, fallback_text) >= 4.5:
                return fallback_text
            return self._get_text_color(button_bg)
        except Exception:
            return "#ffffff"

    def _get_text_shadow(self, text_color: str) -> str:
        """Adaptive text-shadow: strong for light-on-dark, subtle for dark-on-light."""
        try:
            r, g, b = self._hex_to_rgb(text_color)
            lum = self._relative_luminance(r, g, b)
            if lum > 0.5:
                # Light text (white) on dark bg – strong shadow for depth
                return "0 2px 8px rgba(0, 0, 0, 0.5), 0 1px 3px rgba(0, 0, 0, 0.4)"
            # Dark text (black) on light bg – minimal shadow
            return "0 1px 2px rgba(0, 0, 0, 0.06)"
        except Exception:
            return "0 2px 8px rgba(0, 0, 0, 0.3)"

    def _get_headline_text_shadow(self, text_color: str) -> str:
        """Stronger shadow for large headlines."""
        try:
            r, g, b = self._hex_to_rgb(text_color)
            lum = self._relative_luminance(r, g, b)
            if lum > 0.5:
                # Light text on dark bg – strong headline shadow
                return "0 3px 12px rgba(0, 0, 0, 0.6), 0 1px 4px rgba(0, 0, 0, 0.5)"
            # Dark text on light bg – subtle headline shadow
            return "0 1px 4px rgba(0, 0, 0, 0.1)"
        except Exception:
            return "0 2px 8px rgba(0, 0, 0, 0.3)"

    async def render_replica_creative(
        self,
        template_type: str,
        replica_data: Any,  # ReplicaData
        variation_data: Dict[str, Any],
        aspect_ratio: str = "1:1",
    ) -> bytes:
        """
        Render replica creative from extracted landing page data.

        Args:
            template_type: "hero", "features", "screenshot", "before_after", "testimonial"
            replica_data: ReplicaData object with extracted elements
            variation_data: Specific content for this variation
            aspect_ratio: "1:1", "4:5", or "9:16"

        Returns:
            PNG image bytes
        """
        template_name = REPLICA_TEMPLATE_MAP.get(template_type, "replica/hero_replica.html")
        dimensions = AD_DIMENSIONS.get(aspect_ratio, (1080, 1080))

        logger.info(f"Rendering replica creative: type={template_type}, aspect={aspect_ratio}")

        # Compute contrast-safe colors for replica
        primary = replica_data.primary_color
        accent = replica_data.accent_color
        text_color = self._get_text_color(primary)

        cta_styles = replica_data.hero.cta_styles or {}
        cta_bg = cta_styles.get("backgroundColor") or accent
        cta_text_fallback = cta_styles.get("color") or primary
        cta_text_color = self._get_cta_text_color(cta_bg, cta_text_fallback)

        # Build base context from replica_data
        context = {
            # CSS injection
            "font_faces": replica_data.font_faces,
            "css_variables": replica_data.css_variables,
            # Colors — contrast-checked
            "primary_color": primary,
            "secondary_color": replica_data.secondary_color,
            "accent_color": accent,
            "text_color": text_color,
            "secondary_text_color": self._get_secondary_text_color(primary, text_color),
            "muted_text_color": self._get_muted_text_color(primary, text_color),
            "cta_text_color": cta_text_color,
            "solution_text_color": self._get_text_color(accent),
            "solution_secondary_color": self._get_secondary_text_color(accent, self._get_text_color(accent)),
            "solution_muted_color": self._get_muted_text_color(accent, self._get_text_color(accent)),
            "text_shadow": self._get_text_shadow(text_color),
            "headline_text_shadow": self._get_headline_text_shadow(text_color),
            "gradient": None,
            # Typography
            "font_family": replica_data.font_family,
            # Logo
            "logo_url": replica_data.logo_url,
            # Border radius
            "border_radius": "12px",
            # CTA defaults from hero
            "cta_text": replica_data.hero.cta_text,
            "cta_styles": cta_styles,
        }

        # Merge variation-specific data
        context.update(variation_data)

        return await self.render_template(template_name, context, dimensions)

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
