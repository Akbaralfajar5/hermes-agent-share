# Browser/WebGPU Mining Projects — Recon & Feasibility

Applies to projects where the user "mines" inside a browser tab: WebGPU compute,
WASM/WebGL mining. Worked example: **cherryOS** (`cherryos.dev`, `$CHERRY` on
Pons / Robinhood Chain) — "mine with your GPU / train with what you mine".

These are **DePIN/AI-style projects with no useful contract to `eth_call`**, so use the
covers the *feasibility* side: will it actually run for this user, on this machine?

## The sharpest feasibility probe: headless has no GPU adapter

Do not trust `navigator.gpu` for feature detection. A GPU-less/headless box reports it as
**truthy** while `requestAdapter()` returns **`null`** — API present, no adapter to run on.

```js
// browser_console expression, page context:
(async () => {
  const a = await navigator.gpu.requestAdapter();
  if (!a) return { adapter: null };                  // headless VPS case
  return { vendor: a.info?.vendor, arch: a.info?.architecture,
           device: a.info?.device, fallback: a.isFallbackAdapter };
})()
```

Pair it with the machine signature:

```js
({ webgpu: !!navigator.gpu, cores: navigator.hardwareConcurrency,
   mem: navigator.deviceMemory, ua: navigator.userAgent })
```

`HeadlessChrome` UA + `cores: 2` + `mem: 2` = small cloud box, not a mining rig.

**Verdict to report:** `adapter: null` is a hard blocker, not a tuning problem. These
projects fall back to **CPU threads**, so on a 2-core VPS the honest answer is "≈0 output
while the box pegs 100% CPU". The fix is not config — **it must run in a normal browser on
the user's own GPU.** Never try to run the user's mining on the agent's VPS and credit their
wallet; it cannot work and burns the host.

## What the user must do on their own machine

1. Desktop Chrome/Edge ≥113 → `chrome://gpu` → "WebGPU" must read **Hardware accelerated**.
   "Disabled"/software means CPU fallback.
2. Open the project's `sysinfo`-equivalent; confirm detected backend is **not** `cpu`.
3. Paste the credit/wallet address **before** starting, or the work is not credited.
4. Keep the tab open — suspending or closing it stops the work.
5. Intensity ~30–50% if the machine is in use; raise only when unattended.

## Reading these projects honestly

- Convert the user's hardware against the project's **stated anchor**, don't repeat the
  marketing rate. cherryOS: `2^34 hashes = 1 credit`, "an Apple M5 ≈ 3 credits/minute".
- **Proof of work is not useful work.** These readmes usually admit it; quote them rather
  than softening it.
- Check whether the coordinator/bootstrap node is still `mock` (deterministic trainer, real
  GPU nodes "joining later") — that is pre-production infrastructure.
- Browser mining burns real electricity against a token that may not cover it. State that
  plainly; do not imply profitability.
  a DEX pair even exists — rewards with no market are unpriced labour.
