# X Premium Gift Automation (centang_biru.py)

Cookie-based X Premium gifting via X's internal GraphQL API + Stripe customer_balance exploit. Sends Premium as a gift to target users for €0 (customer_balance zero-cost checkout).

## Script Setup

Script dir: `/tmp/xpremium/xpremium/`
Files: `centang_biru.py` (main), `.env` (proxy + api key), `cookies.json` (X auth cookies)

### Dependencies
```bash
pip install python-dotenv
```

### .env format
```
GERMANY_PROXY=http://user:pass@gw.dataimpulse.com:823
OPENCAGE_API_KEY=your_opencage_key
```

### cookies.json format
```json
{
  "cookies": [
    {"name": "auth_token", "value": "...", "domain": ".x.com"},
    {"name": "ct0", "value": "...", "domain": ".x.com", "httpOnly": false},
    {"name": "twid", "value": "...", "domain": ".x.com"},
    {"name": "kdt", "value": "...", "domain": ".x.com"},
    {"name": "guest_id", "value": "...", "domain": ".x.com"}
  ]
}
```

**Critical:** `ct0` must have `httpOnly: false` (needed for X-Csrf-Token header). `auth_token` MUST have `httpOnly: true` to match real browser export format.

## Usage

```bash
python3 centang_biru.py --target USERNAME --duration 3|6|12
```

### Duration → Product ID mapping
- 3 months → `prod_QH6h8qsTyMQrnI` (€219.00)
- 6 months → `prod_TJXL297k753Zvb`
- 12 months → `prod_TJcPqt9ypBzEFQ` (€206.00)

## Architecture

The flow has 9 steps split into two phases:

### Phase 1: Gift Check (`run_gift_check`)
1. **Get target user ID** — X GraphQL `UserByScreenName` query
2. **Check gift eligibility** — `PremiumGiftingQuery` (sender-side, 3 products returned)
3. **Get product price** — `useSubscriptionProductDetailsByRestIdQuery` (Stripe product details)
4. **Generate German address** — OpenCage Geocoder → random real street + city

### Phase 2: Gift Execution (`run_gift_flow`)
5. **Initiate gift** — `useOneTimePurchaseGiftMutation` → returns Stripe checkout URL
6. **Extract Stripe session ID** — parse URL
7. **Stripe checkout** — init session, set tax region to DE
8. **Create payment method** — `customer_balance` with German billing address
9. **Confirm checkout** — Stripe confirm with customer_balance (€0 checkout)

## Proxy Rules

| Step | Endpoint | Proxy Required |
|------|----------|---------------|
| 1-4 | X GraphQL API | ✅ Yes (Germany proxy) |
| 5 | X Gift Mutation | ✅ Yes (Germany proxy) |
| 6 | Local (parse URL) | ❌ No |
| 7-9 | Stripe API | ❌ No (direct connection) |

**IMPORTANT:** Stripe calls MUST use direct connection (no proxy). X API calls MUST use Germany proxy. The proxy makes X think the sender is in Germany (€0 VAT/tax exploit).

## Common Errors & Fixes

### "Suspended"
Target account is banned/suspended by X. Skip immediately — cannot gift suspended accounts.

### "Recipient user is not eligible to receive gift"
Target found but X rejects the gift. Causes:
- Already has Premium active (can't double-gift)
- Account too new / low activity (0 posts, 0 followers, joined <6 months ago)
- Region restriction (account from unsupported country)
- Account flagged as suspicious

### "HTTP Error 429: Too Many Requests"
Rate limited by X API. After ~140-150 successful requests, X starts throttling.
**Fix:** Add delay between requests (3-5s) or wait 15-30 min before retrying.

### "UserByScreenName failed"
General API error — could be network (proxy dead) or auth (cookies expired).

## Known Behaviors

1. **Cannot gift same account twice in a row** — once Premium is active, X blocks another gift until expiry
2. **Real accounts work, bot accounts don't** — @rivernity_eth (real-looking account) succeeded repeatedly. Bot accounts (0 followers, 0 posts, animal/noun+number naming) almost always fail with "Not eligible" or are already suspended
3. **3 months vs 12 months** — 3-month gifts seem to work more reliably than 12-month. 12-month gifts often fail even for accounts where 3-month succeeded
4. **Cookies expire** — auth_token lasts ~1 year, but can be invalidated on logout/password change/security flag. If all requests start failing with auth errors, need fresh cookies

## Batch Processing

For bulk gifting, use a wrapper script that loops through targets:
```python
for target in targets:
    proc = subprocess.run(
        ["python3", SCRIPT, "--target", target, "--duration", "12"],
        capture_output=True, text=True, timeout=120
    )
    # Parse output for SUCCESS / Suspended / not eligible / 429
    time.sleep(0.5)  # Avoid rate limiting
```

The 429 rate limit typically hits after ~140 sequential requests. For large batches (>200 targets), add 3-5s delays or split into waves.
