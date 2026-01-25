# UAT: Publish Campaign Flow

## Prerequisites

### 1. Start Backend (HTTPS required for FB OAuth)
```bash
cd /Users/salehahmadov/Documents/ClineProjects/idea2ad
source venv/bin/activate
python -m uvicorn app.main:app --reload \
  --ssl-keyfile=certs/key.pem \
  --ssl-certfile=certs/cert.pem
```
Backend URL: `https://localhost:8000`

### 2. Start Frontend
```bash
cd /Users/salehahmadov/Documents/ClineProjects/idea2ad/frontend
npm run dev
```
Frontend URL: `https://localhost:5173`

### 3. Facebook Test Account
- At least one Facebook Page
- At least one Ad Account
- Valid payment method on ad account

### 4. Verify Servers Running
```bash
# Backend health check
curl -sk https://localhost:8000/health
# Expected: {"status":"ok"}

# Frontend (open in browser)
open https://localhost:5173
```

> **Note:** Browser will show SSL warning for self-signed certs. Click "Advanced" → "Proceed to localhost" to continue.

## Test Configuration
```yaml
base_url: "https://localhost:5173"
api_url: "https://localhost:8000"
test_url: "https://blacksmith.sh"
expected_min_ads: 1
min_budget: 5
default_budget: 50
```

---

## Scenario 1: Next Button State

### 1.1 Next Button Disabled Without Selection
```
GIVEN user is on ResultsView with generated ads
WHEN no ad is selected
THEN "Next: Publish" button should be disabled
```

**Steps:**
1. Navigate to landing page (http://localhost:5173)
2. Enter URL: `https://blacksmith.sh`
3. Click "Generate Ad"
4. Wait for results page to load
5. Verify "Next: Publish" button exists
6. Verify "Next: Publish" button has `disabled` attribute

**Assertions:**
- [ ] Button with text "Next: Publish" is visible
- [ ] Button is disabled (has disabled attribute or class)

### 1.2 Next Button Enabled After Selection
```
GIVEN user is on ResultsView with generated ads
WHEN user clicks on an ad to select it
THEN "Next: Publish" button should be enabled
```

**Steps:**
1. From ResultsView, click on first ad preview card
2. Verify ad shows selected state (border highlight)
3. Verify "Next: Publish" button is now enabled

**Assertions:**
- [ ] Selected ad has visual indicator (lime border)
- [ ] "Next: Publish" button is enabled (no disabled attribute)

---

## Scenario 2: Navigation Flow

### 2.1 Navigate to Publish View
```
GIVEN user has selected an ad
WHEN user clicks "Next: Publish"
THEN PublishView should render
```

**Steps:**
1. With ad selected, click "Next: Publish" button
2. Wait for page transition

**Assertions:**
- [ ] Page header shows "Publish Campaign"
- [ ] "Back to Results" button is visible
- [ ] Facebook Connection card is visible

### 2.2 Back Navigation Preserves Selection
```
GIVEN user is on PublishView
WHEN user clicks "Back to Results"
THEN ResultsView shows with same ad still selected
```

**Steps:**
1. From PublishView, click "Back to Results"
2. Wait for ResultsView to render

**Assertions:**
- [ ] Previously selected ad still has selected state
- [ ] "Next: Publish" button is still enabled

---

## Scenario 3: Facebook OAuth Flow

### 3.1 Connect Facebook (Not Connected)
```
GIVEN user is not connected to Facebook
WHEN PublishView loads
THEN "Connect with Facebook" button is visible
```

**Steps:**
1. Clear localStorage key `fb_session_id`
2. Navigate to PublishView
3. Verify connection state

**Assertions:**
- [ ] "Connect with Facebook" button is visible
- [ ] No user avatar/name displayed
- [ ] Account Selection card is NOT visible

### 3.2 Facebook OAuth Popup
```
GIVEN user clicks "Connect with Facebook"
WHEN OAuth popup opens
THEN popup should open with correct dimensions
```

**Steps:**
1. Click "Connect with Facebook" button
2. Observe popup window

**Assertions:**
- [ ] Popup opens (not blocked)
- [ ] Popup URL contains `/auth/facebook`
- [ ] Popup dimensions approximately 600x700

### 3.3 Connected State Display
```
GIVEN user completes Facebook OAuth
WHEN connection succeeds
THEN user info and account selection shown
```

**Steps:**
1. Complete OAuth flow in popup
2. Wait for popup to close
3. Observe PublishView update

**Assertions:**
- [ ] User name is displayed
- [ ] Green checkmark shown
- [ ] "Disconnect" link visible
- [ ] Account Selection card appears

---

## Scenario 4: Account Selection

### 4.1 Page Selection Dropdown
```
GIVEN user is connected to Facebook
WHEN Account Selection renders
THEN Facebook Page dropdown shows available pages
```

**Steps:**
1. Click on Facebook Page dropdown
2. Review options

**Assertions:**
- [ ] Dropdown has "Select a page..." placeholder
- [ ] At least one page option available
- [ ] Page options show name and category

### 4.2 Ad Account Selection Dropdown
```
GIVEN user is connected to Facebook
WHEN Account Selection renders
THEN Ad Account dropdown shows available accounts
```

**Steps:**
1. Click on Ad Account dropdown
2. Review options

**Assertions:**
- [ ] Dropdown has "Select an ad account..." placeholder
- [ ] At least one ad account option available
- [ ] Ad account options show name and currency

### 4.3 Payment Status Check
```
GIVEN user selects an ad account
WHEN payment status loads
THEN payment status indicator shown
```

**Steps:**
1. Select an ad account from dropdown
2. Wait for payment status to load

**Assertions:**
- [ ] Payment status shows loading spinner briefly
- [ ] Status shows either "Valid" (green) or "Not Set" (red)
- [ ] If not set, "Add Payment" link visible

---

## Scenario 5: Campaign Settings

### 5.1 Budget Validation
```
GIVEN Campaign Settings card is visible
WHEN user enters budget less than $5
THEN budget should clamp to minimum $5
```

**Steps:**
1. Clear budget input
2. Enter "3"
3. Blur input field

**Assertions:**
- [ ] Budget value is 5 (minimum enforced)
- [ ] "Minimum $5/day" hint visible

### 5.2 Estimated Total Calculation
```
GIVEN user sets budget and duration
WHEN values change
THEN estimated total updates correctly
```

**Test Cases:**
| Budget | Duration | Expected Total |
|--------|----------|----------------|
| $50    | 7 days   | $350           |
| $10    | 3 days   | $30            |
| $100   | 30 days  | $3000          |

**Steps:**
1. Set budget to $50
2. Set duration to 7 days
3. Verify estimated total

**Assertions:**
- [ ] Estimated total shows "$350"
- [ ] Calculation text shows "$50/day x 7 days"

### 5.3 Duration Dropdown Options
```
GIVEN Campaign Settings card is visible
THEN duration dropdown has correct options
```

**Assertions:**
- [ ] Option "3 days" available
- [ ] Option "7 days" available
- [ ] Option "14 days" available
- [ ] Option "30 days" available

### 5.4 CTA Dropdown Options
```
GIVEN Campaign Settings card is visible
THEN CTA dropdown has correct options
```

**Assertions:**
- [ ] "Learn More" option available
- [ ] "Shop Now" option available
- [ ] "Sign Up" option available
- [ ] "Download" option available
- [ ] "Contact Us" option available

---

## Scenario 6: Publish Flow

### 6.1 Publish Button Disabled Without Payment
```
GIVEN ad account has no payment method
WHEN Campaign Settings visible
THEN Publish button is disabled with warning
```

**Assertions:**
- [ ] "Publish Campaign" button is disabled
- [ ] Warning text "Add a payment method to publish ads" visible

### 6.2 Publish Button Enabled With Payment
```
GIVEN ad account has valid payment method
WHEN Campaign Settings visible
THEN Publish button is enabled
```

**Assertions:**
- [ ] "Publish Campaign" button is enabled
- [ ] No payment warning visible

### 6.3 Publish Loading State
```
GIVEN user clicks "Publish Campaign"
WHEN publish request in progress
THEN loading state shown
```

**Steps:**
1. Click "Publish Campaign" button
2. Observe button state

**Assertions:**
- [ ] Button shows "Publishing..." text
- [ ] Spinner icon visible
- [ ] Button is disabled during loading

### 6.4 Publish Success Navigation
```
GIVEN publish request succeeds
WHEN response received
THEN SuccessView renders
```

**Assertions:**
- [ ] SuccessView page visible
- [ ] Success icon (green checkmark) visible
- [ ] "Campaign Published!" heading visible

---

## Scenario 7: Success View

### 7.1 Campaign IDs Display
```
GIVEN publish succeeded
WHEN SuccessView renders
THEN campaign IDs are displayed
```

**Assertions:**
- [ ] Campaign ID shown in card
- [ ] Ad Set ID shown in card
- [ ] Ad ID shown in card
- [ ] IDs are in monospace font

### 7.2 Paused Status Warning
```
GIVEN SuccessView renders
THEN paused status warning visible
```

**Assertions:**
- [ ] Yellow warning box visible
- [ ] Text mentions "PAUSED" status
- [ ] Text mentions Meta Ads Manager

### 7.3 Meta Ads Manager Link
```
GIVEN SuccessView renders
WHEN user clicks "Open Meta Ads Manager"
THEN link opens in new tab
```

**Steps:**
1. Click "Open Meta Ads Manager" button
2. Check link behavior

**Assertions:**
- [ ] Link has target="_blank"
- [ ] Link has rel="noopener noreferrer"
- [ ] URL contains "facebook.com/adsmanager"
- [ ] URL contains campaign_id if available

### 7.4 New Campaign Reset
```
GIVEN user is on SuccessView
WHEN user clicks "Create New Campaign"
THEN app resets to landing page
```

**Steps:**
1. Click "Create New Campaign" button
2. Observe navigation

**Assertions:**
- [ ] Landing page renders
- [ ] URL input is empty
- [ ] No previous campaign data shown

---

## Scenario 8: Error Handling

### 8.1 Publish Error Display
```
GIVEN publish request fails
WHEN error response received
THEN error message displayed
```

**Mock:** Force API error response

**Assertions:**
- [ ] Red error box visible
- [ ] Error message text shown
- [ ] Publish button re-enabled
- [ ] User can retry

### 8.2 OAuth Error Display
```
GIVEN OAuth flow fails
WHEN error message received
THEN error shown in connection card
```

**Assertions:**
- [ ] Red error box in connection card
- [ ] Error message visible
- [ ] "Connect with Facebook" button still available

---

## Scenario 9: Ad Preview & Targeting

### 9.1 Selected Ad Preview
```
GIVEN user navigates to PublishView
THEN selected ad preview shown correctly
```

**Assertions:**
- [ ] Ad image visible (or placeholder)
- [ ] Primary text matches selected ad
- [ ] Headline matches selected ad
- [ ] Page name shown (from FB or fallback to domain)

### 9.2 Targeting Summary
```
GIVEN user navigates to PublishView
THEN targeting summary matches campaign data
```

**Assertions:**
- [ ] Age range displayed correctly
- [ ] Locations displayed correctly
- [ ] Interests displayed (max 6 with +N more)

---

## Test Data Cleanup

After test completion:
1. Disconnect Facebook if connected
2. Clear localStorage `fb_session_id`
3. Note any campaigns created for manual cleanup in Ads Manager

---

## Automation Hints

### Selectors
```javascript
const selectors = {
  // Landing
  urlInput: 'input[placeholder*="landing page URL"]',
  generateBtn: 'button:has-text("Generate Ad")',

  // Results
  adCard: '[data-testid="ad-card"]', // Add this data-testid
  nextBtn: 'button:has-text("Next: Publish")',

  // Publish
  backBtn: 'button:has-text("Back to Results")',
  connectFbBtn: 'button:has-text("Connect with Facebook")',
  pageSelect: 'select:near(:text("Facebook Page"))',
  adAccountSelect: 'select:near(:text("Ad Account"))',
  budgetInput: 'input[type="number"]',
  durationSelect: 'select:near(:text("Duration"))',
  ctaSelect: 'select:near(:text("Call to Action"))',
  publishBtn: 'button:has-text("Publish Campaign")',
  estimatedTotal: ':text("Estimated Total") + div',

  // Success
  successIcon: '.text-green-500',
  campaignId: ':text("Campaign ID") + span',
  adsManagerLink: 'a:has-text("Meta Ads Manager")',
  newCampaignBtn: 'button:has-text("Create New Campaign")',
};
```

### API Mocking Points
```javascript
const mockEndpoints = {
  analyze: 'POST /analyze/async',
  jobStatus: 'GET /jobs/:id',
  fbStatus: 'GET /meta/fb-status',
  paymentStatus: 'GET /meta/payment-status',
  publish: 'POST /meta/publish-campaign',
};
```
