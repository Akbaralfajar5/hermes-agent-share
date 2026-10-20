# SUPERAGENT Security Research Reference

Use this reference for authorized bug-bounty research only.

## Core loop
SCOPE → RECON → ANALYZE → VERIFY/EXPLOIT → REPORT → TRIAGE

## Operating principles
- Read policy and OOS before touching a target.
- Recon is not a vulnerability; require demonstrated impact.
- Never fabricate tool output or exploitability.
- Use safe, minimal PoCs and fork simulations for Web3.
- Treat public client configuration, source maps, version banners, API docs, and WAF bypasses as informational unless chained to material impact.
- Redact credentials, tokens, private keys, cookies, and PII from evidence.
- Time-box dead ends and pivot when no credible exploitation path exists.

## Impact bar
Prioritize cross-user data access, authorization bypass, account takeover, code execution, server-file read, confirmed SSRF/internal access, and financial or protocol loss. Grade severity to actual evidence and prerequisites.

## Report quality
Every report needs exact reproduction steps, evidence, realistic impact, remediation, environment/timestamp, and an honest CVSS vector. Deduplicate before submission and follow coordinated disclosure.
