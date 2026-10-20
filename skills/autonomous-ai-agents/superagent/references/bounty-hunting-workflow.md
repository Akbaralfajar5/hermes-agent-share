# Bug Bounty Hunting Workflow — Target Selection & Parallel Audit

## Target Selection Strategy (Immunefi)

### Sorting criteria (priority order)
1. **Max bounty** — $1M+ = Tier 1 targets (Ethena $3M, Origin $1M)
2. **Recently updated** — active maintenance = responsive triage team
3. **Vault TVL** — higher vault = more likely to pay out
4. **Staleness** — programs not updated in 6+ months = fewer hunters, more low-hanging fruit
5. **Total paid** — programs that have paid before (The Graph $1.5M) are proven payers
6. **Resolution time** — sub-24h = fast triage, less waiting

### Red flags (deprioritize)
- "KYC Required" reduces anonymity but doesn't block submission
- "Private" total paid = no track record visible
- Very small vault ($1-$150) = may not honor large payouts

### Tier Strategy
| Tier | Bounty Range | Approach |
|------|-------------|----------|
| Quick wins | $2.5K-$50K | Web/API bugs, newer protocols with less scrutiny, stale programs |
| Mid game | $50K-$250K | Smart contract logic errors, access control, precision bugs |
| Big game | $250K-$3M | Critical fund-draining exploits, complex multi-step attacks |

## Source Code Acquisition

### Priority order for getting contract source
1. **GitHub org repos** — `gh repo list <org> --limit 20` to find public repos
2. **Contest repos** — many protocols have audit contest repos (e.g., `ethena-usdtb-contest`)
3. **Etherscan verified source** — `cast etherscan-source <address>` (requires Foundry + ETHERSCAN_API_KEY)
4. **Browser Etherscan** — often Cloudflare-blocked from server; use as last resort

### When Etherscan is blocked
- Etherscan aggressively blocks non-residential IPs (Cloudflare challenge)
- Workaround: find the repo on GitHub via org name, or use `cast` CLI with API key
- Alternative explorers: Blockscout, Sourcify (less aggressive blocking)

### When Foundry is not installed
- Contract source still readable from GitHub repos
- Delegate audit to subagent (reads source, provides findings)
- Install Foundry later for PoC development: `curl -L https://foundry.paradigm.xyz | bash && foundryup`

## Parallel Audit Pattern (delegate_task)

### Strategy: dispatch multiple audits simultaneously
```
Target 1 (high bounty) → delegate_task with full context
Target 2 (different protocol) → delegate_task with full context
```

### What to pass in delegation context
1. Repo path with all .sol file locations
2. Architecture description (from CLAUDE.md or docs)
3. Known issues that are NOT eligible (from Immunefi page)
4. Specific vulnerability classes to hunt
5. Bounty amounts and severity tiers for prioritization

### Subagent audit prompt template
```
Audit [PROTOCOL] smart contracts at [PATH]. Max bounty: $[X].

Main contracts:
- [list key .sol files]

Focus on:
1. [vuln class 1]
2. [vuln class 2]
...

Known issues (NOT eligible):
- [list from program page]

For each finding: Severity, Description, Attack Scenario, PoC code, Fix.
```

## Immunefi Program Page — What to Extract

Before starting audit, always pull from the program page:
1. **Reward tiers** — Critical/High/Medium/Low amounts
2. **Scope** — which contracts/assets are in scope
3. **Known issues** — bugs already reported (ineligible for reward)
4. **PoC requirement** — most programs require working PoC
5. **KYC requirement** — plan ahead if needed
6. **Primacy of Impact vs Rules** — affects what you can submit
7. **Previous audits** — check audit reports for unfixed issues

## Vulnerability Classes by ROI (highest hit rate)

```
1. Price oracle manipulation (TWAP bypass, stale price)
2. Cross-function reentrancy (ERC-777, hooks, callbacks)
3. First depositor attack (vault share inflation)
4. Signature replay / permit abuse / deadline bypass
5. Access control gaps (missing modifiers, initializer not called)
6. Rounding errors in share/token math (precision loss)
7. Unchecked return values on low-level calls
8. Proxy storage collision (UUPS upgrade bugs)
9. Block limit / rate limit bypass
10. Flash loan + governance / oracle manipulation
```

## Post-Finding Workflow

1. **Validate locally** — fork test with Foundry, NOT mainnet
2. **Assess severity** — use Immunefi severity classification
3. **Draft report** — Title, Summary, Severity, Steps, Impact, PoC, Fix
4. **Submit** — via Immunefi dashboard, select correct asset
5. **Track** — save submission ID, check for triage responses
