# b.ai (chat.b.ai) API Reverse Engineering — June 2026

## Architecture
- Frontend: Next.js (App Router) + Ant Design v5 + tRPC
- Backend: `chat.ainft.com` (tRPC lambda)
- Auth: NextAuth.js v5 (authjs) + Google Identity Services (GIS)
- Captcha: Cloudflare Turnstile (sitekey `0x4AAAAAADKhTSXIozuHjOoF`)

## Auth Flow (Google OAuth via GIS)
1. `/api/auth/csrf` → GET, returns `{csrfToken: "..."}`
2. User clicks "Continue with Google" → GIS popup opens
3. GIS uses `postMessage` (NOT redirect) to send auth code back to parent
4. Parent calls `/api/auth/callback/google-gis` with code + CSRF
5. Server returns `__Secure-authjs.session-token` cookie

### Google OAuth Details
- Client ID: `244408834658-7gbafoorvctrdn95n8e2s44un3hpo9cn.apps.googleusercontent.com`
- Provider: `google-gis` (NextAuth custom provider)
- Scope: `openid email profile`
- Response type: `code` (authorization code flow)
- Redirect: `postmessage` (GIS popup mode, NOT redirect URI)

### GIS Popup Limitation (Headless)
Google Identity Services popup uses `postMessage` to relay the auth code.
In headless Chromium:
- Popup opens to Google login → fills email/password OK
- After password, gets stuck at `accounts.google.com.sg/accounts/SetSID`
- Never fires postMessage back to parent
- Session cookie never gets set

**Root cause:** Third-party cookie blocking in headless mode prevents
the cross-domain cookie dance that GIS requires to complete.

**Workaround:** Use CloakBrowser (non-headless or with stealth flags)
which passes the full cookie flow. Fresh browser per account = 94% success.

## Claim Endpoint
```
POST https://chat.b.ai/trpc/lambda/user.claimSignupBonus?batch=1
Content-Type: application/json
Cookie: __Secure-authjs.session-token=...

{
  "0": {
    "json": {
      "encryptedToken": "<AES encrypted string>",
      "turnstileToken": "<Turnstile solution token>",
      "type": "oauth:google"
    }
  }
}
```

### encryptedToken Generation (CRACKED)
Found in webpack chunk `25014.742365e7a3957c67.js`:
- Module 795082 exports function `b`:
```javascript
function o(e, t) {
  let r = `${e}|${t}`;
  return CryptoJS.AES.encrypt(r, "1wT1r7z8bZxDHVmZKAs6VFYSXOxmyh0lLByiw5TmF0=").toString();
}
```
- Module 770677 exports function `uh`:
```javascript
g = o => `${o} welcome gift-claim`
```
- Usage: `encryptedToken = ti.b(tn.uh(a.name), Date.now())`

**Formula:**
```
plaintext = "${user_display_name} welcome gift-claim|${timestamp_ms}"
key = "1wT1r7z8bZxDHVmZKAs6VFYSXOxmyh0lLByiw5TmF0="
encryptedToken = CryptoJS.AES.encrypt(plaintext, key).toString()
```

**Python replication (CryptoJS format = OpenSSL compatible):**
```python
import base64, hashlib, os, time
from Crypto.Cipher import AES

def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    dtot, d = b'', b''
    while len(dtot) < key_len + iv_len:
        d = hashlib.md5(d + password + salt).digest()
        dtot += d
    return dtot[:key_len], dtot[key_len:key_len + iv_len]

def generate_encrypted_token(username):
    AES_KEY = "1wT1r7z8bZxDHVmZKAs6VFYSXOxmyh0lLByiw5TmF0="
    timestamp = int(time.time() * 1000)
    plaintext = f"{username} welcome gift-claim|{timestamp}"
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(AES_KEY.encode(), salt)
    data = plaintext.encode()
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(b"Salted__" + salt + encrypted).decode()
```

### What `a.name` is
- `a = (0, v.P)()` — a hook (likely `useUser()` or `useSession()`)
- `a.name` = user's display name from the session
- For GSuite accounts without profile setup, this could be:
  - Email prefix (e.g., "gdjxcfe")
  - Full name if set in Google Workspace admin
  - Email address itself
- **UNRESOLVED:** Exact value of `a.name` for test accounts unknown.
  Server returned "Token verification failed or expired" — likely wrong name value.
  Need to login successfully and inspect `/api/auth/session` response to find exact name.

## Other Useful Endpoints
- `GET /api/auth/session` — returns user session (name, email, image, etc.)
- `GET /api/auth/csrf` — CSRF token for auth operations
- `GET /api/auth/providers` — list auth providers (google-gis, wallet-connector)
- `GET /trpc/lambda/user.getUserState?batch=1` — user state (requires session)
- `GET /trpc/lambda/user.hasClaimedSignupBonus?batch=1` — check claim status

## Turnstile Solver (sctg.xyz)
```python
# Task creation
POST https://sctg.xyz/createTask
{
  "clientKey": "<API_KEY>",
  "task": {
    "type": "TurnstileTask",
    "websiteURL": "https://chat.b.ai/chat",
    "websiteKey": "0x4AAAAAADKhTSXIozuHjOoF"
  }
}

# Result polling
POST https://sctg.xyz/getTaskResult
{"clientKey": "<API_KEY>", "taskId": "<task_id>"}
# Returns: {"solution": {"token": "0.xxx..."}} — ~15-45 seconds
```

## Remaining Blockers
1. **Login:** GIS popup fails in headless → must use CloakBrowser or non-headless
2. **Username for encryptedToken:** Need to confirm what `a.name` resolves to
   for these GSuite accounts (check `/api/auth/session` after successful login)
3. **Token expiry:** encryptedToken uses `Date.now()` — if server validates
   timestamp freshness, claim must happen within seconds of token generation

## Script Locations
- `~/bai-bot/bai_claimer_v3.py` — hybrid script (browser login + API claim)
- `~/bai-bot/bai_mass.py` — original CloakBrowser mass script (94% success)
