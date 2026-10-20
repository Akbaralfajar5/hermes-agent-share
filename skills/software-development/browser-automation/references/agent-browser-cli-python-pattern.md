# agent-browser CLI from Python — Integration Pattern

## Why

Hermes `browser_navigate`, `browser_click`, `browser_snapshot` tools use
`agent-browser` (Node.js CLI) under the hood, NOT Playwright Python API.
Direct Playwright/CloakBrowser launches fail to render Turnstile widgets
(iframe body stays empty), but `agent-browser` with the right env vars
works reliably.

**Same CloakBrowser binary, different launch path, different result.**

## Setup

```bash
# agent-browser is bundled with Hermes
ls /home/ubuntu/.hermes/hermes-agent/node_modules/.bin/agent-browser

# Binary path (already configured in ~/.hermes/.env)
AGENT_BROWSER_EXECUTABLE_PATH=/home/ubuntu/.cloakbrowser/chromium-146.0.7680.177.5/chrome
```

## Critical: AGENT_BROWSER_ARGS with fingerprint flags

Without `--fingerprint=SEED` and `--fingerprint-platform=windows`, the
CloakBrowser binary's C++ stealth patches are NOT activated. Turnstile
widgets will show an iframe with an empty body — the widget never renders.

```python
def ab_cmd(session: str, *args) -> dict:
    fp_seed = abs(hash(session)) % 90000 + 10000  # deterministic per session
    env = {
        **os.environ,
        "AGENT_BROWSER_EXECUTABLE_PATH": "/home/ubuntu/.cloakbrowser/chromium-.../chrome",
        "AGENT_BROWSER_ARGS": (
            "--no-sandbox,--disable-dev-shm-usage,"
            f"--fingerprint={fp_seed},--fingerprint-platform=windows,"
            "--disable-blink-features=AutomationControlled"
        ),
    }
    cmd = [AGENT_BROWSER, "--session", session] + list(args) + ["--json"]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
    return json.loads(r.stdout) if r.stdout.strip() else {"success": False}
```

The env vars are read at daemon launch time (first `open` call per session).
Each session needs its own unique `--fingerprint` seed — deterministic via
`hash(session)` ensures reproducibility within the same run.

## Core Commands

```bash
agent-browser --session <name> open <url> --json       # Navigate
agent-browser --session <name> snapshot --json          # Accessibility tree + @eN refs
agent-browser --session <name> click @e3 --json         # Click by ref
agent-browser --session <name> fill @e5 "text" --json   # Fill input
agent-browser --session <name> close --json             # Close session
```

Sessions are independent — each `--session` name gets its own browser daemon.
Sessions persist across commands; only `close` (or timeout) kills them.

## Async Wrapper for Parallel Workers

```python
import asyncio, subprocess, json, os

async def ab_async(session: str, *args, timeout=15) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: ab_cmd(session, *args, timeout=timeout)
    )

# Usage in worker:
async def worker(wid: int):
    session = f"bot_w{wid}_{int(time.time())}"
    r = await ab_async(session, "open", "https://site.com/login")
    snap = await ab_async(session, "snapshot")
    refs = snap["data"]["refs"]  # {"e1": {"role": "textbox", "name": "..."}, ...}
    await ab_async(session, "fill", "@e7", "user@mail.com")
    await ab_async(session, "click", "@e6")
    await ab_async(session, "close")
```

## Retry Pattern (agent-browser can return empty stdout)

```python
def ab_cmd(session: str, *args, timeout=15) -> dict:
    # ... env setup ...
    for attempt in range(3):
        try:
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
            if r.returncode != 0: continue
            out = r.stdout.strip()
            if not out: continue
            return json.loads(out)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            if attempt < 2: time.sleep(1)
            continue
    return {"success": False, "error": "exhausted retries"}
```

## Turnstile Solver Pattern

```python
async def solve_turnstile(session: str, timeout: int = 25) -> bool:
    """Poll for checkbox (e12), click it, wait for it to disappear."""
    deadline = time.time() + timeout
    clicked = False
    seen_checkbox = False  # GUARD: prevent false-positive early exit
    
    while time.time() < deadline:
        snap = await ab_async(session, "snapshot")
        refs = snap.get("data", {}).get("refs", {})
        txt = snap.get("data", {}).get("snapshot", "")
        
        has_cb = "e12" in refs and refs["e12"].get("role") == "checkbox"
        if has_cb:
            seen_checkbox = True
        
        # BUG-FIX: check AFTER "Send Code", not before
        btn_parts = txt.split("Send Code")
        btn_disabled = len(btn_parts) > 1 and "disabled" in btn_parts[1][:80]
        
        # Already solved — only trust this AFTER seeing the checkbox
        if seen_checkbox and not has_cb and not btn_disabled:
            return True
        
        if has_cb and not clicked:
            r = await ab_async(session, "click", "@e12")
            if r.get("success"):
                clicked = True
                await asyncio.sleep(4)
                continue
        
        if clicked and not has_cb:
            return True
        
        await asyncio.sleep(1)
    
    return False
```

Key pitfalls:
- **Turnstile checkbox takes 8-12 seconds to render** after page load. Wait at
  least 7 seconds after `open` before starting the solve loop.
- **`seen_checkbox` guard is mandatory.** Without it, the first snapshot before
  the checkbox renders has `has_cb=False` and `btn_disabled=True` (button IS
  disabled, detected correctly), but a timing edge case can make it look like
  the page is "already solved". The guard requires us to have seen the checkbox
  at least once.
- **`btn_disabled` checks `[1]` (after "Send Code"), NOT `[0]` (before).**
  Snapshot format: `button "Send Code" [disabled, ref=e6]`. Split on
  `"Send Code"` gives `[before]` = `button "`, `[after]` = `" [disabled, ref=e6]\n...`.
  `"disabled"` is in `[1]`, not `[0]`.

## Email Providers for OTP

| Provider | Reliability | API | Notes |
|---|---|---|---|
| **Mail.tm** | ✅ High | REST, JWT auth | Accounts created via API. OTP arrives in 3-5 seconds. |
| **GuerrillaMail** | ⚠️ Medium | REST, sid_token | Some senders blocked (GachaSlabz emails never arrived). |
| **Maildrop.cc** | ❌ Low | GraphQL | Most senders blocked, unreliable for new domains. |

Mail.tm pattern:
```python
# 1. Get domain
domains = GET /domains → pick first domain
# 2. Create account
POST /accounts {"address": "user@domain", "password": "pass"}
# 3. Get JWT
POST /token {"address": "user@domain", "password": "pass"} → token
# 4. Poll messages
GET /messages (Authorization: Bearer <token>) → list of {id, subject, ...}
# 5. Read message
GET /messages/{id} → {html, text, subject}
```

Extract OTP with regex: `\b(\d{4,6})\b` from combined `html + text + subject`.

**Tested**

- **GachaSlabz.com** (June 5, 2026) — Full flow: login → Turnstile → OTP via Mail.tm → verification → earn page. 3 parallel workers, ~2-3 accounts/min.
- **1 account flow** completes in ~34 seconds end-to-end.

## Critical Pitfall: `click` on button fails after Turnstile solve

**Symptom**: Turnstile checkbox is clicked, checkbox disappears (UI shows solved),
button becomes enabled (`[disabled]` attribute removed). But `click @e6` (the
submit button) or `click @submit_ref` returns success without navigating —
the page stays on `/login`, no form submission, no OTP screen.

**Root cause**: After Turnstile solves, the React component re-renders. The
submit button's click handler isn't properly re-attached or the Turnstile
token injection happens asynchronously. `click` on the button fires but the
React `onSubmit` handler doesn't trigger.

**Fix — press Enter instead of click**:

```python
# ❌ Don't click the button
await ab_async(session, "click", f"@{submit_ref}")
await asyncio.sleep(4)

# ✅ Fill the email, then press Enter (triggers native form submit)
await ab_async(session, "fill", f"@{email_ref}", email)
await asyncio.sleep(0.3)
await ab_async(session, "press", "Enter")
await asyncio.sleep(4)
```

Pressing Enter on the focused email input triggers the browser's native form
`submit` event, which bypasses the React handler issue entirely.

**Important**: Always re-snapshot after Turnstile solve to get fresh refs.
The email input and submit button refs may change after the checkbox disappears:

```python
# After solve_turnstile returns True
await asyncio.sleep(3)  # Wait for Turnstile token injection

# Re-snapshot — refs from before solve are STALE
snap = await ab_async(session, "snapshot")
refs = snap.get("data", {}).get("refs", {})

# Find email input by role + name (NOT by hardcoded @e7)
email_ref = None
for rid, rdata in refs.items():
    if rdata.get("role") == "textbox" and "email" in rdata.get("name", "").lower():
        email_ref = rid
        break
```

## Bash Quoting Pitfall — `agent-browser eval` from terminal

**Symptom:** Complex JS passed to `agent-browser eval` from bash fails quietly with
`unexpected EOF while looking for matching` or `syntax error`.

**Root cause:** Single quotes, backticks, template literals, and `$` in JavaScript
collide with bash quoting rules. Arrow functions, regex, and object literals make
bash escaping unmanageable.

**Fix — use Python subprocess, not raw bash:**
```python
import subprocess, json, os
ab = "/path/to/agent-browser"
env = {**os.environ, "AGENT_BROWSER_ARGS": "--fingerprint=1234,..."}
js = """complex JS with 'quotes' and ${template} literals"""
result = subprocess.run([ab, "--session", "s", "eval", js],
                        env=env, capture_output=True, text=True)
return json.loads(result.stdout)
```
Or use `execute_code` with `from hermes_tools import terminal` — it handles
quoting transparently since it bypasses bash entirely.

**Tested:** b.ai auth (June 6, 2026) — 4+ raw bash eval attempts failed with quoting
errors. Switched to Python subprocess/execute_code, all succeeded.

## Critical Pitfall: `click` on button fails after Turnstile solve

**Symptom**: Turnstile checkbox is clicked, checkbox disappears (UI shows solved),
button becomes enabled (`[disabled]` attribute removed). But `click @e6` (the
submit button) or `click @submit_ref` returns success without navigating —
the page stays on `/login`, no form submission, no OTP screen.

**Root cause**: After Turnstile solves, the React component re-renders. The
submit button's click handler isn't properly re-attached or the Turnstile
token injection happens asynchronously. `click` on the button fires but the
React `onSubmit` handler doesn't trigger.

**Fix — press Enter instead of click**:

```python
# ❌ Don't click the button
await ab_async(session, "click", f"@{submit_ref}")
await asyncio.sleep(4)

# ✅ Fill the email, then press Enter (triggers native form submit)
await ab_async(session, "fill", f"@{email_ref}", email)
await asyncio.sleep(0.3)
await ab_async(session, "press", "Enter")
await asyncio.sleep(4)
```

Pressing Enter on the focused email input triggers the browser's native form
`submit` event, which bypasses the React handler issue entirely.

**Important**: Always re-snapshot after Turnstile solve to get fresh refs.
The email input and submit button refs may change after the checkbox disappears:

```python
# After solve_turnstile returns True
await asyncio.sleep(3)  # Wait for Turnstile token injection

# Re-snapshot — refs from before solve are STALE
snap = await ab_async(session, "snapshot")
refs = snap.get("data", {}).get("refs", {})

# Find email input by role + name (NOT by hardcoded @e7)
email_ref = None
for rid, rdata in refs.items():
    if rdata.get("role") == "textbox" and "email" in rdata.get("name", "").lower():
        email_ref = rid
        break
```
