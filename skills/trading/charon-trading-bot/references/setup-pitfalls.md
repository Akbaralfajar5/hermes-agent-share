# Charon Setup Pitfalls

## Terminal Stuck After Directory Deletion

**Problem**: If you delete the charon folder (`rm -rf ~/charon`) while terminal session is active, all subsequent terminal commands fail:
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/charon'
```

**Workaround**: Use `execute_code` tool with subprocess instead:
```python
import subprocess
import os

os.chdir('/home/ubuntu')
result = subprocess.run(['git', 'clone', 'https://github.com/yunus-0x/charon.git'], 
                       capture_output=True, text=True, cwd='/home/ubuntu')
print(result.stdout, result.stderr)
```

## Strategy Filters Are Per-Strategy

Filter settings (mcap, ATH distance, bundler rate, bot degen, weak holders, etc.) are **NOT** in `.env`.

They are configured **per strategy** in the SQLite database. Methods to change:

1. **Telegram command**: `/stratset <strategy_id> <key> <value>`
   ```
   /stratset sniper max_mcap_usd 500000
   /stratset sniper min_mcap_usd 5000
   ```

2. **SQLite direct**:
   ```sql
   UPDATE strategies SET config = json_set(config, '$.max_mcap_usd', 500000) WHERE id = 'sniper';
   ```

3. **Telegram inline buttons**: Use `/strat` menu to adjust via UI

## Default Strategy Values

| Strategy | MCap Min | MCap Max | ATH Dist | Top20 | Bundler | TP | SL | Trailing |
|----------|----------|----------|----------|-------|---------|----|----|----------|
| Sniper | 7K | 200K | 0% | 100% | 50% | 50% | -25% | 20% |
| Dip Buy | 25K | 500K | -40% | 100% | 50% | 30% | -20% | 15% |
| Smart Money | 10K | 1M | 0% | 50% | 30% | 100% | -25% | off |
| Degen | 5K | 100K | 0% | 100% | 70% | 30% | -15% | 25% |

Only **Sniper** is enabled by default.

## GMGN API Key Format

Current format: `gmgn_<32-char-hex>`
Example: `gmgn_966ae93ad6418b6675637dc49083b5d6`

Note: GMGN API is blocked by Cloudflare Turnstile. Even with valid key, direct calls may fail. Fallback to Jupiter data works automatically when GMGN fails.

## Interactive Setup Flow

When user wants step-by-step setup, walk through each credential one at a time:
1. TELEGRAM_BOT_TOKEN
2. TELEGRAM_CHAT_ID  
3. TELEGRAM_TOPIC_ID (optional)
4. SIGNAL_SERVER_KEY
5. HELIUS_API_KEY
6. SOLANA_PRIVATE_KEY
7. JUPITER_API_KEY
8. LLM config (base URL, key, model)
9. TRADING_MODE
10. MAX_OPEN_POSITIONS
11. GMGN config
12. Exit strategy (partial TP, trailing, SL)
13. BUY_AMOUNT_SOL
14. LIVE_MIN_SOL_RESERVE

Explain each one briefly before asking for input. This builds user understanding.
