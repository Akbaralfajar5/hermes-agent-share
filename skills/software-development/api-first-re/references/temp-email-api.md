# Temp Email API for Mass Registration

## Mail.tm API

### Domains
```
GET https://api.mail.tm/domains
→ Returns available domains (e.g., "web-library.net")
```

### Create Account
```
POST https://api.mail.tm/accounts
Content-Type: application/json
{"address": "user@web-library.net", "password": "Pass123!"}
→ Returns {id, address}
```

### Get JWT Token
```
POST https://api.mail.tm/token
Content-Type: application/json
{"address": "user@web-library.net", "password": "Pass123!"}
→ Returns {token, id}
```

### List Messages
```
GET https://api.mail.tm/messages
Authorization: Bearer {token}
→ Returns {"hydra:member": [{id, subject, from, text}]}
```

### Get Message Body
```
GET https://api.mail.tm/messages/{id}
Authorization: Bearer {token}
→ Returns {text, html, subject}
```

## Rate Limits
- Mail.tm: 429 after rapid account creation. Space out by 10-15 seconds.
- Per-service verification endpoints: varies (some 429 after 3-5 requests)

## Email Domain Whitelisting

**CRITICAL DISCOVERY:** Many services whitelist email domains. Mail.tm domains (web-library.net, etc.) are often BLOCKED.

### Tested on UniModel.ai:
- ✅ `gmail.com` — accepted
- ✅ `outlook.com` — accepted
- ❌ `web-library.net` (Mail.tm) — blocked ("email domain name whitelist")
- ❌ `yahoo.com` — rate limited (429)
- ❌ `protonmail.com` — rate limited (429)
- ❌ `+` aliases (user@example.com) — "invalid parameter" (Chinese backend)

### Strategy for whitelisted domains:
1. **Gmail accounts pool** — multiple real Gmail accounts, access via IMAP
2. **Outlook accounts pool** — similar approach
3. **Catch-all domain** — own domain with catch-all, if domain is whitelisted
4. **Proxy rotation** — to bypass IP-based rate limits (429)

## Python Usage (no curl needed)
```python
import urllib.request, json

# Create temp email
data = json.dumps({"address": "user@web-library.net", "password": "Pass123!"}).encode()
req = urllib.request.Request('https://api.mail.tm/accounts', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())

# Get token
data2 = json.dumps({"address": "user@web-library.net", "password": "Pass123!"}).encode()
req2 = urllib.request.Request('https://api.mail.tm/token', data=data2, headers={'Content-Type': 'application/json'})
resp2 = urllib.request.urlopen(req2)
token = json.loads(resp2.read())['token']
```

## Pitfalls
1. **Domain whitelist** — Always test if target service accepts Mail.tm domains before building automation
2. **Rate limits** — Both Mail.tm (account creation) and target service (verification sending) have limits
3. **+ aliases** — Some services reject Gmail+ aliases as "invalid parameter"
4. **Verification code extraction** — Regex for 4-6 digit codes in email body. Check subject line too.
5. **curl not available** — On some VPS, curl is not installed. Use Python urllib or Node.js fetch instead.
