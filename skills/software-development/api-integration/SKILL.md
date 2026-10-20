---
name: api-integration
description: "Production-grade API integration patterns — retry with backoff, circuit breaker, rate limiting, webhook signature verification, Midtrans/Xendit Indonesian payment gateways, WhatsApp Cloud API."
version: 1.0.0
author: Hermes (adapted from SUPERAGENT v3 m6)
license: MIT
metadata:
  hermes:
    tags: [api, rest, webhook, midtrans, xendit, integration, retry, circuit-breaker, rate-limit, payment]
---

# API Integration & Service Bridge

Load when: API, REST, webhook, midtrans, xendit, integrasi, endpoint, SDK, integration, payment gateway.

Integration engineer. Reliable inter-system communication. Retry, rate-limit, idempotency, signature verification built in by default.

---

## JS Bridge Layer (retry + timeout + idempotency)

```javascript
// http.js
async function call(url, {
  method = 'GET',
  body = null,
  headers = {},
  timeout = 30_000,
  retries = 3,
  idempotencyKey = null,
} = {}) {
  const finalHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.API_KEY}`,
    ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    ...headers,
  };

  const opts = { method, headers: finalHeaders };
  if (body) opts.body = typeof body === 'string' ? body : JSON.stringify(body);

  for (let attempt = 1; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), timeout);
    try {
      const r = await fetch(url, { ...opts, signal: controller.signal });
      clearTimeout(t);

      if (r.status >= 500 || r.status === 429) {
        if (attempt < retries) {
          const wait = r.status === 429
            ? Number(r.headers.get('retry-after') || 1) * 1000
            : 2 ** attempt * 1000;
          await new Promise(s => setTimeout(s, wait));
          continue;
        }
      }
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
      const ct = r.headers.get('content-type') || '';
      return ct.includes('application/json') ? r.json() : r.text();
    } catch (e) {
      clearTimeout(t);
      if (attempt === retries) throw e;
      await new Promise(s => setTimeout(s, 2 ** attempt * 1000));
    }
  }
}

module.exports = { call };
```

---

## Python Bridge Layer (tenacity-based retry)

```python
import requests, os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class TransientError(Exception): pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type(TransientError),
    reraise=True,
)
def call(url, method='GET', data=None, headers=None, timeout=30, idempotency_key=None):
    h = {
        'Authorization': f'Bearer {os.getenv("API_KEY")}',
        'Content-Type': 'application/json',
        **(headers or {}),
    }
    if idempotency_key:
        h['Idempotency-Key'] = idempotency_key

    r = requests.request(method, url, json=data, headers=h, timeout=timeout)

    if r.status_code == 429 or r.status_code >= 500:
        raise TransientError(f'{r.status_code}: {r.text[:200]}')
    r.raise_for_status()
    return r.json() if 'application/json' in r.headers.get('content-type', '') else r.text
```

---

## Circuit Breaker

```javascript
class Breaker {
  constructor({ threshold = 5, timeout = 60_000 } = {}) {
    this.failures = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED';  // CLOSED | OPEN | HALF
    this.openedAt = 0;
  }
  async exec(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.openedAt > this.timeout) this.state = 'HALF';
      else throw new Error('Circuit OPEN');
    }
    try {
      const out = await fn();
      this.failures = 0;
      this.state = 'CLOSED';
      return out;
    } catch (e) {
      this.failures++;
      if (this.failures >= this.threshold) {
        this.state = 'OPEN';
        this.openedAt = Date.now();
      }
      throw e;
    }
  }
}

const breaker = new Breaker();
await breaker.exec(() => call('https://flaky.api/x'));
```

---

## Rate Limit Handler (token bucket)

```javascript
class RateLimit {
  constructor({ rps = 10 } = {}) {
    this.rps = rps;
    this.tokens = rps;
    this.last = Date.now();
  }
  async acquire() {
    while (true) {
      const now = Date.now();
      const delta = (now - this.last) / 1000;
      this.tokens = Math.min(this.rps, this.tokens + delta * this.rps);
      this.last = now;
      if (this.tokens >= 1) { this.tokens--; return; }
      await new Promise(r => setTimeout(r, 50));
    }
  }
}

const rl = new RateLimit({ rps: 5 });
for (const item of items) {
  await rl.acquire();
  await fetch(`https://api/items/${item}`);
}
```

---

## Webhook Signature Verification (HMAC)

```javascript
const crypto = require('crypto');

function verifySignature(body, signature, secret) {
  const expected = crypto.createHmac('sha256', secret).update(body).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

// Express handler
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['x-signature'];
  if (!sig || !verifySignature(req.body, sig, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  const data = JSON.parse(req.body);
  res.sendStatus(200);
});
```

---

## Midtrans Snap (Indonesian payment)

```javascript
const midtransClient = require('midtrans-client');
const snap = new midtransClient.Snap({
  isProduction: process.env.NODE_ENV === 'production',
  serverKey: process.env.MIDTRANS_SERVER_KEY,
});

const tx = await snap.createTransaction({
  transaction_details: {
    order_id: `ORD-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
    gross_amount: 100_000,   // IDR
  },
  customer_details: { first_name: 'User', email: 'user@example.com', phone: '+62...' },
  item_details: [{ id: 'SKU1', price: 100_000, quantity: 1, name: 'Premium Access' }],
  callbacks: { finish: 'https://yourdomain.com/thanks' },
});
// tx.token → frontend Snap popup
// tx.redirect_url → direct redirect
```

### Midtrans webhook handler

```javascript
const core = new midtransClient.CoreApi({
  isProduction: false,
  serverKey: process.env.MIDTRANS_SERVER_KEY,
});

app.post('/midtrans/notification', async (req, res) => {
  const status = await core.transaction.notification(req.body);
  const { order_id, transaction_status, fraud_status } = status;

  if ((transaction_status === 'capture' && fraud_status === 'accept') ||
       transaction_status === 'settlement') {
    await markPaid(order_id);
  }
  res.sendStatus(200);
});
```

---

## Xendit (alternative Indonesian PG)

```javascript
const { Invoice } = require('xendit-node/invoice');
const xen = new Invoice({ secretKey: process.env.XENDIT_SECRET });

const inv = await xen.createInvoice({
  data: {
    externalId: `INV-${Date.now()}`,
    amount: 100_000,
    payerEmail: 'user@example.com',
    description: 'Premium Access',
    successRedirectUrl: 'https://yourdomain.com/thanks',
    invoiceDuration: 3600,
  }
});
// inv.invoiceUrl → redirect customer
```

---

## WhatsApp Cloud API

```javascript
async function sendWA(to, message) {
  return call(
    `https://graph.facebook.com/v18.0/${process.env.WA_PHONE_ID}/messages`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.WA_TOKEN}` },
      body: {
        messaging_product: 'whatsapp',
        to,
        type: 'text',
        text: { body: message },
      }
    }
  );
}
```

---

## Python SSL Bypass + Optional Proxy (urllib & requests)

When calling external APIs (Stripe, payment gateways, etc.) from a VPS or behind a proxy that causes cert errors, bypass SSL verification and make proxy optional.

### urllib.request (stdlib)

```python
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
https_handler = urllib.request.HTTPSHandler(context=ctx)

# With optional proxy
handlers = [https_handler]
if proxy:
    handlers.insert(0, urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
opener = urllib.request.build_opener(*handlers)

req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
with opener.open(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())
```

### requests library

```python
import requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

resp = requests.post(url, data=payload, headers=hdrs, verify=False, timeout=30,
                     proxies={"http": proxy, "https": proxy} if proxy else None)
```

### Proxy Optional Pattern

When script accepts proxy via CLI arg or env var but should work without one:

```python
proxy = args.proxy or os.getenv("PROXY_URL") or None
# Then in http_request: pass proxy=proxy (None = direct connection)
```

**Diagnostic:** HTTP status `0` (not a real status code) = **connection failure** (DNS, timeout, cert error, proxy unreachable). Check `resp.get("error")` for the actual exception message.

---

## Constraints

- `.env.example` listing every required var
- Rate limiting on outbound calls when target has known limits
- Idempotency key on any POST that creates resources
- Webhook receivers: ALWAYS verify signature
- Never log full request body if it contains secrets/PII
- Timeout on every external call (no infinite waits)
- Retry only on transient errors (429, 5xx, network) — not 4xx
