"""Tests for v2 static renderer — Pillow-based image generation."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image, ImageDraw

from app.schemas.creative_params import CreativeParameters, BrandColors
from app.schemas.ad_types import AdTypeDefinition, LayerDefinition, CopyTemplate
from app.services.v2.static_renderer import (
    StaticAdRenderer,
    ASPECT_RATIO_SIZES,
    _resolve_var,
    _check_condition,
    _wrap_text,
    _load_font,
    _create_gradient,
    _darken_overlay,
    _add_shadow,
    _get_position_bbox,
    _render_background,
    _render_text,
    _render_badge,
    _render_review_card,
    _render_comparison_layout,
    _render_social_post_frame,
)


@pytest.fixture
def full_params():
    return CreativeParameters(
        product_name="CloudRest Pillow",
        product_category="Sleep/Bedding",
        product_description_short="Premium memory foam pillow",
        key_benefit="Eliminates neck pain",
        key_differentiator="Cooling gel technology",
        value_props=["Cooling gel", "5-year warranty", "Free returns", "Machine washable"],
        customer_pains=["Neck pain", "Pillow goes flat", "Overheating at night"],
        customer_desires=["Deep uninterrupted sleep", "Waking up refreshed"],
        social_proof="12,847 5-star reviews",
        testimonials=["Best pillow I've ever owned!"],
        brand_name="CloudRest",
        brand_colors=BrandColors(primary="#2D5A7B", secondary="#F4A623"),
        hero_image_url="https://example.com/hero.jpg",
        price="$79",
    )


@pytest.fixture
def simple_static_type():
    """A minimal static ad type for testing."""
    return AdTypeDefinition(
        id="test_static",
        name="Test Static",
        strategy="product_aware",
        format="static",
        aspect_ratios=["1:1", "9:16"],
        layers=[
            LayerDefinition(
                type="background",
                source="{brand_colors.primary}",
                style={"fallback": "#1A365D"},
            ),
            LayerDefinition(
                type="text",
                content="{key_benefit}",
                position="top_third",
                style={"size": "large", "color": "#FFFFFF"},
            ),
        ],
    )


# --- Unit tests for helpers ---

class TestResolveVar:
    def test_simple_field(self, full_params):
        assert _resolve_var("{product_name}", full_params) == "CloudRest Pillow"

    def test_array_index(self, full_params):
        assert _resolve_var("{value_props[0]}", full_params) == "Cooling gel"

    def test_dotted_path(self, full_params):
        assert _resolve_var("{brand_colors.primary}", full_params) == "#2D5A7B"

    def test_missing_field(self, full_params):
        assert _resolve_var("{nonexistent}", full_params) == ""

    def test_no_template(self, full_params):
        assert _resolve_var("plain text", full_params) == "plain text"


class TestCheckCondition:
    def test_no_condition(self, full_params):
        assert _check_condition(None, full_params) is True

    def test_exists_true(self, full_params):
        assert _check_condition("hero_image_url_exists", full_params) is True

    def test_exists_false(self, full_params):
        full_params.hero_image_url = None
        assert _check_condition("hero_image_url_exists", full_params) is False

    def test_price_exists(self, full_params):
        assert _check_condition("price_exists", full_params) is True


class TestWrapText:
    def test_short_text(self):
        font = _load_font("Inter", 36)
        lines = _wrap_text("Hello", font, 500)
        assert len(lines) == 1
        assert lines[0] == "Hello"

    def test_long_text_wraps(self):
        font = _load_font("Inter", 36)
        text = "This is a very long text that should definitely wrap across multiple lines"
        lines = _wrap_text(text, font, 300)
        assert len(lines) > 1

    def test_empty_text(self):
        font = _load_font("Inter", 36)
        lines = _wrap_text("", font, 500)
        assert lines == [""]


class TestPositionBbox:
    def test_center(self):
        x, y, w, h = _get_position_bbox("center", 1080, 1080)
        assert x == 40  # padding
        assert w == 1000  # 1080 - 2*40

    def test_left_half(self):
        x, y, w, h = _get_position_bbox("left_half", 1080, 1080)
        assert x == 0
        assert w == 540

    def test_right_half(self):
        x, y, w, h = _get_position_bbox("right_half", 1080, 1080)
        assert x == 540

    def test_unknown_defaults_to_full(self):
        x, y, w, h = _get_position_bbox("unknown_position", 1080, 1080)
        assert w == 1000  # falls back to padded full width


class TestGradient:
    def test_creates_correct_size(self):
        img = _create_gradient(100, 200, "#FF0000", "#0000FF")
        assert img.size == (100, 200)

    def test_top_is_color1(self):
        img = _create_gradient(100, 200, "#FF0000", "#0000FF")
        r, g, b = img.getpixel((50, 0))
        assert r == 255 and b == 0

    def test_bottom_is_color2(self):
        img = _create_gradient(100, 200, "#FF0000", "#0000FF")
        r, g, b = img.getpixel((50, 199))
        assert r == 0 and b == 255


class TestDarkenOverlay:
    def test_darkens_image(self):
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        dark = _darken_overlay(img, 0.5)
        r, g, b, a = dark.getpixel((50, 50))
        # Should be significantly darker than white
        assert r < 200


class TestAddShadow:
    def test_shadow_increases_size(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        shadowed = _add_shadow(img)
        assert shadowed.width == 120  # +20 for shadow
        assert shadowed.height == 120


# --- Layer renderer tests ---

class TestRenderBackground:
    def test_solid_color(self, full_params):
        canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        draw = MagicMock()
        layer = LayerDefinition(
            type="background",
            source="{brand_colors.primary}",
            style={"fallback": "#1A365D"},
        )
        _render_background(canvas, draw, layer, full_params)
        # Canvas should now be filled with #2D5A7B
        r, g, b, a = canvas.getpixel((50, 50))
        assert (r, g, b) == (45, 90, 123)

    def test_fallback_color(self, full_params):
        full_params.brand_colors.primary = "not-a-color"
        canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        draw = MagicMock()
        layer = LayerDefinition(
            type="background",
            source="{brand_colors.primary}",
            style={"fallback": "#FF0000"},
        )
        _render_background(canvas, draw, layer, full_params)
        r, g, b, a = canvas.getpixel((50, 50))
        assert r == 255 and g == 0 and b == 0


class TestRenderText:
    def test_renders_text(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="text",
            content="{key_benefit}",
            position="center",
            style={"color": "#FFFFFF", "size": "large"},
        )
        _render_text(canvas, draw, layer, full_params)
        # Canvas should have non-black pixels where text was drawn
        pixels = list(canvas.getdata())
        non_black = [p for p in pixels if p != (0, 0, 0, 255)]
        assert len(non_black) > 0

    def test_empty_content_no_crash(self, full_params):
        canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="text",
            content="{nonexistent}",
            position="center",
            style={"color": "#FFFFFF"},
        )
        # Should not raise
        _render_text(canvas, draw, layer, full_params)


class TestRenderBadge:
    def test_renders_badge(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="badge",
            content="{price}",
            position="bottom_right",
            style={"background": "{brand_colors.secondary}"},
        )
        _render_badge(canvas, draw, layer, full_params)
        # Badge renders at bottom_right position: (880, 980) area
        # Check that some pixels in the badge region are non-black
        x, y, _, _ = _get_position_bbox("bottom_right", 1080, 1080)
        r, g, b, a = canvas.getpixel((x + 20, y + 10))
        # The badge area should have the secondary color (#F4A623)
        assert r > 200  # orange-ish

    def test_empty_price_no_badge(self, full_params):
        full_params.price = None
        canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="badge",
            content="{price}",
            position="bottom_right",
            style={"background": "#FF0000"},
        )
        # Should not render anything — no crash
        _render_badge(canvas, draw, layer, full_params)


class TestRenderReviewCard:
    def test_renders_card(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (26, 54, 93, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="review_card",
            style_variant="review_card",
            style={"rating": 5, "verified": True},
        )
        _render_review_card(canvas, draw, layer, full_params)
        # Should have white card pixels
        center_x, center_y = 540, 200
        r, g, b, a = canvas.getpixel((center_x, center_y))
        assert r > 200 and g > 200 and b > 200  # white card area


class TestRenderComparisonLayout:
    def test_renders_divider(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="comparison_layout",
            style={"layout": "split_vertical"},
        )
        _render_comparison_layout(canvas, draw, layer, full_params)
        # Middle column should have the divider (gray pixel)
        r, g, b, a = canvas.getpixel((540, 540))
        assert r == 200  # gray divider line


class TestRenderSocialPostFrame:
    def test_tweet_variant(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (240, 240, 240, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="social_post_frame",
            style_variant="tweet",
        )
        _render_social_post_frame(canvas, draw, layer, full_params)
        # Should have white card
        r, g, b, a = canvas.getpixel((540, 540))
        assert r > 200

    def test_reddit_variant(self, full_params):
        canvas = Image.new("RGBA", (1080, 1080), (240, 240, 240, 255))
        draw = ImageDraw.Draw(canvas)
        layer = LayerDefinition(
            type="social_post_frame",
            style_variant="reddit_post",
        )
        _render_social_post_frame(canvas, draw, layer, full_params)
        # Reddit has gray bg
        r, g, b, a = canvas.getpixel((5, 5))
        assert r > 200  # light gray area


# --- Integration tests for StaticAdRenderer ---

class TestStaticAdRenderer:
    @pytest.fixture
    def renderer(self):
        return StaticAdRenderer()

    @pytest.mark.asyncio
    async def test_render_basic_ad(self, renderer, simple_static_type, full_params):
        """Basic render produces valid PNG bytes."""
        img_bytes = await renderer.render_ad(simple_static_type, full_params, "1:1")
        assert len(img_bytes) > 0
        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(img_bytes))
        assert img.size == (1080, 1080)

    @pytest.mark.asyncio
    async def test_render_9_16(self, renderer, simple_static_type, full_params):
        """9:16 aspect ratio produces correct dimensions."""
        img_bytes = await renderer.render_ad(simple_static_type, full_params, "9:16")
        img = Image.open(io.BytesIO(img_bytes))
        assert img.size == (1080, 1920)

    @pytest.mark.asyncio
    async def test_render_191_1(self, renderer, full_params):
        """1.91:1 aspect ratio (Facebook feed)."""
        ad_type = AdTypeDefinition(
            id="test_wide",
            name="Test Wide",
            strategy="product_aware",
            format="static",
            aspect_ratios=["1.91:1"],
            layers=[
                LayerDefinition(type="background", source="#FF0000"),
                LayerDefinition(type="text", content="Hello", position="center"),
            ],
        )
        img_bytes = await renderer.render_ad(ad_type, full_params, "1.91:1")
        img = Image.open(io.BytesIO(img_bytes))
        assert img.size == (1200, 628)

    @pytest.mark.asyncio
    async def test_render_all_ratios(self, renderer, simple_static_type, full_params):
        """render_all_ratios returns dict of all aspect ratios."""
        results = await renderer.render_all_ratios(simple_static_type, full_params)
        assert "1:1" in results
        assert "9:16" in results
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_render_with_hook_text(self, renderer, full_params):
        """Hook text substitution for problem/organic types."""
        ad_type = AdTypeDefinition(
            id="test_hook",
            name="Test Hook",
            strategy="product_unaware",
            format="static",
            layers=[
                LayerDefinition(type="background", source="#1A202C"),
                LayerDefinition(
                    type="text",
                    content="{problem_hook}",
                    position="center",
                    size="xlarge",
                    style={"color": "#FFFFFF"},
                ),
            ],
        )
        img_bytes = await renderer.render_ad(
            ad_type, full_params, "1:1", hook_text="Neck pain isn't normal."
        )
        img = Image.open(io.BytesIO(img_bytes))
        assert img.size == (1080, 1080)

    @pytest.mark.asyncio
    async def test_render_with_condition_skip(self, renderer, full_params):
        """Layer with unmet condition should be skipped."""
        full_params.price = None
        ad_type = AdTypeDefinition(
            id="test_cond",
            name="Test Condition",
            strategy="product_aware",
            format="static",
            layers=[
                LayerDefinition(type="background", source="#000000"),
                LayerDefinition(
                    type="badge",
                    content="{price}",
                    position="bottom_right",
                    condition="price_exists",
                    style={"background": "#FF0000"},
                ),
            ],
        )
        # Should render without error, badge skipped
        img_bytes = await renderer.render_ad(ad_type, full_params, "1:1")
        assert len(img_bytes) > 0

    @pytest.mark.asyncio
    async def test_render_comparison_layout(self, renderer, full_params):
        """Comparison layout with half-screen elements."""
        ad_type = AdTypeDefinition(
            id="test_comparison",
            name="Test Comparison",
            strategy="product_unaware",
            format="static",
            layers=[
                LayerDefinition(type="comparison_layout", style={"layout": "split_vertical"}),
                LayerDefinition(
                    type="background", position="left_half",
                    source="#E2E8F0", style={"fallback": "#E2E8F0"},
                ),
                LayerDefinition(
                    type="text", content="Before",
                    position="left_half_top",
                    style={"color": "#718096", "size": "small", "uppercase": True},
                ),
                LayerDefinition(
                    type="background", position="right_half",
                    source="{brand_colors.primary}", style={"fallback": "#276749"},
                ),
                LayerDefinition(
                    type="text", content="After",
                    position="right_half_top",
                    style={"color": "#FFFFFF", "size": "small", "uppercase": True},
                ),
            ],
        )
        img_bytes = await renderer.render_ad(ad_type, full_params, "1:1")
        img = Image.open(io.BytesIO(img_bytes))
        # Left half should be light, right half should be brand color
        left_r, left_g, left_b, _ = img.getpixel((100, 500))
        right_r, right_g, right_b, _ = img.getpixel((900, 500))
        # Left is #E2E8F0 (light), right is #2D5A7B (dark blue)
        assert left_r > 200  # light gray
        assert right_r < 100  # dark blue

    @pytest.mark.asyncio
    async def test_render_review_card_type(self, renderer, full_params):
        """Review card ad type renders correctly."""
        ad_type = AdTypeDefinition(
            id="test_review",
            name="Test Review",
            strategy="product_aware",
            format="static",
            layers=[
                LayerDefinition(type="background", source="#1A365D"),
                LayerDefinition(
                    type="review_card",
                    style_variant="review_card",
                    style={"rating": 5, "verified": True},
                ),
            ],
        )
        img_bytes = await renderer.render_ad(ad_type, full_params, "1:1")
        img = Image.open(io.BytesIO(img_bytes))
        assert img.size == (1080, 1080)

    @pytest.mark.asyncio
    async def test_unknown_layer_no_crash(self, renderer, full_params):
        """Unknown layer type logs warning but doesn't crash."""
        ad_type = AdTypeDefinition(
            id="test_unknown",
            name="Test Unknown",
            strategy="product_aware",
            format="static",
            layers=[
                LayerDefinition(type="background", source="#000000"),
                LayerDefinition(type="hologram_3d", content="future"),
            ],
        )
        img_bytes = await renderer.render_ad(ad_type, full_params, "1:1")
        assert len(img_bytes) > 0


class TestAspectRatioSizes:
    def test_all_ratios_defined(self):
        assert "1:1" in ASPECT_RATIO_SIZES
        assert "9:16" in ASPECT_RATIO_SIZES
        assert "1.91:1" in ASPECT_RATIO_SIZES

    def test_square_dimensions(self):
        w, h = ASPECT_RATIO_SIZES["1:1"]
        assert w == h == 1080

    def test_story_dimensions(self):
        w, h = ASPECT_RATIO_SIZES["9:16"]
        assert w == 1080 and h == 1920
