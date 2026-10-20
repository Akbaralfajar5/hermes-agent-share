# Turnstile Timing Pitfalls

Collection of Turnstile automation timing bugs discovered during GachaSlabz.com
bot development (June 2026). These apply regardless of whether you use Hermes
browser tools, Playwright, or agent-browser CLI.

## 1. Checkbox Renders 8-12 Seconds After Page Load

**Symptom:** Snapshot at 3-5s shows `Iframe` present but no checkbox. At 8-12s,
checkbox appears as `[checked=false, ref=e12]`.

**Fix:** Always wait at least 7 seconds after `goto` before starting Turnstile
polling. The iframe loads first, then the Turnstile JS executes and renders
the widget.

```python
await page.goto(login_url)
await asyncio.sleep(7)  # Minimum — 10s safer
```

## 2. `seen_checkbox` Guard Prevents False-Positive Early Exit

**Symptom:** `solve_turnstile` returns `True` on the first snapshot, before the
checkbox even renders. The flow proceeds to fill email and submit, but the form
doesn't navigate because Turnstile was never solved.

**Root cause:** The first snapshot shows `has_cb=False` and `btn_disabled=True`.
A timing edge can cause `not has_cb and not btn_disabled` to evaluate `True`
if the disabled-detection logic has a bug (see pitfall #3).

**Fix:** Track whether the checkbox was ever seen. Only return "already solved"
after the checkbox has been observed at least once.

```python
seen_checkbox = False

while time.time() < deadline:
    has_cb = "e12" in refs and refs["e12"].get("role") == "checkbox"
    if has_cb:
        seen_checkbox = True
    
    if seen_checkbox and not has_cb and not btn_disabled:
        return True  # Legitimately solved
```

Without this guard, the function returns `True` on the very first poll when
the widget hasn't loaded yet. **Bug cost:** 10+ wasted accounts in one session.

## 3. Button Disabled Detection: Check AFTER "Send Code", Not Before

**Symptom:** `btn_disabled` always reports `False` even when button is disabled.

**Root cause:** Snapshot format is:
```
- button "Send Code" [disabled, ref=e6]
```

Splitting on `"Send Code"`:
- `[0]` = `- button "` (never contains `"disabled"`)
- `[1]` = `" [disabled, ref=e6]\n...` (contains `"disabled"` when disabled)

**❌ Wrong:**
```python
btn_disabled = "disabled" in txt.split("Send Code")[0][-80:]
```

**✅ Correct:**
```python
parts = txt.split("Send Code")
btn_disabled = len(parts) > 1 and "disabled" in parts[1][:80]
```

**Bug cost:** 10 accounts wasted across multiple debug cycles.

## 4. Post-Click Wait: 4-5 Seconds Minimum

After clicking the Turnstile checkbox, wait at least 4 seconds before checking
if it disappeared. Turnstile validates the click server-side and this takes
3-5 seconds.

```python
await click("@e12")
await asyncio.sleep(4)  # NOT 1-2 seconds
```

Going too fast means the checkbox is still there on the next snapshot and
the code might retry the click (wasting time) or assume failure.

## 5. `press Enter` NOT `click` After Turnstile Solve

**Symptom:** After Turnstile solves, clicking the submit button returns
`{"success": true, "data": {"clicked": "@e6"}}` but the page stays on `/login`.
No navigation, no error, no network request.

**Root cause:** After Turnstile's DOM manipulation (removing the checkbox,
injecting the token), the React submit button's click handler may not be
re-attached. The `click` event fires on the DOM element but React doesn't
respond.

**Fix:** After Turnstile solve, re-snapshot to get fresh refs, fill the email
field, then **press Enter** (triggers native form `submit`, bypassing React).

```python
# After Turnstile solved:
snap = await snapshot()  # Fresh refs
email_ref = find_textbox_by_name(snap, "email")
await fill(f"@{email_ref}", email)
await press("Enter")  # NOT click on button
```

**Why this works:** Native form submission doesn't go through React's event
system. The browser's built-in form behavior picks up the Turnstile token
from the hidden input and includes it in the POST.

## 6. Re-Snapshot After Turnstile Solve — Refs Are Stale

**Symptom:** `fill("@e7", email)` returns `{"error": "Unknown ref: e7"}` after
Turnstile solve.

**Root cause:** The checkbox disappearing changes the DOM. The old snapshot's
`@e7` ref no longer maps to the email input (or maps to the wrong element).

**Fix:** Always take a fresh snapshot after Turnstile solve. Find elements by
role + name pattern, not by hardcoded ref numbers.

```python
snap = await snapshot()
for rid, rdata in snap["refs"].items():
    if rdata["role"] == "textbox" and "email" in rdata["name"].lower():
        email_ref = rid
        break
```

## Full Turnstile Solver Pseudocode

```python
async def solve_turnstile(session, timeout=25):
    deadline = time.time() + timeout
    clicked = False
    seen_cb = False
    
    while time.time() < deadline:
        snap = await snapshot(session)
        refs = snap["refs"]
        txt = snap["snapshot"]
        
        has_cb = "e12" in refs and refs["e12"]["role"] == "checkbox"
        if has_cb: seen_cb = True
        
        parts = txt.split("Send Code")
        btn_dis = len(parts) > 1 and "disabled" in parts[1][:80]
        
        # Only trust "already solved" after seeing the checkbox
        if seen_cb and not has_cb and not btn_dis:
            return True
        
        if has_cb and not clicked:
            await click("@e12")
            clicked = True
            await asyncio.sleep(4)
            continue
        
        if clicked and not has_cb:
            return True
        
        await asyncio.sleep(1)
    
    return False
```
