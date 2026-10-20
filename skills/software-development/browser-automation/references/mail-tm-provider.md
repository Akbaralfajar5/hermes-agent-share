# Mail.tm — Disposable Email Provider for Automation

Preferred temp email provider after GuerrillaMail failed to receive GachaSlabz OTPs
(tested June 2026). Mail.tm delivered OTP within 3 seconds consistently.

## API Flow

```
GET  /domains                  → pick a domain (e.g. wshu.net)
POST /accounts {address, password} → create inbox (no verification needed)
POST /token    {address, password} → get JWT bearer token
GET  /messages (Bearer token)  → list messages (poll for OTP)
GET  /messages/{id} (Bearer)   → get full message (html + text)
```

## Python Implementation

```python
import httpx
import random, string, re

MAILTM_BASE = "https://api.mail.tm"

async def create_email(client: httpx.AsyncClient):
    """Returns (email, password, token). Retry 3x for rate limits."""
    for attempt in range(3):
        try:
            r = await client.get(f"{MAILTM_BASE}/domains")
            domain = random.choice(r.json()["hydra:member"])["domain"]
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            email = f"gacha_{rand}@{domain}"
            password = "Test1234!"
            
            r = await client.post(f"{MAILTM_BASE}/accounts",
                json={"address": email, "password": password})
            if r.status_code >= 500:
                await asyncio.sleep(2); continue
            
            r = await client.post(f"{MAILTM_BASE}/token",
                json={"address": email, "password": password})
            token = r.json().get("token", "")
            if token:
                return email, password, token
        except Exception:
            await asyncio.sleep(2)
    return "", "", ""

async def poll_otp(client, token, timeout=60):
    """Poll inbox for OTP code. Returns 4-6 digit string or None."""
    deadline = time.time() + timeout
    seen = set()
    while time.time() < deadline:
        r = await client.get(f"{MAILTM_BASE}/messages",
            headers={"Authorization": f"Bearer {token}"})
        for msg in r.json().get("hydra:member", []):
            if msg["id"] in seen: continue
            seen.add(msg["id"])
            r2 = await client.get(f"{MAILTM_BASE}/messages/{msg['id']}",
                headers={"Authorization": f"Bearer {token}"})
            data = r2.json()
            html = data.get("html", [""])[0] if isinstance(data.get("html"), list) else data.get("html", "")
            text = data.get("text", "")
            combined = re.sub(r'<[^>]+>', ' ', str(html) + ' ' + str(text))
            codes = re.findall(r'\b(\d{4,6})\b', combined)
            for c in codes:
                if len(c) >= 4:
                    return c
        await asyncio.sleep(2)
    return None
```

## Rate Limiting

Mail.tm rate-limits account creation. Symptoms:
- `500` from `/accounts` endpoint
- `KeyError: 'token'` when `/token` returns without a token

Always retry 3x with 2-second delays. Randomize the domain choice (`random.choice(domains)`)
to spread load across available domains.

## Node.js Alternative

```javascript
const axios = require('axios');
const MAILTM = 'https://api.mail.tm';

async function createEmail() {
  const { data: d } = await axios.get(`${MAILTM}/domains`);
  const domain = d['hydra:member'][0].domain;
  const rand = Math.random().toString(36).substring(2, 12);
  const email = `gacha_${rand}@${domain}`;
  await axios.post(`${MAILTM}/accounts`, { address: email, password: 'Test1234!' });
  const { data: t } = await axios.post(`${MAILTM}/token`, { address: email, password: 'Test1234!' });
  return { email, token: t.token };
}
```

## Comparison

| Provider | GachaSlabz Delivery | API Quality | Best For |
|----------|-------------------|-------------|----------|
| Mail.tm | ✅ ~3 seconds | Clean REST + JWT | Production bots |
| Maildrop.cc | ❌ Never arrived | GraphQL, sporadic | Quick tests |
| GuerrillaMail | ❌ Never arrived | REST, rate-limited | Legacy/backup |
