# Facebook OAuth Debug Log

## Issue Summary
After completing Facebook OAuth in popup, the main page (launchad.io) doesn't update to show signed-in state. User has to navigate away and back to see connected status.

## Environment
- **Frontend**: Vercel (`launchad.io`)
- **Backend**: Railway (`idea2ad-production.up.railway.app`)
- **Browser**: Arc (Chromium-based)

---

## Attempt 1: Fix `get_fb_session()` Missing Fields
**Date**: 2026-01-10
**Commit**: `7ff1f25`

### Problem Identified
`get_fb_session()` function wasn't returning `adAccounts` and `selectedAdAccountId` fields.

### Changes Made
```python
# Before
return {
    "access_token": session.access_token,
    "user_id": session.fb_user_id,
    "user_name": session.fb_user_name,
    "pages": session.pages
}

# After
return {
    "access_token": session.access_token,
    "user_id": session.fb_user_id,
    "user_name": session.fb_user_name,
    "pages": session.pages,
    "adAccounts": session.adAccounts,
    "selectedAdAccountId": session.selectedAdAccountId
}
```

### Result
**Did not fix the issue.** The ad account data was now returned, but the core OAuth state update problem persisted.

### Learning
This was a secondary bug. The primary issue was that the OAuth callback wasn't communicating with the parent window at all.

---

## Attempt 2: Fix `FRONTEND_URL` Environment Variable
**Date**: 2026-01-10
**Commit**: `fe6981f`

### Problem Identified
Suspected that `FRONTEND_URL` wasn't set on Railway, causing `postMessage` to target wrong origin (`localhost:5173` instead of `launchad.io`).

### Changes Made
Added production fallback in `app/config.py`:
```python
# Set production URL defaults if not explicitly configured
if self.frontend_url == "http://localhost:5173":
    object.__setattr__(self, 'frontend_url', "https://launchad.io")
```

### Result
**Did not fix the issue.** Checked Railway env vars - `FRONTEND_URL=https://launchad.io` was already set.

### Learning
The environment variable was already correct. The issue was elsewhere.

---

## Attempt 3: Add Comprehensive Console Logging
**Date**: 2026-01-10
**Commit**: `651981a`

### Problem Identified
Needed visibility into what was happening during OAuth flow.

### Changes Made

**Backend (callback HTML):**
```javascript
console.log('[OAuth Callback] Starting postMessage');
console.log('[OAuth Callback] Target origin:', '{frontend_url}');
console.log('[OAuth Callback] window.opener:', window.opener);
if (window.opener) {
    window.opener.postMessage({...}, '{frontend_url}');
    console.log('[OAuth Callback] postMessage sent successfully');
} else {
    console.error('[OAuth Callback] window.opener is NULL!');
}
```

**Frontend (message listener):**
```javascript
console.log('[OAuth] Message received from:', event.origin)
console.log('[OAuth] Expected origin (API_URL):', API_URL)
console.log('[OAuth] Origin match:', event.origin === API_URL)
```

### Result
**Revealed critical insight:**
- Popup logs showed: `window.opener` exists, `postMessage sent successfully`
- Parent window logs showed: **NO message received at all**

### Learning
The `postMessage` was being sent from the popup, but the parent window never received it. This pointed to a cross-origin issue.

---

## Attempt 4: Fix Race Condition - Register Listener Before Popup
**Date**: 2026-01-10
**Commit**: `651981a` (same commit)

### Problem Identified
Message listener was being registered AFTER popup opened - potential race condition.

### Changes Made
```javascript
// Before: Open popup, then add listener
const popup = window.open(...)
window.addEventListener('message', handleMessage)

// After: Add listener first, then open popup
window.addEventListener('message', handleMessage)
const popup = window.open(...)
```

### Result
**Did not fix the issue.** Message still not received.

### Learning
Race condition wasn't the root cause. The message was fundamentally not being delivered.

---

## Attempt 5: Verify Vercel Deployment
**Date**: 2026-01-10

### Problem Identified
Frontend changes weren't appearing in production. Checked Vercel deployments - last deploy was 3 days ago!

### Changes Made
Manually triggered Vercel deployment:
```bash
cd frontend && vercel --prod --yes
```

### Result
**Partial fix** - new console logs now appeared in production, confirming code was deployed.

### Learning
Vercel wasn't auto-deploying from GitHub. Need to either set up auto-deploy or manually deploy after changes.

---

## Attempt 6: Replace postMessage with Polling
**Date**: 2026-01-10
**Commit**: `c2a49f2`

### Problem Identified
`postMessage` from Railway domain to Vercel domain was being blocked/lost by browser.

### Changes Made
Removed `postMessage` listener entirely. Instead, poll `/meta/fb-status` after popup closes:

```javascript
const pollTimer = setInterval(async () => {
  if (popup?.closed) {
    clearInterval(pollTimer)
    const response = await fetch(`${API_URL}/meta/fb-status`, {
      credentials: 'include'
    })
    // ... update state from response
  }
}, 500)
```

### Result
**Did not fix the issue.** Console showed:
- `[OAuth] Popup closed, checking session...`
- But then nothing - the fetch wasn't completing or was failing silently.

### Learning
The issue wasn't with `postMessage` specifically - it was with cross-origin communication in general.

---

## Attempt 7: Investigate Cookie Behavior
**Date**: 2026-01-10

### Problem Identified
Checked Network tab for `fb-status` request:
- Request succeeded (200 OK)
- Response: `{"connected":false}` (19 bytes)
- Cookie `fb_session` existed in browser (Application → Cookies)
- But cookie was **NOT sent** with the request!

Key header: `sec-fetch-storage-access: none`

### Root Cause Identified
**Third-party cookies are blocked by modern browsers.**

The cookie was set by Railway domain, but the request was coming from Vercel domain (launchad.io). Even with `SameSite=None` and `Secure=True`, cross-site cookies are being phased out by browsers.

### Learning
Cross-site cookies no longer work reliably. Need alternative authentication method.

---

## Attempt 8: Use Header-Based Token Authentication (PENDING)
**Date**: 2026-01-10
**Commit**: `b5f5b96`

### Problem Identified
Cross-site cookies blocked. Need to pass session token without relying on cookies.

### Solution Design
1. Backend callback redirects to frontend URL with token in query param
2. Frontend extracts token from URL, stores in `localStorage`
3. Frontend sends token as `X-FB-Session` header with API requests
4. Backend checks header first, falls back to cookie

### Changes Made

**Backend (`app/routers/facebook.py`):**

Callback now redirects with token:
```python
redirect_url = f"{frontend_url}/launch?fb_session={session_id}"
response = HTMLResponse(f"""
    <script>
        if (window.opener) {{
            window.opener.location.href = '{redirect_url}';
            window.close();
        }} else {{
            window.location.href = '{redirect_url}';
        }}
    </script>
""")
```

Session lookup checks header first:
```python
async def get_fb_session(request: Request):
    # Try header first (for cross-origin requests)
    session_id = request.headers.get("X-FB-Session")
    # Fall back to cookie
    if not session_id:
        session_id = request.cookies.get("fb_session")
```

**Frontend (`frontend/src/CampaignLaunchPage.jsx`):**

Helper for authenticated API calls:
```javascript
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('fb_session')
  const headers = { ...options.headers }
  if (token) {
    headers['X-FB-Session'] = token
  }
  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include'
  })
}
```

Extract token from URL on page load:
```javascript
useEffect(() => {
  const params = new URLSearchParams(window.location.search)
  const sessionToken = params.get('fb_session')
  if (sessionToken) {
    localStorage.setItem('fb_session', sessionToken)
    // Clean up URL
    params.delete('fb_session')
    window.history.replaceState({}, '', newUrl)
    checkFacebookStatus()
  }
}, [])
```

### Result
**PENDING** - Not yet tested

### Expected Behavior
1. User clicks "Connect with Facebook"
2. Popup opens, OAuth completes
3. Popup redirects parent to `launchad.io/launch?fb_session=TOKEN`
4. Frontend extracts token, stores in localStorage
5. Frontend calls `/meta/fb-status` with `X-FB-Session` header
6. Backend finds session, returns `{connected: true, ...}`
7. UI updates to show connected state

---

## Summary of Learnings

| Issue | Root Cause | Status |
|-------|------------|--------|
| Ad accounts missing in response | `get_fb_session()` didn't return all fields | Fixed |
| postMessage not received | Cross-origin blocked by browser | Identified |
| Polling fb-status fails | Cross-site cookies blocked | Identified |
| Third-party cookies blocked | Modern browser security | Root cause found |

## Key Takeaways

1. **Cross-site cookies are dead** - Don't rely on cookies for cross-origin auth flows
2. **postMessage is unreliable** - Browser extensions (Arc) and security policies can block it
3. **Vercel doesn't auto-deploy** - Need to manually deploy or configure GitHub integration
4. **Console logging is essential** - Without detailed logs, debugging cross-origin issues is nearly impossible
5. **Header-based auth is more reliable** - `localStorage` + custom headers bypass cookie restrictions

## Files Modified

- `app/routers/facebook.py` - Session lookup, OAuth callback
- `app/config.py` - Production URL fallback
- `frontend/src/CampaignLaunchPage.jsx` - OAuth handling, API calls

## Next Steps (After Testing)

1. Test header-based auth flow
2. If working, remove debug console.log statements
3. Add disconnect functionality to clear localStorage
4. Consider adding token refresh mechanism
