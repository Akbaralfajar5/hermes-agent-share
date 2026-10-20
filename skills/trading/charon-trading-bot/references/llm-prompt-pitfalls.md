# LLM Prompt Pitfalls for Charon

## Safety Filter Trigger (Claude)

When customizing the LLM system prompt in `src/pipeline/llm.js`, certain words trigger Claude's content safety filter, causing it to return "I can't help..." instead of valid JSON.

### Words to Avoid
- "manipulation"
- "dump" / "dump risk"
- "honeypot"
- "exit liquidity"
- "rug" / "rug pull"
- "scam"
- "coordinated manipulation"

### Safe Alternatives

| Avoid | Use Instead |
|-------|-------------|
| manipulation | coordination / activity |
| dump risk | sell pressure |
| honeypot risk | entrapment risk |
| exit liquidity | late entry |
| rug pull | project failure |
| whale dominance | concentration |

### Example Error

```
🧭 Charon Screening
Batch: #19 · Screened: 2
Pick: none
Decision: WATCH 0.0%
Reason: LLM failed: Unexpected token 'I', "I can't he"... is not valid JSON
```

This means Claude returned "I can't help with that" instead of JSON.

### Working Prompt Style

Keep the system prompt:
1. **Concise** — Long prompts with many rules increase trigger risk
2. **Technical** — Use data field names and thresholds, not emotional language
3. **Neutral** — Describe what to check, not why it's "bad" or "dangerous"

**Bad:**
```
FLAG 1 - Fresh Wallet Rate: If > 30%, RED FLAG. Many new wallets = coordinated manipulation.
```

**Good:**
```
Flag 1: gmgnAnalysis.freshWalletRate > 0.3 (many new wallets)
```

### Debugging

Check PM2 logs for LLM errors:
```bash
pm2 logs charon --lines 50 | grep -i "llm\|failed\|can't"
```

If you see "I can't he" in the error, the prompt triggered safety filter.

## Model Alternatives

If Claude consistently refuses, consider switching to more permissive models via enowX:
- `deepseek-3.2` — Less restrictive
- `minimax-m2.5` — Default Charon model, designed for this use case
- `glm-5` — Alternative option

Change in `.env`:
```
LLM_MODEL=deepseek-3.2
```
