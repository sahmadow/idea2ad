"""
Meta (Facebook) Marketing API Integration Service
Handles campaign creation and publishing to Meta Ads Manager
"""

import logging
import os
import time
from typing import Callable, Dict, Any, List, Optional
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.user import User
from facebook_business.adobjects.page import Page
from facebook_business.exceptions import FacebookRequestError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Retry configuration for transient Meta API errors
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds
# Meta API error codes considered transient (worth retrying)
TRANSIENT_ERROR_CODES = {
    1,       # Unknown error
    2,       # Temporary issue
    4,       # Too many calls
    17,      # Rate limit
    32,      # Page request limit
    341,     # Temporary error
    368,     # Temporarily blocked
    2446079, # Transient error
}


def _is_transient_error(exc: Exception) -> bool:
    """Check if a Meta API error is transient and worth retrying."""
    if isinstance(exc, FacebookRequestError):
        return exc.api_error_code() in TRANSIENT_ERROR_CODES
    return False


def _retry_api_call(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a Meta API call with retry logic for transient errors.
    Uses exponential backoff: 1s, 2s, 4s delays between retries.
    """
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_transient_error(exc):
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"Transient Meta API error (attempt {attempt + 1}/{MAX_RETRIES + 1}), "
                    f"retrying in {delay}s: {exc}"
                )
                time.sleep(delay)
            else:
                raise
    raise last_exc  # Should not reach here, but safety net


# Meta Business Verticals
BUSINESS_VERTICALS = {
    'ECOMMERCE': 'E-commerce',
    'ADVERTISING': 'Advertising',
    'AUTOMOTIVE': 'Automotive',
    'CONSUMER_PACKAGED_GOODS': 'Consumer Packaged Goods',
    'EDUCATION': 'Education',
    'ENERGY_AND_UTILITIES': 'Energy and Utilities',
    'ENTERTAINMENT_AND_MEDIA': 'Entertainment and Media',
    'FINANCIAL_SERVICES': 'Financial Services',
    'GAMING': 'Gaming',
    'GOVERNMENT_AND_POLITICS': 'Government and Politics',
    'MARKETING': 'Marketing',
    'ORGANIZATIONS_AND_ASSOCIATIONS': 'Organizations and Associations',
    'PROFESSIONAL_SERVICES': 'Professional Services',
    'RETAIL': 'Retail',
    'TECHNOLOGY': 'Technology',
    'TELECOM': 'Telecom',
    'TRAVEL': 'Travel',
    'NON_PROFIT': 'Non-profit',
    'RESTAURANT': 'Restaurant',
    'HEALTH': 'Health',
    'LUXURY': 'Luxury',
    'OTHER': 'Other'
}


class MetaAdsManager:
    """Manages Meta Ads campaign creation and publishing"""

    def __init__(
        self,
        access_token: Optional[str] = None,
        app_secret: Optional[str] = None,
        app_id: Optional[str] = None,
        ad_account_id: Optional[str] = None
    ):
        """
        Initialize Meta Ads API client

        Args:
            access_token: Meta user access token
            app_secret: Meta app secret
            app_id: Meta app ID
            ad_account_id: Meta Ad Account ID (format: act_XXXXXXXXX)
        """
        self.access_token = access_token or os.getenv('META_ACCESS_TOKEN')
        self.app_secret = app_secret or os.getenv('META_APP_SECRET')
        self.app_id = app_id or os.getenv('META_APP_ID')
        self.ad_account_id = ad_account_id or os.getenv('META_AD_ACCOUNT_ID')

        # Validate credentials
        if not all([self.access_token, self.app_secret, self.app_id, self.ad_account_id]):
            raise ValueError(
                "Missing Meta API credentials. Please set META_ACCESS_TOKEN, "
                "META_APP_SECRET, META_APP_ID, and META_AD_ACCOUNT_ID in .env file"
            )

        # Initialize Facebook Ads API
        FacebookAdsApi.init(
            app_id=self.app_id,
            app_secret=self.app_secret,
            access_token=self.access_token
        )

        self.ad_account = AdAccount(self.ad_account_id)

    def create_campaign(
        self,
        name: str,
        objective: str = 'OUTCOME_SALES',
        status: str = 'PAUSED',
        special_ad_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Meta Ads campaign

        Args:
            name: Campaign name
            objective: Campaign objective (OUTCOME_SALES, OUTCOME_LEADS, etc.)
            status: Campaign status (ACTIVE, PAUSED)
            special_ad_categories: List of special ad categories if applicable

        Returns:
            Dict with campaign details including campaign_id
        """
        params = {
            Campaign.Field.name: name,
            Campaign.Field.objective: objective,
            Campaign.Field.status: status,
            # Meta requires special_ad_categories even if empty
            Campaign.Field.special_ad_categories: special_ad_categories if special_ad_categories else [],
            # Required when using ad set level budgets (not campaign level)
            'is_adset_budget_sharing_enabled': False
        }

        try:
            campaign = _retry_api_call(
                self.ad_account.create_campaign, params=params
            )

            return {
                'campaign_id': campaign.get_id(),
                'name': name,
                'objective': objective,
                'status': status,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create campaign'
            }

    def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        daily_budget: int,  # In cents (e.g., 2000 = $20.00)
        targeting: Dict[str, Any],
        billing_event: str = 'IMPRESSIONS',
        optimization_goal: str = 'REACH',
        bid_amount: Optional[int] = None,
        status: str = 'PAUSED'
    ) -> Dict[str, Any]:
        """
        Create an ad set within a campaign

        Args:
            campaign_id: Parent campaign ID
            name: Ad set name
            daily_budget: Daily budget in cents
            targeting: Targeting specifications (age, gender, geo, interests)
            billing_event: Billing event type
            optimization_goal: Optimization goal
            bid_amount: Optional bid amount in cents
            status: Ad set status

        Returns:
            Dict with ad set details including ad_set_id
        """
        params = {
            AdSet.Field.name: name,
            AdSet.Field.campaign_id: campaign_id,
            AdSet.Field.daily_budget: daily_budget,
            AdSet.Field.billing_event: billing_event,
            AdSet.Field.optimization_goal: optimization_goal,
            AdSet.Field.targeting: targeting,
            AdSet.Field.status: status,
        }

        if bid_amount:
            params[AdSet.Field.bid_amount] = bid_amount

        try:
            ad_set = _retry_api_call(
                self.ad_account.create_ad_set, params=params
            )

            return {
                'ad_set_id': ad_set.get_id(),
                'name': name,
                'daily_budget': daily_budget,
                'status': status,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create ad set'
            }

    def build_targeting_spec(
        self,
        age_min: int = 18,
        age_max: int = 65,
        genders: List[int] = [1, 2],  # 1=male, 2=female, 0=all
        geo_locations: Optional[Dict[str, Any]] = None,
        interests: Optional[List[Dict[str, Any]]] = None,
        flexible_spec: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build Meta Ads targeting specification

        Args:
            age_min: Minimum age
            age_max: Maximum age
            genders: List of gender codes
            geo_locations: Geographic targeting (countries, cities, etc.)
            interests: Interest-based targeting
            flexible_spec: Advanced flexible targeting

        Returns:
            Targeting specification dict
        """
        targeting = {
            'age_min': age_min,
            'age_max': age_max,
            'genders': genders,
            # Meta now requires advantage_audience flag in targeting_automation
            'targeting_automation': {
                'advantage_audience': 0  # 0=disabled, 1=enabled
            }
        }

        # Default to US if no geo specified
        if geo_locations:
            targeting['geo_locations'] = geo_locations
        else:
            targeting['geo_locations'] = {'countries': ['US']}

        if interests:
            targeting['interests'] = interests

        if flexible_spec:
            targeting['flexible_spec'] = flexible_spec

        return targeting

    def create_ad_creative(
        self,
        name: str,
        object_story_spec: Dict[str, Any],
        degrees_of_freedom_spec: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an ad creative (the actual ad content)

        Args:
            name: Creative name
            object_story_spec: Story specification (link, message, image, etc.)
            degrees_of_freedom_spec: Dynamic creative optimization settings

        Returns:
            Dict with creative details including creative_id
        """
        params = {
            AdCreative.Field.name: name,
            AdCreative.Field.object_story_spec: object_story_spec,
        }

        if degrees_of_freedom_spec:
            params[AdCreative.Field.degrees_of_freedom_spec] = degrees_of_freedom_spec

        try:
            creative = _retry_api_call(
                self.ad_account.create_ad_creative, params=params
            )

            return {
                'creative_id': creative.get_id(),
                'name': name,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create ad creative'
            }

    def upload_image(
        self,
        image_path: str,
        image_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an image to Meta Ads

        Args:
            image_path: Local path to image file
            image_name: Optional image name

        Returns:
            Dict with image hash and details
        """
        try:
            image = AdImage(parent_id=self.ad_account_id)
            image[AdImage.Field.filename] = image_path
            if image_name:
                image[AdImage.Field.name] = image_name

            _retry_api_call(image.remote_create)

            return {
                'image_hash': image[AdImage.Field.hash],
                'url': image.get('url', ''),
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to upload image'
            }

    def upload_image_from_url(
        self,
        image_url: str,
        image_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an image to Meta Ads from a URL (e.g., S3 public URL)

        Args:
            image_url: Public URL of the image
            image_name: Optional image name

        Returns:
            Dict with image hash and details
        """
        try:
            image = AdImage(parent_id=self.ad_account_id)
            image[AdImage.Field.url] = image_url
            if image_name:
                image[AdImage.Field.name] = image_name

            _retry_api_call(image.remote_create)

            return {
                'image_hash': image[AdImage.Field.hash],
                'url': image_url,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to upload image from URL'
            }

    def upload_video(
        self,
        video_path: str,
        video_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a video to Meta Ads.

        Args:
            video_path: Local path to video file
            video_name: Optional video name

        Returns:
            Dict with video_id and details
        """
        try:
            video = AdVideo(parent_id=self.ad_account_id)
            video[AdVideo.Field.filepath] = video_path
            if video_name:
                video[AdVideo.Field.name] = video_name

            _retry_api_call(video.remote_create)

            return {
                'video_id': video.get_id(),
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to upload video'
            }

    def upload_video_from_url(
        self,
        video_url: str,
        video_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a video to Meta Ads from a URL.

        Args:
            video_url: Public URL of the video
            video_name: Optional video name

        Returns:
            Dict with video_id and details
        """
        try:
            video = AdVideo(parent_id=self.ad_account_id)
            video[AdVideo.Field.file_url] = video_url
            if video_name:
                video[AdVideo.Field.name] = video_name

            _retry_api_call(video.remote_create)

            return {
                'video_id': video.get_id(),
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to upload video from URL'
            }

    def create_carousel_creative(
        self,
        name: str,
        page_id: str,
        cards: List[Dict[str, Any]],
        message: str = '',
        link: str = ''
    ) -> Dict[str, Any]:
        """
        Create a carousel ad creative with multiple cards.

        Args:
            name: Creative name
            page_id: Facebook Page ID
            cards: List of card dicts, each with:
                - image_hash or video_id
                - link
                - name (headline)
                - description (optional)
                - call_to_action (optional, dict with 'type' and 'value')
            message: Primary text shown above the carousel
            link: Default destination URL

        Returns:
            Dict with creative_id and details
        """
        try:
            child_attachments = []
            for card in cards:
                attachment: Dict[str, Any] = {
                    'link': card.get('link', link),
                    'name': card.get('name', ''),
                }
                if card.get('description'):
                    attachment['description'] = card['description']
                if card.get('image_hash'):
                    attachment['image_hash'] = card['image_hash']
                if card.get('video_id'):
                    attachment['video_id'] = card['video_id']
                if card.get('call_to_action'):
                    attachment['call_to_action'] = card['call_to_action']
                child_attachments.append(attachment)

            object_story_spec = {
                'page_id': page_id,
                'link_data': {
                    'message': message,
                    'link': link,
                    'child_attachments': child_attachments,
                }
            }

            params = {
                AdCreative.Field.name: name,
                AdCreative.Field.object_story_spec: object_story_spec,
            }

            creative = _retry_api_call(
                self.ad_account.create_ad_creative, params=params
            )

            return {
                'creative_id': creative.get_id(),
                'name': name,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create carousel creative'
            }

    def create_video_creative(
        self,
        name: str,
        page_id: str,
        video_id: str,
        message: str = '',
        link: str = '',
        headline: str = '',
        description: str = '',
        call_to_action_type: str = 'LEARN_MORE',
        image_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a video ad creative.

        Args:
            name: Creative name
            page_id: Facebook Page ID
            video_id: Meta video ID from upload
            message: Primary text
            link: Destination URL
            headline: Ad headline
            description: Ad description
            call_to_action_type: CTA button type
            image_hash: Optional thumbnail image hash

        Returns:
            Dict with creative_id and details
        """
        try:
            video_data: Dict[str, Any] = {
                'video_id': video_id,
                'message': message,
                'link_description': description,
                'call_to_action': {
                    'type': call_to_action_type,
                    'value': {'link': link}
                }
            }
            if headline:
                video_data['title'] = headline
            if image_hash:
                video_data['image_hash'] = image_hash

            object_story_spec = {
                'page_id': page_id,
                'video_data': video_data,
            }

            params = {
                AdCreative.Field.name: name,
                AdCreative.Field.object_story_spec: object_story_spec,
            }

            creative = _retry_api_call(
                self.ad_account.create_ad_creative, params=params
            )

            return {
                'creative_id': creative.get_id(),
                'name': name,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create video creative'
            }

    def activate_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Activate a paused campaign by setting status to ACTIVE.

        Args:
            campaign_id: Meta campaign ID to activate

        Returns:
            Dict with success flag and details
        """
        try:
            campaign = Campaign(campaign_id)
            _retry_api_call(
                campaign.api_update,
                params={Campaign.Field.status: Campaign.Status.active}
            )

            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': 'ACTIVE',
                'ads_manager_url': self.get_ads_manager_url(campaign_id),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'campaign_id': campaign_id,
                'details': 'Failed to activate campaign'
            }

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pause an active campaign.

        Args:
            campaign_id: Meta campaign ID to pause

        Returns:
            Dict with success flag and details
        """
        try:
            campaign = Campaign(campaign_id)
            _retry_api_call(
                campaign.api_update,
                params={Campaign.Field.status: Campaign.Status.paused}
            )

            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': 'PAUSED',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'campaign_id': campaign_id,
                'details': 'Failed to pause campaign'
            }

    @staticmethod
    def get_ads_manager_url(campaign_id: str) -> str:
        """Get the Ads Manager URL for a campaign."""
        return f"https://www.facebook.com/adsmanager/manage/campaigns?act=&campaign_ids={campaign_id}"

    @staticmethod
    def validate_campaign_data(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all required fields before submitting to Meta API.

        Args:
            campaign_data: Campaign specification to validate

        Returns:
            Dict with 'valid' bool and list of 'errors'
        """
        errors = []

        # Check project URL
        project_url = campaign_data.get('project_url', '')
        if not project_url or not project_url.startswith(('http://', 'https://')):
            errors.append('project_url must be a valid HTTP(S) URL')

        # Check creatives
        creatives = campaign_data.get('suggested_creatives', [])
        if not creatives:
            # Also accept direct ad data
            ad = campaign_data.get('ad', {})
            if not ad.get('headline') and not ad.get('primaryText'):
                errors.append('At least one creative with headline/primary text is required')

        # Check budget
        budget = campaign_data.get('budget_daily', campaign_data.get('budget', 0))
        if isinstance(budget, (int, float)) and budget < 100:
            # If in cents, minimum is 100 cents ($1)
            if budget > 0 and budget < 1:
                errors.append('Daily budget must be at least $1.00')

        # Check image briefs (at least one should have an image_url)
        image_briefs = campaign_data.get('image_briefs', [])
        has_image = any(b.get('image_url') for b in image_briefs)
        ad_image = campaign_data.get('ad', {}).get('imageUrl')
        if not has_image and not ad_image:
            # Warning but not blocking
            errors.append('WARNING: No images available - ad will be created without an image')

        return {
            'valid': not any(e for e in errors if not e.startswith('WARNING:')),
            'errors': errors,
            'warnings': [e for e in errors if e.startswith('WARNING:')],
        }

    def create_ad(
        self,
        name: str,
        ad_set_id: str,
        creative_id: str,
        status: str = 'PAUSED'
    ) -> Dict[str, Any]:
        """
        Create an ad linking creative to ad set

        Args:
            name: Ad name
            ad_set_id: Parent ad set ID
            creative_id: Ad creative ID
            status: Ad status

        Returns:
            Dict with ad details including ad_id
        """
        params = {
            Ad.Field.name: name,
            Ad.Field.adset_id: ad_set_id,
            Ad.Field.creative: {'creative_id': creative_id},
            Ad.Field.status: status,
        }

        try:
            ad = _retry_api_call(
                self.ad_account.create_ad, params=params
            )

            return {
                'ad_id': ad.get_id(),
                'name': name,
                'status': status,
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create ad'
            }

    def publish_complete_campaign(
        self,
        campaign_data: Dict[str, Any],
        page_id: Optional[str] = None,
        ads_to_publish: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Publish a complete campaign with ad sets and ads.
        Supports multiple ads with partial failure recovery.

        Args:
            campaign_data: Complete campaign specification from CampaignDraft
            page_id: Facebook Page ID for ad creative (optional, falls back to env var)
            ads_to_publish: Optional list of ad dicts to create. Each dict has:
                - headline, primaryText, description, imageUrl (optional)
                Defaults to using suggested_creatives from campaign_data.

        Returns:
            Dict with all created resource IDs, Ads Manager link, and status
        """
        results: Dict[str, Any] = {
            'success': False,
            'campaign': None,
            'ad_sets': [],
            'creatives': [],
            'ads': [],
            'errors': [],
            'ads_manager_url': None,
        }

        try:
            # 0. Pre-submission validation
            validation = self.validate_campaign_data(campaign_data)
            if not validation['valid']:
                results['errors'].extend(
                    [{'error': e, 'details': 'Validation failed'} for e in validation['errors']
                     if not e.startswith('WARNING:')]
                )
                return results

            # 0b. Validate page_id
            if not page_id:
                page_id = os.getenv('META_DEFAULT_PAGE_ID')

            if not page_id:
                results['errors'].append({
                    'error': 'Missing Facebook Page ID',
                    'details': 'page_id parameter not provided and META_DEFAULT_PAGE_ID not set in .env'
                })
                return results

            # 1. Create Campaign
            campaign_name = f"Idea2Ad - {campaign_data.get('project_url', 'Campaign')}"
            campaign_result = self.create_campaign(
                name=campaign_name,
                objective=campaign_data.get('objective', 'OUTCOME_SALES'),
                status='PAUSED'  # Start paused for safety
            )

            if not campaign_result.get('success'):
                results['errors'].append(campaign_result)
                return results

            results['campaign'] = campaign_result
            campaign_id = campaign_result['campaign_id']
            results['ads_manager_url'] = self.get_ads_manager_url(campaign_id)

            # 2. Build targeting from analysis
            targeting_data = campaign_data.get('targeting', {})
            genders = []
            for g in targeting_data.get('genders', ['male', 'female']):
                if g.lower() == 'male':
                    genders.append(1)
                elif g.lower() == 'female':
                    genders.append(2)

            if not genders:
                genders = [1, 2]  # Default to all

            # Get geo_locations (already in proper format from request)
            geo_locations = targeting_data.get('geo_locations', {'countries': ['US']})

            targeting_spec = self.build_targeting_spec(
                age_min=targeting_data.get('age_min', 18),
                age_max=targeting_data.get('age_max', 65),
                genders=genders,
                geo_locations=geo_locations
            )

            # 3. Create Ad Set
            daily_budget_cents = int(campaign_data.get('budget_daily', 20.0) * 100)
            ad_set_result = self.create_ad_set(
                campaign_id=campaign_id,
                name=f"{campaign_name} - Ad Set 1",
                daily_budget=daily_budget_cents,
                targeting=targeting_spec,
                bid_amount=200,  # $2.00 CPM bid cap (in cents)
                status='PAUSED'
            )

            if not ad_set_result.get('success'):
                results['errors'].append(ad_set_result)
                return results

            results['ad_sets'].append(ad_set_result)
            ad_set_id = ad_set_result['ad_set_id']

            # 4. Determine ads to create
            # Use explicit ads_to_publish if provided, else fall back to suggested_creatives
            ad_specs = []
            if ads_to_publish:
                ad_specs = ads_to_publish
            else:
                creatives = campaign_data.get('suggested_creatives', [])
                image_briefs = campaign_data.get('image_briefs', [])
                if creatives:
                    for i, creative in enumerate(creatives):
                        spec = {
                            'headline': creative.get('headline', 'Limited Time Offer'),
                            'primaryText': creative.get('primary_text', 'Check out our product!'),
                            'description': creative.get('description', ''),
                        }
                        # Try to pair with an image brief
                        if i < len(image_briefs) and image_briefs[i].get('image_url'):
                            spec['imageUrl'] = image_briefs[i]['image_url']
                        elif image_briefs:
                            # Use first available image
                            for brief in image_briefs:
                                if brief.get('image_url'):
                                    spec['imageUrl'] = brief['image_url']
                                    break
                        ad_specs.append(spec)

            # If still no ad specs, create one from defaults
            if not ad_specs:
                ad_specs = [{
                    'headline': 'Limited Time Offer',
                    'primaryText': 'Check out our amazing product!',
                    'description': '',
                }]

            project_url = campaign_data.get('project_url', 'https://example.com')

            # 5. Create each ad with partial failure recovery
            for i, ad_spec in enumerate(ad_specs):
                ad_num = i + 1
                try:
                    # Upload image if available
                    image_hash = None
                    image_url = ad_spec.get('imageUrl')
                    if image_url:
                        img_result = self.upload_image_from_url(
                            image_url=image_url,
                            image_name=f"Idea2Ad - Ad {ad_num}"
                        )
                        if img_result.get('success'):
                            image_hash = img_result['image_hash']
                        else:
                            logger.warning(f"Image upload failed for ad {ad_num}: {img_result.get('error')}")

                    # Build creative spec
                    link_data: Dict[str, Any] = {
                        'link': project_url,
                        'message': ad_spec.get('primaryText', ''),
                        'name': ad_spec.get('headline', ''),
                        'call_to_action': {
                            'type': campaign_data.get('call_to_action', 'LEARN_MORE')
                        }
                    }
                    if ad_spec.get('description'):
                        link_data['description'] = ad_spec['description']
                    if image_hash:
                        link_data['image_hash'] = image_hash

                    object_story_spec = {
                        'page_id': page_id,
                        'link_data': link_data
                    }

                    creative_result = self.create_ad_creative(
                        name=f"{campaign_name} - Creative {ad_num}",
                        object_story_spec=object_story_spec
                    )

                    if not creative_result.get('success'):
                        results['errors'].append({
                            'ad_index': i,
                            **creative_result,
                            'note': f'Creative {ad_num} failed - skipping this ad'
                        })
                        continue  # Partial failure: skip to next ad

                    results['creatives'].append(creative_result)
                    creative_id = creative_result['creative_id']

                    # Create ad
                    ad_result = self.create_ad(
                        name=f"{campaign_name} - Ad {ad_num}",
                        ad_set_id=ad_set_id,
                        creative_id=creative_id,
                        status='PAUSED'
                    )

                    if not ad_result.get('success'):
                        results['errors'].append({
                            'ad_index': i,
                            **ad_result,
                            'note': f'Ad {ad_num} creation failed'
                        })
                        continue  # Partial failure: skip to next ad

                    results['ads'].append(ad_result)

                except Exception as ad_exc:
                    logger.error(f"Error creating ad {ad_num}: {ad_exc}")
                    results['errors'].append({
                        'ad_index': i,
                        'error': str(ad_exc),
                        'details': f'Unexpected error creating ad {ad_num}'
                    })
                    # Continue to next ad (partial failure recovery)

            # Mark success if at least one ad was created
            results['success'] = len(results['ads']) > 0

            return results

        except Exception as e:
            results['errors'].append({
                'error': str(e),
                'details': 'Unexpected error during campaign publishing'
            })
            return results


    # =====================================
    # META API TEST METHODS
    # =====================================

    def test_connection(self) -> Dict[str, Any]:
        """
        Test basic API connectivity and credentials

        Returns:
            Dict with success flag, account details, and message
        """
        try:
            # Try to fetch ad account info
            account = self.ad_account.api_get(fields=['name', 'account_status', 'currency'])

            return {
                'success': True,
                'account_name': account.get('name'),
                'account_status': account.get('account_status'),
                'currency': account.get('currency'),
                'account_id': self.ad_account_id,
                'message': 'Successfully connected to Meta API'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to Meta API'
            }

    def test_permissions(self) -> Dict[str, Any]:
        """
        Verify that access token has required permissions

        Returns:
            Dict with success flag, granted/missing permissions, and message
        """
        try:
            # Check what permissions the token has
            me = User(fbid='me')
            permissions = me.api_get(fields=['permissions'])

            required = ['ads_management', 'ads_read', 'pages_manage_ads']
            granted = [
                p['permission']
                for p in permissions.get('permissions', {}).get('data', [])
                if p['status'] == 'granted'
            ]

            missing = [p for p in required if p not in granted]

            return {
                'success': len(missing) == 0,
                'granted_permissions': granted,
                'missing_permissions': missing,
                'required_permissions': required,
                'message': 'All required permissions granted' if len(missing) == 0
                          else f'Missing permissions: {", ".join(missing)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to check permissions'
            }

    def test_page_access(self, page_id: str) -> Dict[str, Any]:
        """
        Verify access to a Facebook Page

        Args:
            page_id: Facebook Page ID to test

        Returns:
            Dict with success flag, page details, and message
        """
        try:
            page = Page(page_id)
            page_data = page.api_get(fields=['name', 'access_token'])

            return {
                'success': True,
                'page_id': page_id,
                'page_name': page_data.get('name'),
                'has_page_token': bool(page_data.get('access_token')),
                'message': f'Successfully accessed page: {page_data.get("name")}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'page_id': page_id,
                'message': f'Failed to access Facebook Page {page_id}'
            }

    def validate_budget(self, daily_budget_cents: int) -> Dict[str, Any]:
        """
        Validate that budget meets Meta's minimum requirements

        Args:
            daily_budget_cents: Daily budget in cents

        Returns:
            Dict with success flag and budget validation details
        """
        try:
            # Meta typically requires minimum $1/day = 100 cents
            min_budget = 100

            return {
                'success': daily_budget_cents >= min_budget,
                'daily_budget_cents': daily_budget_cents,
                'daily_budget_dollars': daily_budget_cents / 100,
                'min_required_cents': min_budget,
                'min_required_dollars': min_budget / 100,
                'message': 'Budget valid' if daily_budget_cents >= min_budget
                          else f'Budget too low. Minimum: ${min_budget/100}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to validate budget'
            }

    def run_all_tests(self, page_id: str, daily_budget_cents: int = 2000) -> Dict[str, Any]:
        """
        Run all Meta API tests (comprehensive health check)

        Args:
            page_id: Facebook Page ID to test
            daily_budget_cents: Daily budget to validate (default: 2000 = $20)

        Returns:
            Dict with all test results and overall success flag
        """
        results = {
            'overall_success': True,
            'tests': {}
        }

        # Run all tests
        results['tests']['connection'] = self.test_connection()
        results['tests']['permissions'] = self.test_permissions()
        results['tests']['page_access'] = self.test_page_access(page_id)
        results['tests']['budget_validation'] = self.validate_budget(daily_budget_cents)

        # Check if all tests passed
        for test_name, test_result in results['tests'].items():
            if not test_result.get('success', False):
                results['overall_success'] = False

        results['message'] = 'All tests passed ✅' if results['overall_success'] else 'Some tests failed ❌'
        results['summary'] = {
            'total_tests': len(results['tests']),
            'passed': sum(1 for t in results['tests'].values() if t.get('success', False)),
            'failed': sum(1 for t in results['tests'].values() if not t.get('success', False))
        }

        return results


    # =====================================
    # 2-TIER BUSINESS MANAGER METHODS
    # =====================================

    def create_client_business_manager(
        self,
        client_name: str,
        primary_page_id: str,
        vertical: str = 'ECOMMERCE',
        timezone_id: int = 1  # 1 = America/Los_Angeles
    ) -> Dict[str, Any]:
        """
        Create a Child Business Manager for a client (2-Tier Solution)

        IMPORTANT: Requires Parent Business Manager with:
        - Line of Credit (LOC)
        - business_management permission
        - Meta partner approval

        Args:
            client_name: Name of the client's business
            primary_page_id: Facebook Page ID (required - cannot be skipped)
            vertical: Business vertical (see BUSINESS_VERTICALS)
            timezone_id: Timezone ID (default: 1 for US Pacific)

        Returns:
            Dict with child_business_id and details
        """
        # Get parent Business Manager ID from environment
        parent_business_id = os.getenv('META_PARENT_BUSINESS_ID')

        if not parent_business_id:
            return {
                'success': False,
                'error': 'META_PARENT_BUSINESS_ID not set in .env file',
                'details': 'Parent Business Manager ID required for 2-Tier solution'
            }

        try:
            parent_business = Business(parent_business_id)

            params = {
                'name': client_name,
                'primary_page': primary_page_id,
                'timezone_id': timezone_id,
                'vertical': vertical,
            }

            child_business = parent_business.create_managed_business(
                fields=[],
                params=params
            )

            return {
                'success': True,
                'child_business_id': child_business.get_id(),
                'client_name': client_name,
                'vertical': vertical,
                'note': 'Child Business Manager created successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create client Business Manager. Check permissions and LOC setup.'
            }

    def create_ad_account_for_client(
        self,
        child_business_id: str,
        account_name: str,
        currency: str = 'USD',
        timezone_id: int = 1
    ) -> Dict[str, Any]:
        """
        Create an Ad Account under a Child Business Manager

        Args:
            child_business_id: Child Business Manager ID
            account_name: Name for the ad account
            currency: Currency code (USD, EUR, etc.)
            timezone_id: Timezone ID

        Returns:
            Dict with ad_account_id and details
        """
        try:
            child_business = Business(child_business_id)

            params = {
                'name': account_name,
                'currency': currency,
                'timezone_id': timezone_id,
                'end_advertiser': child_business_id,  # Sets the child as end advertiser
            }

            ad_account = child_business.create_ad_account(params=params)

            return {
                'success': True,
                'ad_account_id': ad_account.get_id(),
                'account_name': account_name,
                'currency': currency
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': 'Failed to create ad account for client'
            }

    def get_client_business_managers(self) -> Dict[str, Any]:
        """
        Get all Child Business Managers (clients) under Parent BM

        Returns:
            Dict with list of child businesses
        """
        parent_business_id = os.getenv('META_PARENT_BUSINESS_ID')

        if not parent_business_id:
            return {
                'success': False,
                'error': 'META_PARENT_BUSINESS_ID not set',
                'child_businesses': []
            }

        try:
            parent_business = Business(parent_business_id)

            # Get managed businesses
            child_businesses = parent_business.get_owned_businesses(
                fields=['id', 'name', 'created_time', 'verification_status']
            )

            return {
                'success': True,
                'child_businesses': [
                    {
                        'id': biz.get('id'),
                        'name': biz.get('name'),
                        'created_time': biz.get('created_time'),
                        'verification_status': biz.get('verification_status')
                    }
                    for biz in child_businesses
                ],
                'count': len(child_businesses)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'child_businesses': []
            }

    def setup_client_onboarding_flow(
        self,
        client_name: str,
        primary_page_id: str,
        vertical: str = 'ECOMMERCE',
        initial_budget: float = 20.0
    ) -> Dict[str, Any]:
        """
        Complete client onboarding workflow (2-Tier)
        Creates Child BM + Ad Account in one flow

        Args:
            client_name: Client business name
            primary_page_id: Facebook Page ID
            vertical: Business vertical
            initial_budget: Initial daily budget in dollars

        Returns:
            Dict with all created resources
        """
        results = {
            'success': False,
            'child_business': None,
            'ad_account': None,
            'errors': []
        }

        # Step 1: Create Child Business Manager
        bm_result = self.create_client_business_manager(
            client_name=client_name,
            primary_page_id=primary_page_id,
            vertical=vertical
        )

        if not bm_result.get('success'):
            results['errors'].append(bm_result)
            return results

        results['child_business'] = bm_result
        child_business_id = bm_result['child_business_id']

        # Step 2: Create Ad Account
        account_result = self.create_ad_account_for_client(
            child_business_id=child_business_id,
            account_name=f"{client_name} - Ads"
        )

        if not account_result.get('success'):
            results['errors'].append(account_result)
            # Partial success - BM created but not account
            return results

        results['ad_account'] = account_result
        results['success'] = True

        # Note: LOC sharing would happen here if implemented
        results['note'] = (
            'Client onboarded successfully. '
            'Remember to share Line of Credit from Parent BM for billing.'
        )

        return results


def get_meta_manager() -> MetaAdsManager:
    """Factory function to get initialized Meta Ads Manager"""
    return MetaAdsManager()
