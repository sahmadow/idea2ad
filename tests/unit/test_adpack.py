"""Tests for AdPack assembly service (Phase 5)."""

import pytest
from app.models import (
    AdPack,
    AdCreative,
    SmartBroadTargeting,
    CampaignDraft,
    AnalysisResult,
    StylingGuide,
    AdSetTargeting,
    CreativeAsset,
    ImageBrief,
    TextOverlay,
    Ad,
    AdPackUpdateRequest,
)
from app.services.adpack import (
    derive_smart_broad_targeting,
    assemble_ad_pack,
    get_ad_pack,
    update_ad_pack,
    delete_ad_pack,
    _ad_packs,
)


@pytest.fixture(autouse=True)
def clear_ad_packs():
    """Clear in-memory ad packs before each test."""
    _ad_packs.clear()
    yield
    _ad_packs.clear()


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        summary="A great SaaS tool for project management that helps teams stay organized",
        unique_selling_proposition="All-in-one project management for remote teams",
        pain_points=["Scattered tools", "Poor visibility", "Wasted time"],
        call_to_action="Start Free Trial",
        buyer_persona={
            "age_range": [25, 45],
            "gender": "All",
            "education": "College",
            "job_titles": ["Project Manager", "Team Lead"],
        },
        keywords=["project management", "team collaboration", "productivity", "remote work", "task tracking"],
        styling_guide=StylingGuide(
            primary_colors=["#4F46E5"],
            secondary_colors=["#818CF8"],
            font_families=["Inter"],
            design_style="modern",
            mood="professional",
        ),
    )


@pytest.fixture
def sample_draft(sample_analysis):
    return CampaignDraft(
        project_url="https://example.com",
        analysis=sample_analysis,
        targeting=AdSetTargeting(
            age_min=25,
            age_max=45,
            genders=["male", "female"],
            geo_locations=["US"],
            interests=["project management", "productivity"],
        ),
        suggested_creatives=[
            CreativeAsset(type="headline", content="Manage Projects Effortlessly", rationale="Direct benefit"),
            CreativeAsset(type="headline", content="Your Team Deserves Better Tools", rationale="Emotional appeal"),
            CreativeAsset(type="copy_primary", content="Tired of juggling multiple tools? Our platform brings everything together.", rationale="Pain point"),
            CreativeAsset(type="copy_primary", content="Join 10,000+ teams who switched and never looked back.", rationale="Social proof"),
        ],
        image_briefs=[
            ImageBrief(
                approach="product-focused",
                visual_description="Dashboard screenshot",
                styling_notes="Clean modern look",
                text_overlays=[TextOverlay(content="Try Free", font_size="large", position="center", color="#ffffff")],
                meta_best_practices=["Keep text under 20%"],
                rationale="Show the product",
            ),
        ],
        ads=[
            Ad(id=1, imageUrl="https://s3.example.com/img1.png", primaryText="Tired of juggling tools?", headline="Manage Projects Effortlessly", description="All-in-one project management"),
            Ad(id=2, imageUrl="https://s3.example.com/img2.png", primaryText="Join 10,000+ teams", headline="Your Team Deserves Better", description="Start your free trial today"),
        ],
        status="ANALYZED",
    )


class TestDeriveSmartBroadTargeting:
    def test_basic_targeting_from_persona(self):
        persona = {"age_range": [25, 45], "gender": "All"}
        targeting = derive_smart_broad_targeting(persona, ["test", "keywords"])

        assert targeting.age_min == 25
        assert targeting.age_max == 45
        assert targeting.genders == ["all"]
        assert targeting.geo_locations == ["US"]
        assert targeting.rationale.methodology == "smart_broad"

    def test_male_gender_targeting(self):
        persona = {"age_range": [18, 35], "gender": "Male"}
        targeting = derive_smart_broad_targeting(persona, [])

        assert targeting.genders == ["male"]

    def test_female_gender_targeting(self):
        persona = {"age_range": [20, 50], "gender": "Female"}
        targeting = derive_smart_broad_targeting(persona, [])

        assert targeting.genders == ["female"]

    def test_default_age_range(self):
        persona = {}
        targeting = derive_smart_broad_targeting(persona, [])

        assert targeting.age_min == 18
        assert targeting.age_max == 65

    def test_custom_geo_locations(self):
        persona = {"age_range": [25, 45]}
        targeting = derive_smart_broad_targeting(persona, [], geo_locations=["US", "CA"])

        assert targeting.geo_locations == ["US", "CA"]

    def test_age_clamping(self):
        persona = {"age_range": [10, 80]}
        targeting = derive_smart_broad_targeting(persona, [])

        assert targeting.age_min == 18
        assert targeting.age_max == 65

    def test_rationale_includes_job_titles(self):
        persona = {
            "age_range": [25, 45],
            "job_titles": ["Software Engineer", "DevOps"],
        }
        targeting = derive_smart_broad_targeting(persona, [])

        assert "Software Engineer" in targeting.rationale.age_range_reason


class TestAssembleAdPack:
    def test_basic_assembly(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        assert pack.id is not None
        assert pack.project_url == "https://example.com"
        assert len(pack.creatives) > 0
        assert pack.budget_daily == 15.0
        assert pack.duration_days == 3
        assert pack.status == "draft"
        assert pack.campaign_structure.ad_count == len(pack.creatives)

    def test_creatives_have_strategy_labels(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        strategies = [c.strategy for c in pack.creatives]
        assert "product_aware" in strategies
        assert "product_unaware" in strategies

    def test_creatives_from_ads(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        # First 2 creatives should come from the ads
        assert pack.creatives[0].image_url == "https://s3.example.com/img1.png"
        assert pack.creatives[1].image_url == "https://s3.example.com/img2.png"

    def test_campaign_name_from_url(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        assert "Example" in pack.campaign_structure.campaign_name

    def test_targeting_derived_from_persona(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        assert pack.targeting.age_min == 25
        assert pack.targeting.age_max == 45
        assert pack.targeting.rationale.methodology == "smart_broad"

    def test_stores_in_memory(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        retrieved = get_ad_pack(pack.id)
        assert retrieved is not None
        assert retrieved.id == pack.id

    def test_job_id_stored(self, sample_draft):
        pack = assemble_ad_pack(sample_draft, job_id="test-job-123")

        assert pack.created_from == "test-job-123"

    def test_max_10_creatives(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        assert len(pack.creatives) <= 10


class TestUpdateAdPack:
    def test_update_budget(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        updated = update_ad_pack(
            pack.id,
            AdPackUpdateRequest(budget_daily=25.0),
        )
        assert updated is not None
        assert updated.budget_daily == 25.0

    def test_update_duration(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        updated = update_ad_pack(
            pack.id,
            AdPackUpdateRequest(duration_days=7),
        )
        assert updated is not None
        assert updated.duration_days == 7

    def test_update_creative_headline(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)
        creative_id = pack.creatives[0].id

        updated = update_ad_pack(
            pack.id,
            AdPackUpdateRequest(creative_id=creative_id, headline="New Headline"),
        )
        assert updated is not None
        matching = [c for c in updated.creatives if c.id == creative_id]
        assert len(matching) == 1
        assert matching[0].headline == "New Headline"

    def test_update_creative_primary_text(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)
        creative_id = pack.creatives[0].id

        updated = update_ad_pack(
            pack.id,
            AdPackUpdateRequest(creative_id=creative_id, primary_text="Updated copy text"),
        )
        assert updated is not None
        matching = [c for c in updated.creatives if c.id == creative_id]
        assert matching[0].primary_text == "Updated copy text"

    def test_update_nonexistent_pack(self):
        result = update_ad_pack("nonexistent", AdPackUpdateRequest(budget_daily=10.0))
        assert result is None

    def test_budget_minimum_enforced(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        updated = update_ad_pack(
            pack.id,
            AdPackUpdateRequest(budget_daily=0.5),
        )
        assert updated is not None
        assert updated.budget_daily == 1.0


class TestDeleteAdPack:
    def test_delete_existing(self, sample_draft):
        pack = assemble_ad_pack(sample_draft)

        assert delete_ad_pack(pack.id) is True
        assert get_ad_pack(pack.id) is None

    def test_delete_nonexistent(self):
        assert delete_ad_pack("nonexistent") is False
