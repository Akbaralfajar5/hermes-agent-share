# Email Domain Whitelisting for Mass Registration

## Problem
Many SaaS services enable email domain whitelisting to prevent temp mail abuse. When this is active, Mail.tm / Guerrilla Mail / temp-mail.org domains get rejected at the API level.

## Detection
```python
import urllib.request, json

def check_email_domain(email):
    """Test if an email passes the service's whitelist"""
    url = f"https://service.com/api/verification?email={email}&turnstile="
    req = urllib.request.Request(url, method='GET')
    req.add_header('User-Agent', 'Mozilla/5.0')
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        return data.get('success', False)
    except Exception as e:
        return str(e)

# Test whitelisted domains
domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'protonmail.com', 'hotmail.com']
for d in domains:
    result = check_email_domain(f"test_verify_123@{d}")
    print(f"{d}: {result}")
```

## Known Whitelisted Domains (UniModel.ai, similar Chinese-backend services)
- `gmail.com` ✅
- `outlook.com` ✅
- `yahoo.com` — sometimes, often 429 rate limited
- `protonmail.com` — sometimes, often 429 rate limited
- `mail.com` — sometimes
- `zoho.com` — sometimes

## Blocked Temp Mail Domains
- `wshu.net` (Mail.tm) ❌
- `web-library.net` (Mail.tm) ❌
- `guerrillamail.com` ❌
- `tempmail.com` ❌
- `throwaway.email` ❌

## Plus-Alias Rejection
Some backends reject `+` in email addresses:
- `user@example.com` → "invalid parameter" / "无效的参数"
- This is common in Chinese-backend services (UniModel.ai, similar)
- Always test before building a pipeline around Gmail+ aliases

## Fallback Strategies

### 1. Gmail IMAP Pool
- Create N Gmail accounts
- Access via IMAP to poll for verification codes
- Each account can receive unlimited verification emails
- Use `himalaya` skill for IMAP access

### 2. Outlook/Hotmail Pool
- Similar to Gmail but with Outlook
- May have stricter rate limits

### 3. Custom Domain Catch-All
- Register domain, set up catch-all email
- Only works if domain passes whitelist check
- Use `id-domain-registration` skill for .id domains

### 4. Proxy Rotation
- When IP rate-limited (429), rotate proxies
- Residential proxies preferred for anti-bot bypass
- Space requests 10-15s apart per IP

## Rate Limiting Patterns
- **IP-based:** 3-5 requests → 429 for 5-15 minutes
- **Domain-based:** Some services rate-limit per email domain
- **Time-based:** Resets after 15-60 minutes
- **Burst detection:** Rapid-fire requests trigger longer bans

## Mail.tm API Quick Reference
```
GET  https://api.mail.tm/domains          → current available domains
POST https://api.mail.tm/accounts         → create {address, password}
POST https://api.mail.tm/token            → get JWT {address, password}
GET  https://api.mail.tm/messages         → list messages (Bearer token)
GET  https://api.mail.tm/messages/{id}    → full message body
```
