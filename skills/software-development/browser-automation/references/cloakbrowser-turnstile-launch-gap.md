# CloakBrowser Turnstile: Hermes vs Direct Python Launch

Discovered June 2026 during GachaSlabz.com automation attempt.

## The Gap

CloakBrowser binary (`/home/ubuntu/.cloakbrowser/chromium-146.0.7680.177.5/chrome`) behaves differently depending on how it's launched:

| Launch Method | Turnstile Behavior | Result |
|---|---|---|
| Hermes `browser_navigate` | Iframe loads, checkbox appears, auto-solves | ✅ Works |
| `cloakbrowser.launch_async()` (Python package) | Iframe exists but body stays empty forever | ❌ Widget never renders |
| `playwright.chromium.launch(executable_path=...)` | Same as cloakbrowser package — empty iframe body | ❌ Widget never renders |

Same binary, same VPS, same site. The difference is in the launch path.

## Diagnostic Steps Taken

1. **Verified Hermes works**: `browser_navigate` → Turnstile iframe loads → checkbox appears → clicked → solved → button enabled
2. **Tested cloakbrowser 0.3.31**: `launch_async(headless=True)` → iframe exists (Python `page.frames` shows it) → but `document.body.innerHTML` always empty → checkbox never appears
3. **Tested playwright direct**: Same binary path → same empty iframe result
4. **Checked flags**: CloakBrowser uses `--fingerprint=SEED --fingerprint-platform=windows` by default. Adding `--disable-blink-features=AutomationControlled` didn't help.
5. **Frame detection nuance**: `window.frames.length` returns 0 (cross-origin invisible to page JS), but Python `page.frames` shows 2 frames. This is normal — the issue is not frame detection but widget rendering.

## Hypothesis

Hermes browser tools likely configure additional context (user data dir, environment variables, CDP flags, or proxy settings) that the Python package's default `launch_async()` doesn't. The Turnstile JS inside the iframe may require specific browser context conditions to initialize.

## Workaround

When Turnstile interaction is required:
- **Use Hermes browser tools** (`browser_navigate`, `browser_click`, `browser_snapshot`) — they work
- **Don't rely on** direct `cloakbrowser.launch_async()` for Turnstile-protected pages unless you replicate Hermes' full launch configuration

## When This Matters

Any automation targeting sites with Cloudflare Turnstile interactive challenges needs the Hermes browser tool path, not direct Python CloakBrowser/Playwright launches. This is especially relevant for:
- Mass account registration flows
- Login automation
- Any flow where "Verify you are human" checkbox must be solved

**Alternative**: Use 2captcha/Anti-Captcha service to solve Turnstile programmatically (~$1-2 per 1000 solves), then call APIs directly with the token. This bypasses the browser entirely. Recommended for 100+ account farming where speed matters.

## Additional Findings

- **agent-browser CLI renders Turnstile, but solve is false-positive.** With
  `AGENT_BROWSER_ARGS` set to `--fingerprint=SEED,--fingerprint-platform=windows`,
  the `agent-browser` CLI (via Python `subprocess`) successfully renders the
  Turnstile checkbox. Clicking it makes the checkbox disappear and the button
  appears enabled. However, **no valid Turnstile token is generated** — the form
  submission fails silently (page stays on `/login`). Hermes browser tools
  (`browser_navigate`/`browser_click`) properly generate the token
  (`input[name="cf-turnstile-response"]` value is populated). The gap is likely
  in CDP-level vs accessibility-tree event dispatch.

- **Console error**: `Failed to load resource: the server responded with a
  status of 401` appears when Python-launched CloakBrowser hits the Turnstile
  iframe. The 401 may be Turnstile rejecting the browser fingerprint.

- **IP independence**: VPS was Singapore (43.159.56.39). Hermes browser tools
  worked on same IP, so geo-blocking is not the cause — it's purely the launch
  method difference.

- **Tested on**: GachaSlabz.com (June 5, 2026), b.ai (June 6, 2026), CloakBrowser v0.3.31, chromium-146.0.7680.177.5, agent-browser CLI via Python subprocess

- **CloakBrowser + Chrome Extensions incompatibility (June 2026).** Loading browser extensions (e.g. MetaMask) into CloakBrowser via `--load-extension` flag: `window.ethereum` appears with `isMetaMask:true` but `chrome.storage.local` LevelDB backend doesn't initialize — no `Local Extension Settings/` directory is created in the profile. CloakBrowser's C++ stealth patches likely interfere with extension storage APIs. Regular Chromium loads extensions correctly but can't bypass Turnstile. For sites requiring BOTH Turnstile bypass AND browser extensions: two requirements are mutually exclusive on headless VPS.
