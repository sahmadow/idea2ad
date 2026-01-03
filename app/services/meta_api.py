"""
Meta (Facebook) Marketing API Integration Service
Handles campaign creation and publishing to Meta Ads Manager
"""

import os
from typing import Dict, Any, List, Optional
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.user import User
from facebook_business.adobjects.page import Page
from dotenv import load_dotenv

load_dotenv()


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
            campaign = self.ad_account.create_campaign(params=params)

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
            ad_set = self.ad_account.create_ad_set(params=params)

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
            creative = self.ad_account.create_ad_creative(params=params)

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

            image.remote_create()

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

            image.remote_create()

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
            ad = self.ad_account.create_ad(params=params)

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
        page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a complete campaign with ad sets and ads

        Args:
            campaign_data: Complete campaign specification from CampaignDraft
            page_id: Facebook Page ID for ad creative (optional, falls back to env var)

        Returns:
            Dict with all created resource IDs and status
        """
        results = {
            'success': False,
            'campaign': None,
            'ad_sets': [],
            'creatives': [],
            'ads': [],
            'errors': []
        }

        try:
            # 0. Validate page_id
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

            # 4. Create Ads from suggested creatives
            # Get headline and primary text from creatives
            creatives = campaign_data.get('suggested_creatives', [])
            if creatives and len(creatives) > 0:
                first_creative = creatives[0]
                headline = first_creative.get('headline', 'Limited Time Offer')
                primary_text = first_creative.get('primary_text', 'Check out our amazing product!')
            else:
                headline = 'Limited Time Offer'
                primary_text = 'Check out our amazing product!'

            # 4a. Try to upload image from image_briefs if available
            image_hash = None
            image_briefs = campaign_data.get('image_briefs', [])
            for brief in image_briefs:
                image_url = brief.get('image_url')
                if image_url:
                    img_result = self.upload_image_from_url(
                        image_url=image_url,
                        image_name=f"Idea2Ad - {brief.get('approach', 'image')}"
                    )
                    if img_result.get('success'):
                        image_hash = img_result['image_hash']
                        break  # Use first successful image

            # Build object story spec for link ad
            link_data = {
                'link': campaign_data.get('project_url', 'https://example.com'),
                'message': primary_text,
                'name': headline,
                'call_to_action': {
                    'type': 'LEARN_MORE'
                }
            }

            # Add image hash if we have one
            if image_hash:
                link_data['image_hash'] = image_hash

            object_story_spec = {
                'page_id': page_id,
                'link_data': link_data
            }

            creative_result = self.create_ad_creative(
                name=f"{campaign_name} - Creative 1",
                object_story_spec=object_story_spec
            )

            if not creative_result.get('success'):
                results['errors'].append(creative_result)
                results['errors'].append({
                    'note': 'Creative creation failed. You may need to provide a Facebook Page ID.'
                })
                # Continue anyway to show what was created
                results['success'] = True  # Partial success
                return results

            results['creatives'].append(creative_result)
            creative_id = creative_result['creative_id']

            # 5. Create Ad
            ad_result = self.create_ad(
                name=f"{campaign_name} - Ad 1",
                ad_set_id=ad_set_id,
                creative_id=creative_id,
                status='PAUSED'
            )

            if not ad_result.get('success'):
                results['errors'].append(ad_result)
                results['success'] = True  # Partial success (campaign & ad set created)
                return results

            results['ads'].append(ad_result)
            results['success'] = True

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
