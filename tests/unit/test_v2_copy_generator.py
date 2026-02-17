"""Tests for v2 copy generator — template fill and constraint enforcement."""

import pytest
from app.schemas.creative_params import CreativeParameters, BrandColors
from app.services.v2.copy_generator import (
    generate_copy_from_template,
    _resolve_variable,
    PRIMARY_TEXT_MAX,
    HEADLINE_MAX,
)
from app.services.v2.ad_type_registry import (
    PRODUCT_BENEFITS_STATIC,
    PROBLEM_STATEMENT_TEXT,
    US_VS_THEM_PROBLEM,
    ORGANIC_STATIC_SOLUTION,
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
        brand_name="CloudRest",
        brand_colors=BrandColors(primary="#2D5A7B"),
        hero_image_url="https://example.com/hero.jpg",
    )


class TestResolveVariable:
    def test_simple_field(self, full_params):
        result = _resolve_variable("{product_name}", full_params)
        assert result == "CloudRest Pillow"

    def test_array_index(self, full_params):
        result = _resolve_variable("{value_props[0]}", full_params)
        assert result == "Cooling gel"

    def test_dotted_path(self, full_params):
        result = _resolve_variable("{brand_colors.primary}", full_params)
        assert result == "#2D5A7B"

    def test_missing_field(self, full_params):
        result = _resolve_variable("{nonexistent}", full_params)
        assert result == ""

    def test_array_out_of_bounds(self, full_params):
        result = _resolve_variable("{value_props[99]}", full_params)
        assert result == ""


class TestCopyGeneration:
    def test_product_benefits_copy(self, full_params):
        copy = generate_copy_from_template(PRODUCT_BENEFITS_STATIC, full_params)
        assert "CloudRest Pillow" in copy["primary_text"]
        assert "Eliminates neck pain" in copy["primary_text"]
        assert "Cooling gel" in copy["primary_text"]
        assert copy["cta_type"] == "SHOP_NOW"

    def test_problem_statement_copy(self, full_params):
        copy = generate_copy_from_template(PROBLEM_STATEMENT_TEXT, full_params)
        assert "Neck pain" in copy["primary_text"]
        assert "CloudRest Pillow" in copy["primary_text"]
        assert copy["cta_type"] == "LEARN_MORE"

    def test_us_vs_them_problem_copy(self, full_params):
        copy = generate_copy_from_template(US_VS_THEM_PROBLEM, full_params)
        assert "Before" in copy["primary_text"]
        assert "After" in copy["primary_text"]
        assert "Neck pain" in copy["primary_text"]
        assert "Deep uninterrupted sleep" in copy["primary_text"]

    def test_headline_truncation(self, full_params):
        """Headlines longer than 40 chars should be truncated."""
        full_params.key_benefit = "This is an extremely long key benefit that definitely exceeds forty characters"
        copy = generate_copy_from_template(PRODUCT_BENEFITS_STATIC, full_params)
        assert len(copy["headline"]) <= HEADLINE_MAX

    def test_fallback_applied(self):
        """Missing optional fields should use fallbacks."""
        params = CreativeParameters(
            product_name="Test Product",
            customer_pains=["Generic pain"],
        )
        copy = generate_copy_from_template(PROBLEM_STATEMENT_TEXT, params)
        # Should not have unresolved {variables}
        assert "{" not in copy["primary_text"]
        assert "{" not in copy["headline"]
