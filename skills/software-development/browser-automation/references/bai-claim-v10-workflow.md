# b.ai Credit Claim Workflow (June 2026)

## Architecture: 2-Phase Cookie + Manual Claim

### Phase 1: Login (can be headless or headed)
- Login all accounts via Google OAuth popup
- Save cookies to `cookies/{email}.json` (Playwright `context.cookies()`)
- Fresh browser per account (reusing context = ~50% success rate)

### Phase 2: Claim (must be non-headless, residential IP)
- Load cookies into fresh browser context (`context.add_cookies(data['cookies'])`)
- Navigate to chat.b.ai
- Verify session via `/api/auth/session`
- Check claim status: `GET /trpc/lambda/user.hasClaimedSignupBonus?batch=1`
- Click "Claim Free Credits" button → modal opens
- Wait Turnstile solve (button.disabled becomes false)
- Click "Claim" button
- Verify: re-check hasClaimedSignupBonus

### Status Check API (works from any IP, no Turnstile)
```python
headers = {'Cookie': cookie_str, 'User-Agent': '...'}
r = requests.get(
    'https://chat.b.ai/trpc/lambda/user.hasClaimedSignupBonus?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D',
    headers=headers, timeout=10
)
# Response: [{"result":{"data":{"json":{"hasClaimed":true/false}}}}]
```

## Key Learnings

### Multi-worker pitfall: `bai_claims.txt` as "done" tracker
- Script reads output file to skip "done" accounts
- If status like `logged_in` is written, script thinks account is done even if unclaimed
- Fix: only mark `claimed` or `already_claimed` as done statuses

### ThreadPoolExecutor vs threading.Thread
- ThreadPoolExecutor: use when browser closes after work (login phase)
- threading.Thread: use when browser stays open (manual claim phase)
- With ThreadPoolExecutor, if browser stays open → worker never returns → deadlock

### Cookie expiry
- b.ai session cookies (AuthJS) expire after ~24h
- If claim fails with "cookies_expired", need re-login
- Delete cookie file to force re-login on next run

### Turnstile rendering failures in parallel
- 15 browsers from same IP: some won't render Turnstile
- Fix: reduce to 5-8 parallel, or user refreshes (F5) affected windows
- `channel="chrome"` (real Chrome) renders better than Playwright Chromium
- `context.add_init_script` to remove webdriver flag helps

### Solver tokens DON'T work for b.ai
- sctg.xyz can solve the sitekey (`0x4AAAAAADKhTSXIozuHjOoF`)
- But server validates: token IP must match claim request IP
- Result: "Invalid token: Token verification failed or expired"
- Only real browser solve from same residential IP works
