---
name: crypto-project-review
description: "Evaluate new crypto projects for legitimacy, quality, and airdrop/investment potential. Due diligence framework: read docs, check contracts, assess red flags, rate 1-10, recommend action."
triggers:
  - review project
  - bagus ga
  - legit ga
  - scam ga
  - worth it
  - aman ga
  - project baru
  - cek project
  - due diligence
  - rug pull check
---

# Crypto Project Review & Due Diligence

## When to Use

User sends a project URL, contract address, or asks "bagus ga / legit ga / scam ga" about any crypto/DeFi/NFT project.

## Review Framework (ordered)

### 1. Read Everything Available
- Docs / whitepaper / lite paper
- Landing page claims vs actual implementation
- Smart contract (if address provided) — check on explorer
- Twitter/X presence and engagement
- GitHub (if open source)

### 2. Technical Assessment

| Check | What to look for |
|-------|-----------------|
| **Contract verification** | Verified on explorer? Audit report linked? |
| **Contract really live** | `eth_getCode` non-zero — don't trust a "contract address" from marketing |
| **Traction (THE key test)** | `eth_getTransactionCount` on the contract, `launchCount()`, holder count, DexScreener `txns.h24`. Deployed ≠ used. |
| **Custody model** | Non-custodial claim but uses deposit addresses = custodial moment |
| **Chain choice** | Established (ETH, Arb, Base) vs unknown chain |
| **Open source** | Can claims be verified? |
| **Fee transparency** | Exact % shown or "all-in quote" hiding markup? Verify the number via `eth_call` |
| **Tokenomics** | Supply, distribution, vesting, buy/burn mechanics — check `totalSupply()` matches the claim |
| **Bonding curve / AMM** | Formula shown? Immutable? |

**Verify every marketing number with one `eth_call`.** If the site says "launch fee
0.001 ETH", call `launchFee()` and compare. Match = honest. Mismatch = red flag. Numbers
that cannot be verified get reported as unverified, never assumed true.

**The single sharpest question in a crypto review: has it been used, or only deployed?**
Contract nonce `0x1`, `launchCount() = 0`, supply still in one wallet, DEX volume under
$100/day — that is the whole verdict. Report it as `🟠 LIVE BUT ZERO TRACTION`: real code,
real contract, real revenue model, zero users. That is neither "scam" nor "good project",
and saying it that way is the honest answer.

### 2b. Website & Stack Due Diligence (DePIN / AI / non-contract projects)

Project types without a smart contract — DePIN bandwidth, AI tools, SaaS-style token
projects — have nothing to `eth_call`. Judge them on **who built the site and how**, plus
whether the reward token actually exists anywhere tradable.

| Signal | Command | Verdict |
|---|---|---|
| Hosting + platform | `curl -skI "https://TARGET/"` → `server`, `x-powered-by`, `platform` | — |
| **AI/website-builder** | `x-powered-by: HostingerWebsiteBuilder`, `platform: hostinger`, HTML meta `generator: Hostinger AI Builder` | 🔴 site is drag-drop template, not engineering |
| Brand-name mismatch | HTML `<title>` / JSON-LD `"name"` differ from the visible product name | 🟠 template leftover, nobody proofread |
| Domain age | `curl -s https://rdap.verisign.com/com/v1/domain/DOMAIN` → `events[].eventDate` | young = thin track record |
| Docs freshness | GitBook/GitHub `last updated` | "1 year ago" while site is active = docs are dead |
| Docs brand vs site brand | GitBook path (e.g. `azurewave.gitbook.io`) vs product name | 🟠 different brands = copy-paste |
| **Reward token tradability** | `curl -s "https://api.dexscreener.com/latest/dex/search?q=SYMBOL"` | no matching pair = rewards have **no market to cash out** |
| Chain mismatch | Site on Robinhood Chain while docs cite another chain's subnets | 🟠 no on-chain connection between the two |

**The sharpest DePIN question: can the reward actually be sold?** A bandwidth/task-farming
project whose token has no DEX pair is unpaid labour — the user burns data quota and battery
for points that cannot be converted. Report that as the headline, not a footnote.

Two free endpoints carry almost all of the signal:

```bash
# Brand + generator + registrar, all in one request
curl -skL "https://TARGET/" | grep -oE '<meta[^"]*(generator|og:site_name)[^>]*>|"name":"[^"]*"' | head

# Domain age (no whois binary needed — RDAP is JSON)
curl -s "https://rdap.verisign.com/com/v1/domain/DOMAIN" | python3 -m json.tool | grep -A2 eventAction
```

**AI-builder-site pattern (report as `🟠 TEMPLATE LAUNCH`):** name left over in `<title>`,
JSON-LD, and the GitBook path; docs not touched in a year; no whitepaper/tokenomics/pricing;
social presence = a Telegram + X account with no engagement. The prototype is real, the
*company* is not built yet. That is not a scam call and not a "good project" call — say both
halves.

**Also check `meta name="author"` / `twitter:site` for the builder brand** (`Lovable`,
`@Lovable`) — an AI-site-builder credit is the same signal. Full worked example (OrbitAI DPN,
bandwidth DePIN) plus the no-contract checklist: `references/review-examples.md`.

### 2c. Browser-Based Mining Projects (WebGPU / DePIN compute)

When the user wants to **mine** in a browser tab (cherryOS-style: "mine with your GPU through
WebGPU"), the legitimacy checklist above is only half the job — the other half is feasibility.
The sharpest probe: a headless/GPU-less box reports `navigator.gpu` as truthy while
`requestAdapter()` returns **`null`**. That is a hard blocker, not a tuning problem, because
these projects silently fall back to CPU threads (≈0 output on a small VPS while pegging the
CPU). Browser GPU mining must run in a normal browser on the user's own machine — never on the
agent's headless VPS credited to their wallet. Full probe, the "what the user must do on their
own machine" checklist, and the honest-reading notes (reward anchors, proof-of-work ≠ useful
work, `mock` coordinator): `references/browser-webgpu-mining-recon.md`.

### 3. Red Flag Checklist

Score each (🔴 = critical, 🟡 = concerning, 🟢 = OK):

- Team doxxed / anon?
- Audit by reputable firm?
- Testnet vs mainnet?
- Age of project (days since launch)?
- TVL / volume (real or wash)?
- Social followers vs engagement ratio
- "Too good to be true" yield claims?
- Deposit-address model (funds leave your wallet to theirs)?
- No GitHub / closed source claiming "non-custodial"?
- Buzzword-heavy docs with no technical depth?
- Fork of dead project (friend.tech, OHM, etc)?
- Contract ownership / upgradeability / pause functions?

### 4. Scoring

| Score | Meaning |
|-------|---------|
| 9-10 | Blue chip, audited, proven track record |
| 7-8 | Solid project, minor concerns |
| 5-6 | Speculative, worth testnet farming only |
| 3-4 | High risk, likely not worth time |
| 1-2 | Probable scam, do not interact |

### 5. Action Recommendation

Always end with one of:
- **Farm testnet** — zero cost, potential airdrop
- **Small position OK** — limited upside but low risk
- **Wait for mainnet** — too early to commit
- **Avoid** — high scam probability or dead model
- **Deep audit needed** — looks interesting but needs contract review

## Promotion & Deposit-Bonus Research

Use this section when the user asks for a promo, deposit bonus, cashback, top-up event, or whether a reward can be withdrawn.

1. Search in this order: official promo/event page or in-app campaign page → official terms/FAQ → official social announcement → reputable secondary source only for discovery. Search snippets and affiliate pages are leads, not proof.
2. Establish status against the current date/time. Mark each event `ACTIVE`, `EXPIRED`, `UNCLEAR`, or `NOT VERIFIED`; never call an event active from an undated or old page.
3. Extract separately: eligibility (new/existing user, KYC, region); funding action (minimum deposit/top-up, payment method, one-time vs cumulative); qualifying action (trade/purchase/turnover, minimum amount, excluded pairs/items); reward type (cash, crypto cashback, points, voucher, trading credit); reward cap, quota, reset time, distribution delay; and withdrawal/use restrictions, fees, expiry, and principal risk.
4. Distinguish deposit bonus from cashback/points and trading credit. Never imply cash withdrawal unless the official terms explicitly allow it.
5. Calculate break-even only from verified fees and requirements. Do not recommend depositing solely to chase a reward.
6. For crypto exchanges, check official availability/licensing for the user's jurisdiction and link the official terms. For game or betting categories, label legal, withdrawal, and account-closure risks; promotional claims are not guaranteed income.

Output table: platform | status/end date | deposit/top-up | qualifying action | reward | cash-out restriction | official link.

## Verification

Before finalizing, quote the official source date and key terms, and state which details remain unverified. If no current official source is accessible, say `belum terverifikasi` rather than inferring from search snippets.

## Output Format

```
## [Project Name] — Ringkasan
[1 paragraph what it does]

## Mekanik Utama
[Table of key features]

## Bukti On-Chain (klaim vs state chain)
[Table: klaim di web | bukti eth_call/DexScreener | putusan ✅/🟠/🔴]

## Penilaian
**Yang menarik:** [bullets]
**Red flags:** [bullets with 🔴🟡🟢]

## Verdict
**X/10 — [one line summary]** + label traksi (🟢/🟡/🟠/🔴/⚫)
[Strategy recommendation]

## Catatan Keterbatasan
[Apa yang belum terverifikasi, dan kenapa]
```

Jawab tiga pertanyaan user secara eksplisit kalau dia menanyakan ketiganya — jangan cuma
satu. Contoh pola yang diminta user: **"project bagus ga?" → "website-nya gimana?" →
"project real?"**. Jawab berurutan: kualitas konsep, kualitas produk/web, lalu bukti realitas
(kontrak + traksi). Setiap klaim teknis harus punya satu bukti tool di belakangnya.

## Penilaian Traksi — Skala Wajib

Setiap review crypto HARUS menutup dengan salah satu label traksi ini. Ini yang membedakan
jawaban berguna dari "web-nya cakep".

| Label | Kriteria | Artinya |
|---|---|---|
| 🟢 **PRODUKTIF** | Pemakaian nyata + volume berkelanjutan + holder tersebar | Layak dipakai/difarm |
| 🟡 **AWAL TAPI HIDUP** | Ada volume, ada holder, tapi kecil/baru | Testnet-farm / watchlist |
| 🟠 **LIVE, ZERO TRACTION** | Kontrak live, nonce `0x1` / counter 0 / volume < $100/hari | Kode real, nol pengguna |
| 🟠 **TEMPLATE LAUNCH** | Situs dari AI/website builder, brand name nyangkut dari template, docs mati, token reward tidak ada pasarnya | Kosmetik — jangan invest tenaga |
| 🔴 **VAPORWARE** | "Contract address" tidak ada `eth_getCode`-nya, atau klaim ≠ on-chain | Jangan sentuh |
| ⚫ **SCAM** | Honeypot, drainer, custodial diam-diam, owner bisa rug | Hindari total |

**Dua label 🟠 ini berbeda dan jangan dicampur.** `LIVE, ZERO TRACTION` = engineering asli,
belum ada pengguna. `TEMPLATE LAUNCH` = tidak ada engineering, cuma template + copywriting.
Yang pertama bisa dipantau; yang kedua jangan diinvestasikan tenaga.

**Aturan pelaporan yang tidak boleh dilanggar:**
- Jangan sebut "scam" hanya karena traksi nol. Nol pengguna itu bukan kejahatan.
- Jangan sebut "bagus" hanya karena kontraknya live dan UI-nya rapi.
- Angka marketing yang tidak bisa diverifikasi → tulis `belum terverifikasi`, bukan diasumsikan benar.
- Selalu cross-check angka dari web mereka dengan state on-chain, dan tampilkan sebagai tabel
  berdampingan (klaim kiri, bukti kanan) supaya putusannya kelihatan berdasar.

## Verifikasi On-Chain (Crypto/DApp)

Saat user mengirim URL project, jangan berhenti di landing page — landing page itu marketing.
Sumber kebenaran ada di **JS bundle** (RPC URL + alamat kontrak + ABI ter-embed) dan **state
chain**.

```bash
# 1. Ambil RPC dari bundle, JANGAN tebak dari nama domain
curl -skL "https://TARGET/" | grep -oE 'src="[^"]+\.js"'          # nama asset
curl -skL "https://TARGET/assets/index-XXX.js" -o /tmp/t.js
grep -oE "https?://[a-zA-Z0-9._/-]{6,80}" /tmp/t.js | grep -i rpc
grep -oE "0x[a-fA-F0-9]{40}" /tmp/t.js | sort | uniq -c | sort -rn  # alamat kontrak
grep -oE '\{type:"function",name:"[A-Za-z0-9_]+"' /tmp/t.js | sort -u # ABI ter-embed

# 2. Baca state chain langsung (selalu kirim User-Agent — banyak RPC publik 403 tanpa itu)
curl -s -X POST "$RPC" -H 'content-type: application/json' -H 'User-Agent: Mozilla/5.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getCode","params":["0xADDR","latest"]}'
# lalu: eth_getTransactionCount (traksi), eth_getBalance, eth_call owner()/launchFee()/totalSupply()

# 3. Traksi & harga: DexScreener (chain id di path, mis. "robinhood")
curl -s "https://api.dexscreener.com/latest/dex/search?q=SYMBOL"
```

**Pitfall:** `eth_getLogs` balas `[]` atau error `Archive requests require a personal token`
BUKAN berarti kontraknya kosong — RPC publik cuma simpan window block terbatas. Cross-check
dengan `eth_call` baca-balik (`totalSupply`, `balanceOf`) sebelum menyimpulkan apa pun.

**Pitfall: grep alamat kontrak di bundle bisa balik KOSONG padahal kontraknya ada.** Kalau
`grep -oE "0x[a-fA-F0-9]{40}"` cuma nemu alamat sentinel (`0x0`, `0xeeee…`, `0xffff…`,
`0xdeadbeef`), itu tanda **factory pattern**: frontend tidak menyimpan alamat kontrak,
melainkan menyimpan **bytecode contract sebagai string** lalu deploy/deploy-per-request
(mis. CREATE2). Cara mendeteksinya:

```bash
# bytecode blob yang di-embed (bukan alamat) — panjang ratusan–ribuan hex char
grep -oE '0x60806040[0-9a-fA-F]{200,}' /tmp/t.js | awk '{print length($0)}' | sort -un
# ABI factory yang bocor lewat definisi fungsi, bukan lewat alamat
grep -oE '\{type:"function",name:"[A-Za-z0-9_]+"' /tmp/t.js | sort -u
# endpoint backend yang dipakai buat deploy/claim (sering kebuka tanpa auth di probe GET)
grep -oE '/api/[a-zA-Z0-9/_-]{3,60}' /tmp/t.js | sort -u
```

Blob 798–11.188 char = template token yang dideploy on-demand. Untuk kasus begini, ABI dari
bundle (mis. `launchFee()`, `launchCount()`) tetap bisa dipanggil — tapi hanya setelah alamat
launcher/factory-nya ketemu. Kalau alamatnya tidak ada di bundle sama sekali, catat sebagai
**`belum terverifikasi`**, jangan karang alamat dan jangan simpulkan kontraknya tidak ada.

**Pitfall: `meta name="author"` / generator = AI website builder.** `author: Lovable`,
`twitter:site: @Lovable`, atau `x-powered-by: HostingerWebsiteBuilder` itu sinyal kuat
"template launch" — bukan otomatis scam, tapi turunkan keyakinan dan wajib dicek bareng
`references/review-examples.md` pola `🟠 TEMPLATE LAUNCH`. Cloudflare di depan situs juga
bukan bukti apa-apa, cuma proteksi.

Resep lengkap + RPC dan alamat kontrak terverifikasi: lihat skill `web-recon-passive`
bagian Step 15 dan `references/robinhood-chain-4663.md` / `references/webapp-technical-teardown.md`.

## Pitfalls

- **"Non-custodial" with deposit address** — if user sends funds to a generated address controlled by the project, that's a custodial moment regardless of what docs claim. Flag it prominently.
- **Fork of dead model** — friend.tech bonding curve SocialFi, OHM (3,3), Safemoon tokenomics — all historically failed to retain. Discount score by 2 points if it's a fork of a dead narrative without meaningful innovation.
- **Testnet ≠ mainnet** — many projects stay testnet forever. If still testnet, max score is 6/10 regardless of how good the concept is.
- **Privacy swap = mixer rebrand** — projects claiming "private swap" without ZK proofs, using 2-exchange intermediary routing, are just mixers with nice UI. High regulatory risk + high rug risk.
- **Robinhood Chain / unknown chains** — new L2/L3 with no ecosystem = liquidity desert. Extra caution.
- **Contract address without context** — if user sends just a CA, check: (1) explorer for verification, (2) holder distribution, (3) liquidity locked?, (4) deployer history.

## References

- `references/review-examples.md` — past project reviews for pattern matching
- `references/browser-webgpu-mining-recon.md` — browser-tab mining feasibility: the `navigator.gpu` truthy / `requestAdapter()` null trap, headless-VPS blocker, user-machine checklist, honest-reading notes (cherryOS worked example)
