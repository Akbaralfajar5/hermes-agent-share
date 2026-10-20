# In-Browser Proxy Toggle Pattern (June 2026)

**User preference:** Proxy toggle MUST be inside the browser window itself — floating button, not terminal argument. User explicitly said "langsung di browser nya fiturnya, bukan lewat terminal" (the feature in the browser directly, not via terminal).

## Pattern

Floating button at bottom-right of each browser window. Click toggles proxy on/off → browser restarts automatically with new proxy setting → replay login flow.

### JavaScript Injection (runs in browser)

```javascript
PROXY_TOGGLE_JS = """
(() => {
    if (document.getElementById('__proxy_toggle__')) return;
    const panel = document.createElement('div');
    panel.id = '__proxy_toggle__';
    panel.innerHTML = `
        <div id="__proxy_status__" style="
            position:fixed; bottom:10px; right:10px; z-index:9999999;
            background:rgba(0,0,0,0.85); color:#fff; border-radius:8px;
            padding:6px 10px; font:bold 11px monospace; cursor:pointer;
            border:1px solid #555; user-select:none; display:flex; gap:6px; align-items:center;
        ">
            <span id="__proxy_dot__" style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;"></span>
            <span id="__proxy_label__">PROXY: ON</span>
            <span style="color:#888;font-size:9px;">| klik matikan</span>
        </div>
    `;
    document.body.appendChild(panel);
    
    let proxyOn = true;
    let restartRequested = false;
    
    document.getElementById('__proxy_status__').addEventListener('click', () => {
        proxyOn = !proxyOn;
        // Update visual state immediately
        const dot = document.getElementById('__proxy_dot__');
        const label = document.getElementById('__proxy_label__');
        if (proxyOn) {
            dot.style.background = '#22c55e';
            label.textContent = 'PROXY: ON';
        } else {
            dot.style.background = '#ef4444';
            label.textContent = 'PROXY: OFF';
        }
        restartRequested = true;
        window.__proxy_restart__ = !proxyOn;
    });
    
    window.__proxy_restart_requested__ = () => {
        if (restartRequested) {
            restartRequested = false;
            return window.__proxy_restart__;
        }
        return null;
    };
})();
"""
```

### Python Polling & Restart (in worker loop)

```python
async def run_one_worker(phone, worker_id, use_proxy, results):
    """Worker dengan proxy toggle di dalem browser."""
    while True:
        # ... launch browser with current proxy setting ...
        
        async with AsyncCamoufox(**cf_opts) as browser:
            page = await browser.new_page()
            
            # Inject toggle button
            await inject_proxy_toggle(page)
            
            # Update toggle label for initial proxy state
            if not use_proxy:
                await safe_eval(page, """() => {
                    document.getElementById('__proxy_dot__').style.background = '#ef4444';
                    document.getElementById('__proxy_label__').textContent = 'PROXY: OFF';
                }""")
            
            # Run deposit/login flow
            res = await deposit_flow(page, worker_id, phone)
            results[worker_id] = res
            
            # Poll toggle every 1 second
            while True:
                toggle = await poll_proxy_toggle(page)
                if toggle is not None:
                    use_proxy = toggle
                    break  # Restart browser with new proxy setting
                await asyncio.sleep(1)
```

## Key Design Decisions

| Decision | Why |
|----------|-----|
| `while True` restart loop | Cannot change proxy at runtime — must close browser and relaunch |
| Polling via `page.evaluate` | No WebSocket needed; simple JS-exposed flag |
| Visual state change on click | Immediate feedback — dot turns red/green before restart |
| Re-run full flow after restart | Session is lost on browser close; must replay login |
| `MutationObserver` for toggle | Optional — re-inject if SPA wipes the DOM element |

## Pitfalls

- **Proxy CANNOT be changed at runtime** — Playwright/Camoufox/CloakBrowser all set proxy at browser-launch level
- **Session lost on restart** — cookies/session cleared when browser closes
- **Replay must be idempotent** — worker function must be callable multiple times
- **Toggle injection timing** — inject AFTER page load, not before (DOM must exist)

## Why Not Terminal Arguments

User explicitly rejected `--proxy`/`--no-proxy` CLI args. They want UI inside the browser:
- Visual indicator (green = ON, red = OFF)
- One-click toggle
- No need to close all browsers and rerun script
