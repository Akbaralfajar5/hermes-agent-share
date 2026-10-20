# CloakBrowser Setup & Verification

## Installation (Python)
```bash
pip install cloakbrowser
# Optional: timezone/locale auto-detection from proxy IP
pip install cloakbrowser[geoip]
```

First run auto-downloads stealth Chromium binary (~200MB, cached at `~/.cloakbrowser/chromium-<version>/`). Older docs/blog posts say `~/.cache/cloakbrowser/` — that path is wrong as of cloakbrowser ≥0.3.x. Confirm with `cloakbrowser info`.

## Installation (npm/npx — standalone binary)
```bash
npx cloakbrowser
# Or install globally:
npm install -g cloakbrowser
```

When installed via npm, the binary goes to the same `.cloakbrowser` directory:
- **Linux:** `~/.cloakbrowser/chromium-<version>/chrome`
- **Windows:** `C:\Users\<user>\.cloakbrowser\chromium-<version>\chrome.exe`

## Installation (Node.js)
```bash
# With Playwright
npm install cloakbrowser playwright-core
# With Puppeteer
npm install cloakbrowser puppeteer-core
```

## CLI Reference

The `cloakbrowser` command (installed at `~/.local/bin/cloakbrowser` when pip-installed as user) manages the stealth Chromium binary:

```bash
cloakbrowser install       # download chromium binary (first time)
cloakbrowser info          # show version, binary path, platform, install status
cloakbrowser update        # check for + download newer build
cloakbrowser clear-cache   # remove all cached binaries
```

Sample `info` output:
```
Version:   146.0.7680.177.3
Platform:  linux-x64
Binary:    /home/<user>/.cloakbrowser/chromium-146.0.7680.177.3/chrome
Installed: True
Cache:     /home/<user>/.cloakbrowser/chromium-146.0.7680.177.3
```

Use this BEFORE running an automation task to confirm the binary is present — saves a 200MB surprise download mid-run.

## Using with Playwright via executable_path

When CloakBrowser is installed (either via pip or npm), you can use it directly with Playwright:

```python
import os
import glob

# Auto-detect latest CloakBrowser version
cloak_dir = os.path.expanduser("~/.cloakbrowser")
versions = glob.glob(os.path.join(cloak_dir, "chromium-*"))
if versions:
    latest = max(versions)  # Pick highest version
    exe = os.path.join(latest, "chrome.exe" if os.name == "nt" else "chrome")
else:
    raise FileNotFoundError("CloakBrowser not found — run 'cloakbrowser install'")

browser = await p.chromium.launch(
    executable_path=exe,
    headless=False,
    proxy={'server': 'http://proxy:port', 'username': 'user', 'password': 'pass'},
    args=[...]
)

**Key advantage over bundled Chromium:** CloakBrowser handles proxy auth (Basic, Digest) natively — no `ERR_PROXY_AUTH_UNSUPPORTED` or relay proxy needed. This is the single biggest reason to use it for authenticated proxy automation.

## Pitfalls

1. **Don't set both `executable_path` and `channel='chrome'`** — These two parameters are mutually exclusive in Playwright. Using both causes a launch error.
2. **Binary is ~200-300MB** — Multiple versions accumulate. Clean old ones manually.
3. **Version directories change on update** — CloakBrowser auto-updates the version folder. Use `glob` to auto-detect the latest version.
4. **Windows paths** — Use raw strings `r"C:\Users\..."` or double backslashes.
5. **Not headless-friendly** — CloakBrowser is designed for headed mode; headless loses anti-detection benefits.
```

**Key advantage:** CloakBrowser handles proxy auth natively — no `ERR_PROXY_AUTH_UNSUPPORTED`. Unlike Playwright's bundled Chromium, CloakBrowser can authenticate HTTP proxies without a local relay.

### Finding the binary manually
```bash
# Linux
ls ~/.cloakbrowser/chromium-*/

# Windows (CMD)
dir C:\Users\<user>\.cloakbrowser\chromium-*
```

Look for `chrome.exe` (Windows) or `chrome` (Linux) inside the versioned directory.

### Pitfalls for executable_path approach
- `channel='chrome'` and `executable_path` are mutually exclusive — set one, not both
- Binary is ~200-300MB; old versions accumulate under `.cloakbrowser/`
- Version directory changes on update — use glob auto-detection or re-check periodically
- On Windows, use raw strings (`r"C:\..."`) or double backslashes for paths

## Verification Test
```python
from cloakbrowser import launch
import time

browser = launch(headless=True)
page = browser.new_page()
page.goto("https://bot.sannysoft.com")
time.sleep(3)

# Check detection results
js = """() => {
    const rows = document.querySelectorAll("table tr");
    const data = [];
    rows.forEach(r => {
        const cells = r.querySelectorAll("td");
        if (cells.length >= 2) {
            data.push(cells[0].textContent.trim() + ": " + cells[1].textContent.trim());
        }
    });
    return data.slice(0, 20);
}"""
results = page.evaluate(js)
for r in results:
    print(f"  {r}")
browser.close()
```

## Expected Pass Results
- WebDriver: missing (passed)
- Chrome: present (passed)
- WebGL Vendor/Renderer: spoofed GPU (e.g., NVIDIA RTX 4080)
- All PHANTOM_* checks: ok
- All HEADCHR_* checks: ok
- Plugins Length: 5 (normal browser count)

## Use Cases for This Environment
- **Crypto data scraping**: Bypass Cloudflare on CoinGlass, exchange sites, news aggregators
- **Market monitoring**: Scrape sites that block automated requests
- **Research**: Access protected content without detection
- **Trading automation**: Interact with web-based trading interfaces

## Hermes Browser Stack Integration

Hermes has **three** browser backends, and CloakBrowser IS wired into the built-in browser tools via env var:

| Backend | How it activates | Hermes tool compatible? |
|---|---|---|
| **agent-browser** (Chrome) | `engine: auto` (default) or `engine: chrome` | ✅ Yes |
| **camoufox** (Firefox) | Set `CAMOFOX_URL` in `~/.hermes/.env` | ✅ Yes |
| **CloakBrowser** (stealth Chromium) | Set `AGENT_BROWSER_EXECUTABLE_PATH` in `~/.hermes/.env` | ✅ Yes — works as agent-browser's Chromium |

### Making CloakBrowser the Default (Recommended)

**Step 1:** Install and verify CloakBrowser binary:
```bash
pip install cloakbrowser
cloakbrowser info    # confirm Installed: True, note the Binary path
```

**Step 2:** Set env var in `~/.hermes/.env`:
```bash
AGENT_BROWSER_EXECUTABLE_PATH=/home/<user>/.cloakbrowser/chromium-<version>/chrome
```
Use the exact path from `cloakbrowser info` → `Binary:` field.

**Step 3:** Verify — all `browser_navigate`, `browser_click`, `browser_snapshot` calls now use CloakBrowser:
```
browser_navigate("chrome://version")
```
Check: `Executable Path` should show the CloakBrowser binary path. `User Agent` should show ungoogled-chromium.

**How it works:** agent-browser (the Rust CLI that Hermes browser tools invoke) accepts `--executable-path` or `AGENT_BROWSER_EXECUTABLE_PATH` env var to override which Chromium binary it launches. Setting this to CloakBrowser's binary means all Hermes browser tool calls go through the stealth Chromium with fingerprint patches — no code changes needed in Hermes itself.

## Pitfalls
- Binary is ~200MB — first run takes time to download
- On headless servers, ensure display libs are available (Playwright deps)
- `humanize=True` adds realistic delays — slower but passes behavioral detection
- Auto-update checks happen in background — may cause brief startup delay
- Repo: https://github.com/CloakHQ/CloakBrowser
- **npm install path:** The binary is at `~/.cloakbrowser/chromium-*/chrome.exe`, NOT in the npm project's `node_modules/`
- **Version dir changes on update:** Scripts using `executable_path` should auto-detect via glob or listdir
