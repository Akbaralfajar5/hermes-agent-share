---
name: bug-bounty-hunting-strategy
description: >-
  Bug bounty program selection, platform economics, and target triage for actually earning bounties. Use when the user wants to "find bugs / make money" from bug bounty, asks which platform/program to hunt, or when deciding whether a target is worth auditing. Complements the vuln-class playbooks (smart-contract-vulnerabilities, ssrf, xss, etc.) which cover HOW to exploit — this covers WHERE to hunt and WHAT is worth your time.
---

# SKILL: Bug Bounty Hunting Strategy — Where to Hunt, What Pays

> **AI LOAD INSTRUCTION**: This is the meta-layer above the vuln-class playbooks. Load when the user's goal is *earning* from bounties, not exploiting a specific target already chosen. It encodes hard-won lessons about platform fit, target-selection economics, honest expectation-setting, and how to use AI audit subagents without fooling yourself.

## References

- `references/yeswehack-gopay-recon-2026-07.md` — Passive recon results for GoPay/Gojek (subdomains, staging env, HTTP fingerprints). Needs scope confirmation before active testing.
- `references/dev-server-in-production-pattern.md` — Quick-win discovery: Vite/Webpack/Next.js dev server exposed in production → full source code leak. Includes detection one-liners, framework fingerprints, extraction guide, and real-world example (paddock.games Jul 2026).
- `references/web-app-recon-quick-wins.md` — Actionable patterns: Express error-page fingerprint, CSP header as service map, OAuth dynamic registration check, /api/health info leak, CORS misconfig test, Expo bundle analysis, staging API probing. All from real finds (paybox.sh, paddock.games Jul 2026).
- `references/paybox-recon-case-study-2026-07.md` — Full recon walkthrough: paybox.sh from zero knowledge to complete API surface, OAuth dynamic registration vulnerability, and service architecture map — using only passive OSINT and public APIs.
- `references/disproof-first-validation-gate.md` — **the kill layer that runs BEFORE you report.** Distilled from an operator-supplied "maximum assurance" validation framework (80 sections): the four hard gates, writing a property-level oracle (vs the rejected "response looks wrong" symptoms), the baseline/negative-control/attack triad, four adversarial passes (assume correct / assume wrong / assume overclaimed / assume evidence is misleading), the false-positive kill list, E0–E5 evidence levels **with the derivative-evidence penalty** (10 agents reading one response = 1 observation, not 11 confirmations — agreement is not proof), impact bounding (`demonstrated_*` drives severity, never `plausible_maximum`), the overclaim vocabulary detector, duplicate-by-root-cause clustering, and the no-escalation stop conditions. Full template: `templates/validation-prompts.md`. Automated first pass on a draft: `scripts/check_overclaim.py <report.md>` (flags unhedged overclaim vocabulary, missing mandatory sections, and absence of concrete evidence refs — calibrate it against a deliberately bad draft AND a good one before trusting it).

## 0. HONEST FRAMING (do not skip — user asked to "cari duit")

Bug bounty is a long grind, not a quick payday. Set expectations up front instead of overpromising:

- ~90% of hunters never earn their first bounty. The ones who cash out are the ones who grind 6–12 months.
- Months 1–3 are usually $0. That is the learning phase, not the earning phase. Normal.
- **Duplicates are the primary enemy.** Find a real bug 2 hours after someone else reported it = $0. Speed + sparse targets beat raw skill on crowded programs.
- Realistic income curve: M1–3 $0–500 · M4–6 $500–3K · M6–12 $3K–15K · Y2+ $30K–100K+ for the top ~5% who go full-time.

Tell the user this plainly. It prevents the "why haven't I made money" churn later. Being honest here is a first-class part of the job, not a downer.

## 1. PLATFORM ↔ BUG-TYPE FIT (the #1 targeting mistake)

Match the platform to the bug class the user can actually find. Wrong platform = wasted effort.

| Platform | Primary focus | Web/API scope? | Smart contract scope? |
|---|---|---|---|
| **Immunefi** | Smart contracts / Web3 | ❌ Rare — "Web & App" tabs are usually just block-explorer contract links, NOT testable web apps | ✅ Almost everything |
| **HackerOne** | Web2 + some Web3 | ✅ Thousands of web programs | Some |
| **Bugcrowd** | Web2 + some Web3 | ✅ Many web scopes | Some |
| **YesWeHack** | Web2 (EU-heavy) | ✅ | Some |
| **Code4rena / Sherlock / Cantina** | Smart-contract audit *competitions* | ❌ | ✅ (shared prize pool, time-boxed) |

**Hard-learned pitfall:** On Immunefi, clicking "Web & App" scope on a DeFi program (e.g. Ethena) shows only `etherscan.io` / `tonviewer` contract-address links — those are on-chain contracts, NOT web attack surface. If the user wants web/API bugs (IDOR, SSRF, auth bypass, XSS), route them to HackerOne/Bugcrowd, not Immunefi. Crypto companies with real web bounties (Coinbase, Kraken, Crypto.com) live on HackerOne.

## 2. TARGET SELECTION ECONOMICS (hit-rate > payout headline)

The $3M max-bounty number is a trap. Payout size is inversely correlated with your odds of finding anything.

| Target profile | Hit rate | Payout | Verdict |
|---|---|---|---|
| Mature blue-chip protocol (Ethena, SSV, Aave) — audited 5–10× by top firms + hundreds of whitehats | **<1% for a newcomer** | $100K–3M | Avoid as a beginner; low-hanging fruit is long gone |
| Fresh protocol, <1 month live, <3 audits | Medium | $5K–50K | **Best smart-contract ROI** |
| Live audit contest (Code4rena/Sherlock) | Medium | Prize-pool share | Transparent, competitive, good for learning |
| Web program with wildcard scope (`*.company.com`), recently added assets | **High** | $1K–15K | **Best web ROI**, fastest first cash |
| Popular/old web program (PayPal, Google) worked by 1000s | Low | Varies | Duplicate graveyard |

**Selection heuristics for sparse competition:**
- Prefer programs launched in the last ~30 days (fewer eyes).
- Prefer wildcard scope over single-domain (bigger attack surface).
- Watch for newly-added assets/subdomains in scope changelogs.
- VDP → private-invite path: perform on a public VDP, get invited to sparse private programs.
- Verify the scope explicitly lists the asset before touching it. Out-of-scope testing = illegal + unpaid.

## 3. AI AUDIT SUBAGENTS: TRIAGE TOOL, NOT PROOF ENGINE

Delegating a contract audit to a subagent is useful for *surfacing candidates*, but treat output with skepticism:

- **Self-invalidation is common.** A thorough subagent will list a "Critical" then re-evaluate and mentally retract it ("Not a vulnerability"). Read the whole finding — the verdict often lives in the last line, not the header.
- **Long audits time out.** A single-shot audit of a large codebase can hit the subagent wall-clock limit (~600s) and return nothing. Scope each delegation to ONE contract / one attack-vector cluster, not "audit everything."
- **AI findings are hypotheses, not confirmed bugs.** A real Critical requires a working PoC on a mainnet fork. Never report an AI-surfaced finding as confirmed without reproducing it yourself.
- **Net for mature protocols:** expect mostly Medium/Low dust findings (rounding, precision, liveness edge cases). If that's all you get, that's the signal to switch to a fresher target, not to submit marginal reports.

Good delegation shape: one subagent per contract, explicit attack-vector list, "provide severity + attack scenario + PoC + fix," and pass the program's *known/ineligible issues* list so it doesn't rediscover dupes.

## 4. WORKFLOW ORDER (recon > exploitation)

For web targets, attack surface breadth is the differentiator that separates you from the 90%:

```
1. Pick program with WIDE scope (*.target.com), verify assets in-scope
2. Passive recon FIRST (100% legal OSINT, never touches target):
   - crt.sh (cert transparency → subdomains)
   - Wayback Machine / gau / waybackurls (historical endpoints)
   - GitHub dorking (leaked keys, internal hostnames)
3. Subdomain enum → subfinder, amass, dnsx
4. HTTP probe → httpx (which hosts are alive)
5. Content discovery → ffuf, katana (endpoints, hidden params)
6. JS analysis → API endpoints, leaked keys, hidden params
7. nuclei → known CVE + misconfig sweep
8. Manual test → what the scanners missed (this is where bounties live)
```

Passive recon (steps 1–2) is always safe and can run before any authorization concern. Active steps (3+) only against in-scope assets.

## 5. SPECIALIZATION (month 3+)

Jack-of-all-trades stays hungry. Master ONE vuln class and route to its playbook:

| Specialization | Playbook skill | Why it pays |
|---|---|---|
| Access Control / IDOR | business-logic-vulnerabilities, api-auth-and-jwt-abuse | Most common, most often missed |
| SSRF → RCE chains | ssrf-server-side-request-forgery | High-critical, big payout |
| OAuth / SSO bypass | jwt-oauth-token-attacks, authbypass-authentication-flaws | Complex, few can do it |
| Smart contract | smart-contract-vulnerabilities, defi-attack-patterns | $50K–3M but 6+ months to get good |

## 6. DECISION TREE

```
User wants to earn from bug bounty?
├── What bug class can they find?
│   ├── Web/API (IDOR, SSRF, XSS, auth) → HackerOne / Bugcrowd (NOT Immunefi)
│   └── Smart contract (Solidity) → Immunefi / Code4rena
├── Set honest expectations (Section 0) BEFORE they start
├── Choose target by HIT RATE, not headline payout (Section 2)
│   ├── Beginner + blue-chip protocol → redirect to fresh/small target
│   └── Web → wildcard scope, recently launched, sparse
├── Recon first, always passive before active (Section 4)
├── Use AI audit as triage only; reproduce before reporting (Section 3)
└── Push toward ONE specialization by month 3 (Section 5)
```

## 7. YESWEHACK-SPECIFIC NOTES

YesWeHack is the #1 European platform with 62 public bug bounty programs. Key learnings:

**Program visibility:** Scope details require login. Unlike HackerOne, you can see program names + reward ranges on the listing page, but the actual scope (domain list, rules) is gated behind registration.

**Indonesian targets on YesWeHack (cultural advantage for ID-based hunters):**
- **Superbank** — $0–$2K, 5 scopes, only 72 reports (VERY sparse)
- **GOJEK** — $5–$5K, 12 scopes, 876 reports
- **GoTo Financial** — $5–$7K, 14 scopes, 703 reports
- **DANA** — $0–$3K, 4 scopes, 267 reports

**High-payout programs:**
- Swiss Post E-Voting — €100–€230K (4 scopes, voting infrastructure)
- Doctolib — €0–€50K (9 scopes, healthcare, GDPR-heavy = severity escalation)
- FDJ United — €50–€15K (33 scopes, online gambling)

**Sparse/fresh targets (< 200 reports = low competition):**
- Moneybox (€50–€2K, 6 scopes, 133 reports)
- Thüringer Aufbaubank (€50–€7K, 2 scopes, 136 reports)
- DataDome Bot Bounty (€200–€1K, 6 scopes, 105 reports)
- Superbank (5 scopes, 72 reports — sparsest by far)

**Workflow:** Register → pick program → read scope → confirm domains in-scope → passive recon → active test. Never test before confirming scope.

## 8. PASSIVE RECON — LEGAL OSINT TECHNIQUES

These techniques touch only public infrastructure and are safe to run BEFORE scope confirmation:

**DNS brute via Google DoH (no tools needed):**
```bash
# Probe common subdomains via Google's public DNS API
SUBS="api app dev staging beta admin dashboard portal m mobile wallet pay merchant partner"
for sub in $SUBS; do
  result=$(curl -s --max-time 3 "https://dns.google/resolve?name=${sub}.target.com&type=A" | jq -r '.Answer[0].data // empty')
  if [ -n "$result" ]; then echo "✅ ${sub}.target.com → $result"; fi
done
```

**Quick HTTP fingerprint (after finding subdomains):**
```bash
curl -s --max-time 5 -o /dev/null -w "HTTP %{http_code} | Size: %{size_download}" "https://subdomain.target.com"
curl -s --max-time 5 -I "https://subdomain.target.com" | head -15  # headers
```

**Interesting signals from recon:**
- `staging.*` accessible publicly → often has weaker security, testing features exposed
- `.env` returns 403 (not 404) → file EXISTS but is blocked; possible misconfiguration
- Outdated framework versions in headers/HTML (e.g., Gatsby 2.18.4 from 2019)
- Server headers revealing CDN/infra (ESA = Alibaba Cloud, tells you about WAF)
- `robots.txt: Disallow: /` → site doesn't want indexing but is still public
- **Dev server exposed** (Vite `/@vite/client`, Webpack `__webpack_hmr`, Next.js `buildId:development`) → source code leak, often Critical. See `references/dev-server-in-production-pattern.md`

**30-second dev-mode check (run on EVERY new target):**
```bash
curl -s "https://target.com/" | grep -qi "vite/client\|@react-refresh\|webpack.*hmr\|buildId.*development" && echo "⚠️ DEV MODE DETECTED"
```

**What NOT to do without scope confirmation:**
- ❌ Directory bruteforce (ffuf, gobuster)
- ❌ Parameter fuzzing
- ❌ Any injection testing
- ❌ Automated scanning (nuclei, nikto)

## 9. PACK / PLAYBOOK INTEGRATION


## 10. PITFALLS

- Chasing the $3M number into a protocol audited 10 times → weeks of work, $0.
- Hunting web bugs on Immunefi (contract-only) → no attack surface exists.
- Reporting an AI-surfaced "Critical" without a working PoC → rejected, reputation hit.
- Testing out-of-scope assets → unpaid at best, legal exposure at worst. Always confirm scope.
- Submitting marginal Medium/Low dust on a mature protocol → likely downgraded to Informational; time better spent on a fresh target.
- One giant "audit everything" delegation → times out, returns nothing. Scope per-contract.
- **Never accept user credentials** (email/password) in chat for login. Refuse, tell them to change the exposed password, and explain they must login themselves. Reference by action ("lo login dulu, paste scope ke gue"), never handle creds.
- **Don't help exploit live systems for personal gain.** Bug bounty = find → report → get paid. Exploiting a live game/protocol for profit (e.g., "bikin gue menang terus") is fraud. Redirect to responsible disclosure or "provably fair" audit.
- **A validation framework is not an authorization.** Being handed a polished bug-validation methodology (or a skill file like `references/disproof-first-validation-gate.md`) plus a third-party URL is not scope evidence — the two arrive together but only one grants permission. Run Gate 1 first: if the asset is not the operator's and no written program scope covers it, the answer is `BLOCKED`, said plainly and early. Offer the framework as a tool for assets he actually owns or is contracted to test. Building a toolkit is fine; aiming it at a stranger's production system is not. Observed Oct 2026: an 80-section validation framework + a third-party protocol's `/security` page, with no scope — refused up front, then delivered the toolkit for authorized use, which was the actual ask underneath.
