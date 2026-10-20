# Solana Wallet Injection for DApp Automation

Inject a mock Phantom/Solflare wallet provider into headless browsers to interact with Solana DApps without a real browser extension.

## Use Cases
- Automating DApp interactions (betting, trading, gaming, DeFi)
- Browser-based NFT minting
- Mass DApp operations from headless browsers
- Any Solana DApp requiring `window.solana` (Phantom) or `window.phantom.solana`

## Prerequisites
- Solana private key (base58, 64 bytes)
- Browser with JavaScript execution (Hermes browser tools, Playwright, Puppeteer)

## Step 1: Load Solana web3.js into the page

The DApp needs `solanaWeb3.Keypair` for transaction signing. Load the UMD bundle:

```javascript
// In browser_console or page.evaluate
const script = document.createElement('script');
script.src = 'https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js';
document.head.appendChild(script);
// Wait for onload before proceeding
```

## Step 2: Decode private key + create Keypair

```javascript
// Base58 decoder (no external deps needed in browser)
const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const base58Decode = (str) => {
  let num = BigInt(0);
  for (let i = 0; i < str.length; i++) {
    const idx = ALPHABET.indexOf(str[i]);
    if (idx === -1) throw new Error('Invalid base58 character');
    num = num * BigInt(58) + BigInt(idx);
  }
  let hex = num.toString(16);
  if (hex.length % 2) hex = '0' + hex;
  const bytes = [];
  for (let i = 0; i < hex.length; i += 2) {
    bytes.push(parseInt(hex.substr(i, 2), 16));
  }
  // Leading zeros for leading '1's
  let leadingZeros = 0;
  for (let i = 0; i < str.length; i++) { if (str[i] === '1') leadingZeros++; else break; }
  return new Uint8Array([...new Array(leadingZeros).fill(0), ...bytes]);
};

const privKeyBytes = base58Decode('YOUR_BASE58_PRIVATE_KEY_HERE');
const keypair = solanaWeb3.Keypair.fromSecretKey(privKeyBytes);
console.log('Wallet:', keypair.publicKey.toBase58());
```

## Step 3: Inject Phantom mock provider

```javascript
// Store keypair globally
window._walletKeypair = keypair; // from Step 2

// Base58 encoder (needed for some DApps)
const base58Encode = (bytes) => {
  let num = BigInt(0);
  for (const b of bytes) num = num * BigInt(256) + BigInt(b);
  let str = '';
  while (num > 0n) { str = ALPHABET[Number(num % 58n)] + str; num /= 58n; }
  for (const b of bytes) { if (b === 0) str = '1' + str; else break; }
  return str;
};

// Create mock provider
const phantomProvider = {
  isPhantom: true,
  isConnected: false,
  publicKey: null,
  _listeners: {},

  on(event, fn) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(fn);
  },
  off(event, fn) {
    if (this._listeners[event]) {
      this._listeners[event] = this._listeners[event].filter(f => f !== fn);
    }
  },
  emit(event, ...args) {
    (this._listeners[event] || []).forEach(fn => fn(...args));
  },

  async connect() {
    this.isConnected = true;
    this.publicKey = window._walletKeypair.publicKey;
    this.emit('connect', this.publicKey);
    return { publicKey: this.publicKey };
  },

  async disconnect() {
    this.isConnected = false;
    this.publicKey = null;
    this.emit('disconnect');
  },

  async signTransaction(tx) {
    // PartialSign with our keypair (preserves existing signatures)
    tx.partialSign(window._walletKeypair);
    return tx;
  },

  async signAllTransactions(txs) {
    for (const tx of txs) {
      tx.partialSign(window._walletKeypair);
    }
    return txs;
  },

  async signMessage(msg) {
    // NOTE: Full ed25519 sign requires nacl. Most DApps only check
    // the returned publicKey, not the signature itself.
    // For DApps that verify signatures, load tweetnacl:
    // const nacl = await import('https://cdn.jsdelivr.net/npm/tweetnacl/+esm');
    // const signature = nacl.sign.detached(msg, window._walletKeypair.secretKey);
    return {
      signature: new Uint8Array(64), // placeholder — see note above
      publicKey: window._walletKeypair.publicKey.toBytes()
    };
  }
};

// Inject into BOTH locations for maximum compatibility
window.solana = phantomProvider;
window.phantom = { solana: phantomProvider };
```

## Step 4: Connect via DApp UI

After injection, click the DApp's "Connect Wallet" → "Phantom" button. The DApp will call `window.solana.connect()` and receive our mock provider's public key.

## Pitfalls

1. **Page reload clears injection** — If the DApp navigates/reloads, you need to re-inject. Use `page.addInitScript()` in Playwright or `page.evaluateOnNewDocument()` in Puppeteer to persist across navigations.

2. **Transaction simulation failures** — Some DApps call `simulateTransaction` before signing. The mock provider signs but doesn't broadcast — the DApp handles broadcasting. If the DApp expects the wallet to send, you need additional RPC handling.

3. **signMessage for auth challenges** — DApps that do SIWE-style auth (sign a message to prove ownership) need real ed25519 signatures. Load tweetnacl CDN for this:
   ```javascript
   const nacl = await import('https://cdn.jsdelivr.net/npm/tweetnacl/+esm');
   const signature = nacl.sign.detached(
     new TextEncoder().encode(message),
     window._walletKeypair.secretKey
   );
   ```

4. **Multiple wallet adapters** — Some DApps use `@solana/wallet-adapter` which listens for `wallet-standard:register` events. For those, you may also need to register via `navigator.wallets.register()`.

5. **Solflare alternative** — If DApp only supports Solflare, inject as `window.solflare` with same interface (isSolflare: true, same methods).

6. **Race condition on connect** — Some DApps check `window.solana` on page load. Inject BEFORE the DApp initializes by using Playwright's `addInitScript` or navigating to `about:blank` first, injecting, then navigating to the DApp.

## Example: Full Playwright Flow

```javascript
// Playwright - inject before navigation
await page.addInitScript((privKeyB58) => {
  // Load Solana web3.js
  const script = document.createElement('script');
  script.src = 'https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js';
  document.head.appendChild(script);

  // Wait for load, then inject provider
  script.onload = () => {
    // ... decode key, create keypair, inject provider (Steps 2-3 above)
  };
}, PRIVATE_KEY);

await page.goto('https://some-dapp.com');
await page.getByRole('button', { name: /connect/i }).click();
await page.getByRole('button', { name: /phantom/i }).click();
// Wallet now connected
```

## References
- Phantom Provider API: https://docs.phantom.app/
- Solana web3.js: https://solana-labs.github.io/solana-web3.js/
- Wallet Standard: https://github.com/wallet-standard/wallet-standard
