# 2Captcha Turnstile Solving Reference

## When It Works
- **Standalone Turnstile widgets** embedded in a page (visible `data-sitekey` attribute)
- The page itself loads normally (no "Just a moment..." gate)
- Sitekey is in the HTML: `<div class="cf-turnstile" data-sitekey="0x4AAAA...">`

## When It Does NOT Work
- **Cloudflare Managed Challenges** (WAF-level protection)
- Page shows "Just a moment..." / "Performing security verification"
- Source contains `cType: 'managed'` in `window._cf_chl_opt`
- No visible sitekey in page HTML (it's internal to CF's challenge platform)
- 2Captcha accepts the task but returns ERROR_CAPTCHA_UNSOLVABLE after 3 minutes

## How to Distinguish
```bash
# Check if it's a managed challenge
curl -s 'https://target.site/' | grep -oP "cType:\s*'[^']+'"
# If output: cType: 'managed' → CANNOT solve with 2Captcha
# If no output and page loads normally with a Turnstile widget → CAN solve
```

## API Usage (when it works)

### Step 1: Create Task
```javascript
const resp = await axios.post('https://api.2captcha.com/createTask', {
    clientKey: 'YOUR_API_KEY',
    task: {
        type: 'TurnstileTaskProxyless',
        websiteURL: 'https://example.com/page',
        websiteKey: '0x4AAAA...',  // from data-sitekey
    }
});
const taskId = resp.data.taskId;
```

### Step 2: Poll Result (every 5s, max 120s)
```javascript
const result = await axios.post('https://api.2captcha.com/getTaskResult', {
    clientKey: 'YOUR_API_KEY',
    taskId: taskId,
});
// result.data.solution.token → the Turnstile response token
```

### Step 3: Use Token
```javascript
// Submit to the target form with the token
await axios.post('https://example.com/api/submit', {
    address: '0x...',
    'cf-turnstile-response': token,
});
```

## Old API Format (alternative)
```bash
# Submit
curl "https://2captcha.com/in.php?key=KEY&method=turnstile&sitekey=SITEKEY&pageurl=URL&json=1"
# Returns: {"status":1,"request":"TASK_ID"}

# Poll
curl "https://2captcha.com/res.php?key=KEY&action=get&id=TASK_ID&json=1"
# Returns: {"status":1,"request":"TOKEN"}
```

## Cost
- ~$0.00145 per solve
- Typical solve time: 10-30 seconds for standalone widgets

## Finding the Sitekey
```bash
# Method 1: Check page HTML
curl -s 'https://target.site/' | grep -oP 'data-sitekey="([^"]+)"'

# Method 2: Check JS bundles (for SPAs)
curl -s 'https://target.site/_next/static/chunks/page-xxx.js' | grep -oP 'sitekey["\s:]+["'\''](0x[^"'\'']+)'

# Method 3: Intercept in browser console
const origRender = window.turnstile.render;
window.turnstile.render = (el, opts) => { console.log('SITEKEY:', opts.sitekey); return origRender(el, opts); };
```
