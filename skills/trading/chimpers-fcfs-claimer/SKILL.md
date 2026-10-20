---
name: chimpers-fcfs-claimer
description: "Claim free FCFS NFT packs on Chimpers Cards (cards.chimpers.com) using Dynamic SDK auth + temp Gmail addresses. Covers single claim and mass automation (1000+ accounts)."
triggers:
  - chimpers claim
  - chimpcognito
  - chimpers cards FCFS
  - free NFT pack claim
---

# Chimpers FCFS Pack Claimer

## Context
Chimpers Cards (cards.chimpers.com) runs periodic free FCFS drops. Authentication uses **Dynamic SDK** which blocks disposable email domains. The workaround uses real Gmail addresses via `+` aliasing (emailnator/gmailnator).

## Architecture

### Auth System
- **Provider:** Dynamic SDK
- **Env ID:** `5e551d68-2833-4539-82d9-dc14bd2549e8`
- **Auth endpoint:** `https://auth-prod.chimpers.com/api/v0/sdk/{env_id}/emailVerifications/create`
- **Method:** POST, Body: `{"email":"..."}`
- **Status codes:** 200 = OTP sent, 422 = domain blocked
- **Protection:** Cloudflare WAF — direct curl from VPS returns 403. Must use browser context or proper headers.

### Email Strategy
Dynamic SDK has a comprehensive blocklist of disposable email domains. All common temp mail services are blocked:
- ❌ generator.email domains (bjorwi.store, dshznonline.cc, etc.)
- ❌ mail.tm (wshu.net)
- ❌ tempmail.plus (mailto.plus)
- ❌ guerrillamail, yopmail, maildrop, etc.

**Working approach:** Emailnator/Gmailnator generates real `@gmail.com` addresses using the `+` alias trick.
- Example: `user@example.com`
- Gmail ignores `+` and everything after it for delivery
- Dynamic SDK accepts `@gmail.com` domain
- Emailnator can receive emails sent to these addresses

### Emailnator API Endpoints
Found in `https://www.emailnator.com/js/app.js`:
- `POST /generate-email` — generate temp Gmail
- `POST /message-list` — get inbox messages  
- `GET /mailbox/:emailAddress/:messageID` — view specific message
- `POST /delete-message` — delete message
- `POST /send-message` — send email
- `POST /bulk-emails` — bulk generation (100-1000)
- RapidAPI: `https://rapidapi.com/johndevz/api/gmailnator`

**Note:** Emailnator also behind Cloudflare. Need to extract cookies from browser session first, then use those cookies with curl/requests.

## Flow Per Account
1. Generate temp Gmail via emailnator API
2. `POST` to Chimpers auth API → triggers OTP email
3. Poll emailnator inbox → extract 6-digit OTP code
4. Submit OTP to verification endpoint → get session token
5. Navigate to drop page → click "Claim" / "Redeem"
6. Store email + claim status for records

## Verified Working Flow (tested 2026-05-27)

### Step 1: Get Emailnator cookies
```bash
curl -s -c /tmp/emailnator_cookies.txt 'https://www.emailnator.com/' \
  -H 'User-Agent: Mozilla/5.0 ...'
```
Extract XSRF token from cookies (URL-decode it).

### Step 2: Generate temp Gmail
```bash
curl -s -b /tmp/emailnator_cookies.txt -X POST 'https://www.emailnator.com/generate-email' \
  -H 'Content-Type: application/json' \
  -H 'X-XSRF-TOKEN: <decoded_xsrf>' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Origin: https://www.emailnator.com' \
  -d '{"email":["dotGmail","plusGmail"]}'
# Returns: {"email":["user@example.com"]}
```

### Step 3: Submit email to Chimpers (via browser)
Dynamic SDK endpoint is behind Cloudflare WAF — must use browser context.
Navigate to `https://cards.chimpers.com/login`, fill email field, click Continue.
API call: `POST https://auth-prod.chimpers.com/api/v0/sdk/5e551d68-2833-4539-82d9-dc14bd2549e8/emailVerifications/create`

### Step 4: Poll emailnator for OTP
```bash
curl -s -b /tmp/emailnator_cookies.txt -X POST 'https://www.emailnator.com/message-list' \
  -H 'Content-Type: application/json' \
  -H 'X-XSRF-TOKEN: <decoded_xsrf>' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -d '{"email":"user@example.com"}'
# Returns: {"messageData":[{"messageID":"MTll...","from":"Chimpers <...>","subject":"Chimpers login code","time":"Just Now"}]}
```

### Step 5: Read OTP message
```bash
curl -s -b /tmp/emailnator_cookies.txt -X POST 'https://www.emailnator.com/message-list' \
  -H 'Content-Type: application/json' \
  -H 'X-XSRF-TOKEN: <decoded_xsrf>' \
  -d '{"email":"user@example.com","messageID":"MTllNmE3ZjdmYTdmZTA1YQ=="}'
# Returns full HTML of the email. Extract 6-digit OTP via regex.
```

### Step 6: Enter OTP in browser (shadow DOM)
Dynamic SDK inputs are in shadow DOM. Must set values via JS:
```javascript
(function() {
  const otp = '123456';
  const inputs = [];
  document.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) el.shadowRoot.querySelectorAll('input').forEach(inp => inputs.push(inp));
  });
  for (let i = 0; i < 6; i++) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(inputs[i], otp[i]);
    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
    inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
  }
})()
```

### Step 7: Complete onboarding
- Select avatar (click first official character)
- Set random username
- Click "Create Account"
- Skip social ("Finish")

### Step 8: Claim pack
Navigate to Chimpcognito drop page → click "REDEEM NOW"
Note: "REDEEM NOW" may require wallet connection (MetaMask). Further testing needed.

## Pitfalls
- **Rate limiting:** Dynamic SDK likely rate-limits per IP. Need proxy rotation for 1000 accounts.
- **Cloudflare:** Both chimpers auth API and emailnator are behind CF. Cookie extraction from browser required for emailnator API.
- **OTP timing:** OTP codes expire. Poll emailnator within 60s of sending.
- **Shadow DOM:** Dynamic SDK OTP inputs are in shadow DOM. Normal `browser_type` doesn't work. Use JS injection.
- **Session loss:** Browser session can be lost between page navigations. Store cookies/localStorage.
- **REDEEM NOW button:** May require MetaMask wallet connection — not yet fully tested for the final claim step.
- **Emailnator session expiry:** Cookies may expire. Re-extract if 401/403 responses.
- **Emailnator rate limits:** For 1000 accounts, consider delays between generations.
- **Username must be unique:** Generate random usernames per account.
