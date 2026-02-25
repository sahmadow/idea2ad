"""Tests for v2 template selector — two-pass selection algorithm."""

import pytest
from app.schemas.creative_params import CreativeParameters
from app.services.v2.template_selector import select_templates


class TestTemplateSelector:
    def _full_params(self) -> CreativeParameters:
        """CreativeParameters with all data available."""
        return CreativeParameters(
            product_name="CloudRest Pillow",
            product_category="Sleep/Bedding",
            key_benefit="Eliminates neck pain",
            key_differentiator="Cooling gel technology",
            value_props=["Cooling gel", "5-year warranty", "Free returns"],
            customer_pains=["Neck pain", "Pillow goes flat", "Overheating"],
            customer_desires=["Deep sleep", "Wake refreshed"],
            social_proof="12,847 5-star reviews",
            hero_image_url="https://example.com/hero.jpg",
            product_images=["img1.jpg", "img2.jpg", "img3.jpg"],
            scene_problem="Person rubbing stiff neck at desk",
            brand_name="CloudRest",
        )

    def test_full_params_selects_all_types(self):
        """With full data, all available types should be selected."""
        params = self._full_params()
        selected = select_templates(params)
        ids = [t.id for t in selected]

        assert "branded_static" in ids
        assert "organic_static_reddit" in ids
        assert "problem_statement_text" in ids
        assert "review_static" in ids
        assert "review_static_competition" in ids
        assert "service_hero" in ids
        assert "product_centric" in ids
        assert "person_centric" in ids
        assert "branded_static_video" in ids
        assert "service_hero_video" in ids

        assert len(selected) == 10

    def test_minimal_params(self):
        """With minimal data, only low-requirement types selected."""
        params = CreativeParameters(
            product_name="Test Product",
            customer_pains=["Generic pain"],
            key_benefit="Works great",
            brand_name="Test",
        )
        selected = select_templates(params)
        ids = [t.id for t in selected]

        # Always-generate types should be present
        assert "problem_statement_text" in ids
        assert "branded_static" in ids
        assert "person_centric" in ids

        # Should NOT get types needing social_proof or hero_image_url
        assert "review_static" not in ids
        assert "service_hero" not in ids

    def test_no_social_proof_skips_review(self):
        """review_static requires social_proof."""
        params = self._full_params()
        params.social_proof = None
        params.testimonials = []
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "review_static" not in ids

    def test_no_images_skips_product_centric(self):
        """product_centric requires product_images or hero_image_url."""
        params = self._full_params()
        params.product_images = []
        params.hero_image_url = None
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "product_centric" not in ids
