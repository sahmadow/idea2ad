# Meta Ads Integration Guide for Idea2Ad

This guide explains how to set up and use the Meta (Facebook) Ads API integration for Idea2Ad, including both simple single-account mode and the advanced 2-Tier Business Manager solution for agencies and SaaS platforms.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Setup: Simple Mode (Single Account)](#setup-simple-mode)
4. [Setup: 2-Tier Mode (Multi-Client/Agency)](#setup-2-tier-mode)
5. [API Endpoints](#api-endpoints)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Idea2Ad supports two modes of Meta Ads integration:

### Simple Mode
- **Best for**: Individual advertisers, small businesses
- **Creates campaigns in**: A single Meta Ad Account
- **Setup difficulty**: Easy
- **Billing**: Direct to your own Ad Account

### 2-Tier Mode (Advanced)
- **Best for**: Agencies, SaaS platforms, managing multiple clients
- **Creates**: Separate Business Managers for each client
- **Setup difficulty**: Advanced (requires Meta partner approval)
- **Billing**: Centralized Line of Credit (LOC) shared from Parent BM

---

## Prerequisites

### For Both Modes

1. **Meta for Developers Account**
   - Create an app at https://developers.facebook.com/
   - Note your App ID and App Secret

2. **Facebook Business Manager**
   - Set up at https://business.facebook.com/
   - Create or have access to a Business Manager

3. **Access Token**
   - Generate a System User token (recommended for production)
   - Or use personal access token for testing

### For 2-Tier Mode Only

4. **Meta Partner Approval**
   - Your app needs `business_management` permission
   - Parent Business Manager must have Line of Credit (LOC)
   - Requires approval from Meta

5. **Facebook Page**
   - Every Child Business Manager requires a Primary Page
   - Create pages in advance or use existing ones

---

## Setup: Simple Mode

### Step 1: Get Meta Credentials

1. **Create a Meta App**
   - Go to https://developers.facebook.com/apps/
   - Click "Create App" → Choose "Business" type
   - Note your `App ID` and `App Secret`

2. **Generate Access Token**
   - In App Dashboard → Tools → Access Token Tool
   - Generate a System User token (recommended)
   - Grant these permissions:
     - `ads_management`
     - `ads_read`
     - `pages_read_engagement`
     - `pages_manage_ads`

3. **Get Ad Account ID**
   - Go to https://business.facebook.com/
   - Navigate to Business Settings → Ad Accounts
   - Note your Ad Account ID (format: `act_XXXXXXXXXXX`)

### Step 2: Configure .env File

```env
# Meta (Facebook) Marketing API Credentials
META_ACCESS_TOKEN=YOUR_LONG_LIVED_ACCESS_TOKEN_HERE
META_APP_SECRET=your_app_secret_here
META_APP_ID=your_app_id_here
META_AD_ACCOUNT_ID=act_XXXXXXXXXXX
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Test the Integration

```bash
# Start the backend
python -m uvicorn app.main:app --reload

# Check Meta config
curl http://localhost:8000/meta/config
```

You should see `"simple_mode": { "enabled": true }`

---

## Setup: 2-Tier Mode

### Step 1: Meet Prerequisites

✅ Complete all Simple Mode setup steps first
✅ Your app must be approved with `business_management` permission
✅ Parent Business Manager must have Line of Credit (LOC)
✅ Have Facebook Pages ready for each client

### Step 2: Get Parent Business Manager ID

1. Go to https://business.facebook.com/
2. Click on Business Settings → Business Info
3. Note your Business Manager ID (numeric ID)

### Step 3: Apply for Business Management Permission

1. In Meta App Dashboard → App Review → Permissions and Features
2. Request `business_management` advanced access
3. Provide use case: "Creating managed Business Managers for clients"
4. **Wait for approval** (can take several days)

### Step 4: Set Up Line of Credit

1. Contact your Meta account representative
2. Request Line of Credit (LOC) setup for your Parent BM
3. Once approved, LOC can be shared with Child BMs

### Step 5: Update .env File

```env
# All Simple Mode credentials (required)
META_ACCESS_TOKEN=YOUR_SYSTEM_USER_TOKEN
META_APP_SECRET=your_app_secret
META_APP_ID=your_app_id
META_AD_ACCOUNT_ID=act_XXXXXXXXXXX

# 2-Tier specific (required for multi-client)
META_PARENT_BUSINESS_ID=YOUR_PARENT_BUSINESS_ID_HERE
META_DEFAULT_PAGE_ID=YOUR_DEFAULT_PAGE_ID_HERE
```

### Step 6: Test 2-Tier Setup

```bash
curl http://localhost:8000/meta/config
```

You should see `"two_tier_mode": { "enabled": true }`

---

## API Endpoints

### 1. Check Configuration

**GET** `/meta/config`

Returns configuration status and available business verticals.

```json
{
  "simple_mode": {
    "enabled": true,
    "requires": [...]
  },
  "two_tier_mode": {
    "enabled": true,
    "requires": [...]
  },
  "business_verticals": ["ECOMMERCE", "ADVERTISING", ...]
}
```

### 2. Publish Campaign (Simple Mode)

**POST** `/meta/publish`

Publishes a campaign draft to your Meta Ad Account.

```json
{
  "campaign_draft": {
    "project_url": "https://example.com",
    "analysis": {...},
    "targeting": {...},
    "suggested_creatives": [...],
    "status": "ANALYZED"
  },
  "page_id": "YOUR_FB_PAGE_ID"
}
```

### 3. Onboard New Client (2-Tier)

**POST** `/meta/client/onboard`

Creates a Child Business Manager and Ad Account for a new client.

```json
{
  "client_name": "Acme Corp",
  "primary_page_id": "123456789",
  "vertical": "ECOMMERCE",
  "initial_budget": 50.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Client onboarded successfully",
  "data": {
    "child_business": {
      "child_business_id": "456789123",
      "client_name": "Acme Corp"
    },
    "ad_account": {
      "ad_account_id": "act_987654321",
      "account_name": "Acme Corp - Ads"
    },
    "note": "Remember to share Line of Credit from Parent BM"
  }
}
```

### 4. List All Clients (2-Tier)

**GET** `/meta/clients`

Lists all Child Business Managers under your Parent BM.

```json
{
  "success": true,
  "clients": [
    {
      "id": "456789123",
      "name": "Acme Corp",
      "created_time": "2025-01-15T10:30:00+0000",
      "verification_status": "not_verified"
    }
  ],
  "count": 1
}
```

---

## Usage Examples

### Example 1: Simple Campaign Publishing

```python
import requests

# 1. Analyze landing page
analyze_response = requests.post('http://localhost:8000/analyze', json={
    "url": "https://myproduct.com"
})

campaign_draft = analyze_response.json()

# 2. Publish to Meta
publish_response = requests.post('http://localhost:8000/meta/publish', json={
    "campaign_draft": campaign_draft,
    "page_id": "YOUR_PAGE_ID"
})

result = publish_response.json()
print(f"Campaign ID: {result['data']['campaign']['campaign_id']}")
```

### Example 2: Onboard Multiple Clients

```python
clients = [
    {"name": "Client A", "page_id": "111111", "vertical": "ECOMMERCE"},
    {"name": "Client B", "page_id": "222222", "vertical": "RETAIL"},
    {"name": "Client C", "page_id": "333333", "vertical": "TECHNOLOGY"},
]

for client in clients:
    response = requests.post('http://localhost:8000/meta/client/onboard', json={
        "client_name": client["name"],
        "primary_page_id": client["page_id"],
        "vertical": client["vertical"],
        "initial_budget": 25.0
    })

    result = response.json()
    if result["success"]:
        print(f"✅ {client['name']}: BM ID = {result['data']['child_business']['child_business_id']}")
    else:
        print(f"❌ {client['name']}: {result['message']}")
```

---

## Troubleshooting

### Error: "Missing Meta API credentials"

**Solution**: Check that all required environment variables are set in `.env`:
- `META_ACCESS_TOKEN`
- `META_APP_SECRET`
- `META_APP_ID`
- `META_AD_ACCOUNT_ID`

### Error: "META_PARENT_BUSINESS_ID not set"

**Solution**: For 2-Tier features, add `META_PARENT_BUSINESS_ID` to `.env`

### Error: "Failed to create client Business Manager"

**Possible causes**:
1. **No `business_management` permission** → Apply for advanced access in App Review
2. **No Line of Credit** → Contact Meta to set up LOC for Parent BM
3. **Invalid Page ID** → Verify the primary_page_id exists and you have access
4. **Not a Meta partner** → Some LOC features require Meta partner approval

### Error: "Failed to create ad creative"

**Solution**: Ensure you provide a valid `page_id` when publishing campaigns. The page must be connected to your Business Manager.

### Error: "Access token expired"

**Solution**:
- Use **System User tokens** instead of personal tokens (they don't expire)
- Generate new token in Business Settings → System Users → Generate New Token

### Campaign created but in PAUSED status

**This is intentional!** All campaigns, ad sets, and ads are created in `PAUSED` status for safety. You can activate them manually in Meta Ads Manager after review.

---

## Important Notes

### System User Tokens vs Personal Tokens

**Always use System User tokens for production:**
- ✅ Don't expire
- ✅ Independent of individual Facebook accounts
- ✅ Can be managed by Business Manager
- ❌ Personal tokens expire after 60 days

### Billing

**Simple Mode**: Charged to your Ad Account's payment method

**2-Tier Mode**:
- Child BMs need shared Line of Credit from Parent
- Centralized billing through Parent BM
- Each client's spend tracked separately

### Security Best Practices

1. **Never commit .env file** to version control
2. **Rotate access tokens** periodically
3. **Use least-privilege permissions** (only request permissions you need)
4. **Store tokens securely** (use secret management in production)

### API Rate Limits

Meta enforces rate limits:
- **Marketing API**: 200 calls per user per hour
- **Business Management API**: Lower limits, contact Meta for details

For high-volume operations, contact Meta to request increased limits.

---

## Resources

- **[Meta Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)**
- **[Business Management API](https://developers.facebook.com/docs/marketing-api/business-asset-management)**
- **[Facebook Python Business SDK](https://github.com/facebook/facebook-python-business-sdk)**
- **[Understanding Tier-1 vs Tier-2](https://medium.com/@ashishkumar_81395/understanding-facebook-business-manager-apis-tier-1-vs-tier-2-153ec3894f00)**

---

## Next Steps

1. ✅ Configure your credentials in `.env`
2. ✅ Test with `/meta/config` endpoint
3. ✅ Try publishing a test campaign (Simple Mode)
4. ✅ If using 2-Tier, apply for `business_management` permission
5. ✅ Set up Line of Credit with Meta
6. ✅ Onboard your first client

**Need help?** Check the [troubleshooting section](#troubleshooting) or open an issue on GitHub.
