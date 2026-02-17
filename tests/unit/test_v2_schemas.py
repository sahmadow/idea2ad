"""Tests for v2 schemas — CreativeParameters, AdTypeDefinition, AdPack."""

import pytest
from app.schemas.creative_params import (
    CreativeParameters,
    BrandColors,
    PersonaDemographics,
    TargetPersona,
)
from app.schemas.ad_types import AdTypeDefinition, CopyTemplate, LayerDefinition, VariantRule
from app.schemas.ad_pack import GeneratedCreative, TargetingSpec, AdPack


class TestCreativeParameters:
    def test_defaults(self):
        """Minimal CreativeParameters with required fields only."""
        params = CreativeParameters(product_name="Test Product")
        assert params.product_name == "Test Product"
        assert params.brand_colors.primary == "#1A365D"
        assert params.brand_fonts == ["Inter"]
        assert params.tone == "casual"
        assert params.cta_text == "Shop Now"

    def test_has_enough_value_props(self):
        params = CreativeParameters(
            product_name="Test",
            value_props=["a", "b", "c"],
        )
        assert params.has_enough_value_props(3) is True
        assert params.has_enough_value_props(4) is False

    def test_has_social_proof(self):
        params = CreativeParameters(product_name="Test")
        assert params.has_social_proof() is False

        params.social_proof = "1000+ reviews"
        assert params.has_social_proof() is True

        params.social_proof = None
        params.testimonials = ["Great product!"]
        assert params.has_social_proof() is True

    def test_has_pains_and_desires(self):
        params = CreativeParameters(
            product_name="Test",
            customer_pains=["pain"],
            customer_desires=["desire"],
        )
        assert params.has_pains_and_desires() is True

        params.customer_desires = []
        assert params.has_pains_and_desires() is False

    def test_full_params(self):
        """CreativeParameters with all fields populated."""
        params = CreativeParameters(
            product_name="CloudRest Pillow",
            product_category="Sleep/Bedding",
            product_description_short="Premium memory foam pillow",
            price="$79",
            brand_name="CloudRest",
            brand_colors=BrandColors(primary="#2D5A7B", secondary="#F4A623"),
            key_benefit="Eliminates neck pain",
            key_differentiator="Cooling gel technology",
            value_props=["Cooling gel", "5-year warranty", "Free returns"],
            customer_pains=["Neck pain", "Pillow goes flat", "Overheating"],
            customer_desires=["Deep sleep", "Wake refreshed"],
            social_proof="12,847 5-star reviews",
            persona_primary=TargetPersona(
                label="Side sleeper, 35-55",
                demographics=PersonaDemographics(age_min=35, age_max=55),
            ),
            scene_problem="Person rubbing stiff neck at desk",
            scene_solution="Person sleeping peacefully",
        )
        assert params.has_enough_value_props(3) is True
        assert params.has_social_proof() is True
        assert params.has_pains_and_desires() is True
        assert params.has_scene_problem() is True


class TestAdTypeDefinition:
    def test_basic_definition(self):
        ad_type = AdTypeDefinition(
            id="test_static",
            name="Test Static",
            strategy="product_aware",
            format="static",
            required_params=["product_name", "hero_image_url"],
            layers=[
                LayerDefinition(type="background", source="{brand_colors.primary}"),
                LayerDefinition(type="text", content="{key_benefit}", position="center"),
            ],
            copy_templates=CopyTemplate(
                primary_text="{key_benefit} — try {product_name}",
                headline="{key_benefit}",
                cta_type="SHOP_NOW",
            ),
            variants=[VariantRule(vary="background", options=["solid", "gradient"])],
        )
        assert ad_type.id == "test_static"
        assert len(ad_type.layers) == 2
        assert ad_type.copy_templates.cta_type == "SHOP_NOW"


class TestAdPack:
    def test_default_pack(self):
        pack = AdPack(id="test-pack-1")
        assert pack.status == "generating"
        assert pack.budget_daily_cents == 1500
        assert pack.duration_days == 3
        assert pack.creatives == []

    def test_pack_with_creatives(self):
        pack = AdPack(
            id="test-pack-2",
            product_name="Test Product",
            creatives=[
                GeneratedCreative(
                    id="c1",
                    ad_type_id="product_benefits_static",
                    strategy="product_aware",
                    format="static",
                    aspect_ratio="1:1",
                    primary_text="Test copy",
                    headline="Test headline",
                ),
            ],
            status="draft",
        )
        assert len(pack.creatives) == 1
        assert pack.creatives[0].strategy == "product_aware"
