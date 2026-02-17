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
        """With full data, all 11 types should be selected."""
        params = self._full_params()
        selected = select_templates(params)
        ids = [t.id for t in selected]

        # Product Aware (6)
        assert "product_benefits_static" in ids
        assert "review_static" in ids
        assert "us_vs_them_solution" in ids
        assert "organic_static_solution" in ids
        assert "product_demo_video" in ids
        assert "founder_video_solution" in ids

        # Product Unaware (5)
        assert "problem_statement_text" in ids
        assert "problem_statement_image" in ids
        assert "organic_static_problem" in ids
        assert "us_vs_them_problem" in ids
        assert "founder_video_problem" in ids

        assert len(selected) == 11

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

        # Should still get organic + problem types
        assert "problem_statement_text" in ids
        assert "organic_static_problem" in ids
        assert "founder_video_problem" in ids

        # Should NOT get types needing hero_image_url or value_props >= 3
        assert "product_benefits_static" not in ids
        assert "review_static" not in ids

    def test_no_social_proof_skips_review(self):
        """review_static requires social_proof."""
        params = self._full_params()
        params.social_proof = None
        params.testimonials = []
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "review_static" not in ids

    def test_insufficient_product_images_skips_demo(self):
        """product_demo_video requires 3+ product images."""
        params = self._full_params()
        params.product_images = ["img1.jpg"]
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "product_demo_video" not in ids

    def test_no_scene_problem_skips_problem_image(self):
        """problem_statement_image requires scene_problem."""
        params = self._full_params()
        params.scene_problem = None
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "problem_statement_image" not in ids

    def test_no_desires_skips_before_after(self):
        """us_vs_them_problem requires both pains and desires."""
        params = self._full_params()
        params.customer_desires = []
        selected = select_templates(params)
        ids = [t.id for t in selected]
        assert "us_vs_them_problem" not in ids
