# wagmi Network Spy — Confirming postMessage-Only Wallet Detection

When reverse-engineering a wagmi/RainbowKit-based dApp, inject network spies BEFORE clicking any wallet button to confirm whether wagmi makes HTTP calls or uses pure `postMessage`.

## Why

wagmi v2+ connectors use `window.postMessage` to detect browser extension wallets (MetaMask, Trust Wallet, etc.). A mock `window.ethereum` object won't work because it can't respond to postMessage. But how do you confirm this is the case without guessing?

Inject network spies, click the wallet button, and check if ANY API calls were made:

- **Zero calls** → wagmi is using pure postMessage (need real extension)
- **Calls to `/api/auth/signin` or similar** → SIWE challenge is fetched via HTTP (can intercept + sign programmatically)

## Spy Injection (via agent-browser eval or browser console)

```javascript
// Spy 1: Fetch interceptor
window.__fetchLog = [];
const origFetch = window.fetch;
window.fetch = function(...args) {
    const url = (typeof args[0] === "string" ? args[0] : args[0]?.url) || "";
    const opts = args[1] || {};
    const entry = {type: "fetch", url, method: opts.method || "GET", time: Date.now()};
    if (opts.body) {
        try { entry.body = typeof opts.body === "string" ? opts.body.substring(0, 200) : JSON.stringify(opts.body).substring(0, 200); } catch(e) {}
    }
    window.__fetchLog.push(entry);
    return origFetch.apply(this, args).then(r => {
        const ct = r.headers.get("content-type") || "";
        if (ct.includes("json")) {
            return r.clone().json().then(j => { entry.resp = JSON.stringify(j).substring(0, 300); return r; }).catch(() => r);
        }
        return r;
    });
};

// Spy 2: XHR interceptor
const origOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    this.__url = url; this.__method = method; this.__time = Date.now();
    return origOpen.apply(this, arguments);
};
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(body) {
    if (this.__url) {
        window.__fetchLog.push({type: "xhr", url: this.__url, method: this.__method, time: this.__time,
            body: typeof body === "string" ? body.substring(0, 200) : ""});
    }
    return origSend.apply(this, arguments);
};

// Spy 3: Performance API observer (catches resources loaded before injectors)
try {
    const obs = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
            if (entry.name.includes("ainft.com") || entry.name.includes("b.ai")) {
                window.__allRequests = window.__allRequests || [];
                window.__allRequests.push({name: entry.name, type: entry.initiatorType});
            }
        }
    });
    obs.observe({type: "resource", buffered: true});
} catch(e) {}
```

## After clicking wallet button

```javascript
// Filter for auth-related calls
JSON.stringify(window.__fetchLog.filter(e =>
    e.url.includes("auth") || e.url.includes("sign") || e.url.includes("message") ||
    e.url.includes("callback") || e.url.includes("nonce") || e.url.includes("csrf")
))
```

## b.ai Result (June 2026)

Clicked MetaMask button → **zero fetch/XHR calls** to `ainft.com`. Confirmed: wagmi uses pure `postMessage` protocol. No SIWE challenge endpoint is reachable via HTTP until after the extension handshake succeeds.

## General Pattern

This technique applies to ANY wagmi/RainbowKit dApp. Inject spies before interacting with wallet buttons to understand the auth architecture without reading minified JS bundles.
