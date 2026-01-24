# Facebook OAuth HTTPS Setup

Facebook requires HTTPS for OAuth redirect URIs. This guide covers local development setup.

## Quick Setup

```bash
# 1. Generate SSL certificates
./scripts/generate-certs.sh

# 2. Add env vars to .env
api_url=https://localhost:8000
frontend_url=https://localhost:5173

# 3. Start servers
./start_app.sh
```

## Meta Dashboard Configuration

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Select your app
3. Navigate to: **Facebook Login → Settings**
4. Add to **Valid OAuth Redirect URIs**:
   ```
   https://localhost:8000/auth/facebook/callback
   ```
5. Save changes

## SSL Certificates

Certificates are stored in `certs/` folder (gitignored):
- `certs/cert.pem` - SSL certificate
- `certs/key.pem` - Private key

To regenerate:
```bash
rm -rf certs/
./scripts/generate-certs.sh
```

## Configuration Files

### Backend (`start_app.sh`)
```bash
uvicorn app.main:app --reload \
  --ssl-keyfile=./certs/key.pem \
  --ssl-certfile=./certs/cert.pem
```

### Frontend (`frontend/vite.config.ts`)
```typescript
server: {
  https: {
    key: fs.readFileSync('../certs/key.pem'),
    cert: fs.readFileSync('../certs/cert.pem'),
  },
}
```

### Environment (`.env`)
```bash
api_url=https://localhost:8000
frontend_url=https://localhost:5173
```

## URLs

- Frontend: https://localhost:5173
- Backend: https://localhost:8000
- OAuth Test: https://localhost:5173/#/test/fb-auth

## Browser Certificate Warning

Self-signed certs trigger browser warnings - normal for local dev.

**Accept the warning:**
- Chrome: "Advanced" → "Proceed to localhost"
- Safari: "Show Details" → "visit this website"
- Firefox: "Advanced" → "Accept the Risk"

**Or trust permanently (macOS):**
```bash
# Add to Keychain and trust
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/cert.pem
```

## Troubleshooting

### "redirect URI not white-listed"
Add `https://localhost:8000/auth/facebook/callback` to Meta Dashboard → Facebook Login → Settings → Valid OAuth Redirect URIs.

### "Insecure login blocked"
Both frontend AND backend must use HTTPS. Check that:
- Frontend runs on `https://localhost:5173`
- Backend runs on `https://localhost:8000`

### Page doesn't update after OAuth
Check `frontend_url` in `.env` matches exactly: `https://localhost:5173`
(postMessage origin must match)

### "Feature Unavailable" for other accounts
The Facebook account must be added as Tester/Developer in Meta Dashboard → Roles.

## Multi-Account Support

To allow other Facebook accounts to test:
1. Go to Meta Dashboard → Roles → Roles
2. Add the account as "Tester" or "Developer"
3. Have them accept the invitation
4. They can now use OAuth

## Security Notes

- Self-signed certs are **for development only**
- Never commit `certs/` folder (gitignored)
- Certificate expires in 365 days
- Regenerate with `./scripts/generate-certs.sh`
