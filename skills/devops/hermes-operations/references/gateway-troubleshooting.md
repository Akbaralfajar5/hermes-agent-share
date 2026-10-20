# Gateway Troubleshooting — Error Traces & Fixes

## Telegram: AsyncClient proxy parameter mismatch

### Full Error Trace
```
ERROR gateway.platforms.telegram: [Telegram] Failed to connect to Telegram: AsyncClient.__init__() got an unexpected keyword argument 'proxy'
Traceback (most recent call last):
  File ".../gateway/platforms/telegram.py", line 1423, in connect
    request = HTTPXRequest(
  File ".../telegram/request/_httpxrequest.py", line 192, in __init__
    self._client = self._build_client()
  File ".../telegram/request/_httpxrequest.py", line 227, in _build_client
    return httpx.AsyncClient(**self._client_kwargs)
TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxy'
```

### Version Matrix

| python-telegram-bot | httpx    | Result |
|---------------------|----------|--------|
| <22.8               | <0.28    | ✅ Works (uses `proxies` plural) |
| <22.8               | >=0.28   | ❌ FAILS (httpx renamed to `proxy` singular, but telegram-bot still passes old way) |
| >=22.8              | >=0.28   | ✅ Works (both use `proxy` singular) |
| >=22.8              | <0.28    | ❌ May fail (telegram-bot passes `proxy`, httpx expects `proxies`) |

### Affected Code Path
`gateway/platforms/telegram.py` line ~1414-1434:
```python
proxy_url = resolve_proxy_url("TELEGRAM_PROXY", target_hosts=proxy_targets)
# ...
elif proxy_url:
    request = HTTPXRequest(**request_kwargs, proxy=proxy_url)
    get_updates_request = HTTPXRequest(**request_kwargs, proxy=proxy_url)
```

The `proxy` kwarg goes through `HTTPXRequest.__init__()` → `self._client_kwargs` → `httpx.AsyncClient(**self._client_kwargs)`.

### Fix Commands
```bash
# Check current versions
/home/ubuntu/.hermes/hermes-agent/venv/bin/python -c "import telegram; print(telegram.__version__); import httpx; print(httpx.__version__)"

# Upgrade (in venv, NOT system pip)
/home/ubuntu/.hermes/hermes-agent/venv/bin/python -m pip install "python-telegram-bot>=22.8" "httpx>=0.28"

# Restart gateway
hermes gateway stop && sleep 2 && hermes gateway start
```

---

## WhatsApp: Non-retryable startup conflict

### Full Error Log
```
WARNING gateway.platforms.whatsapp: [Whatsapp] WhatsApp is enabled but not paired (no creds.json at ~/.hermes/platforms/whatsapp/session/creds.json). Run `hermes whatsapp` to pair, or remove WHATSAPP_ENABLED from your .env to disable.
WARNING gateway.run: ✗ whatsapp failed to connect
ERROR gateway.run: Gateway hit a non-retryable startup conflict: whatsapp: WhatsApp enabled but not paired — run `hermes whatsapp` to pair.
ERROR gateway.run: Gateway exiting cleanly: whatsapp: WhatsApp enabled but not paired — run `hermes whatsapp` to pair.
```

### Cascade Effect
When WhatsApp hits non-retryable conflict → gateway exits → Telegram (which may have connected fine) is also killed.

### Fix
```bash
# Option A: Disable in .env
sed -i 's/^WHATSAPP_ENABLED=true/WHATSAPP_ENABLED=false/' ~/.hermes/.env

# Option B: Pair WhatsApp (interactive)
hermes whatsapp
```

---

## Diagnosis Checklist

When gateway isn't connecting a platform:

1. **Check logs** (most important):
   ```bash
   journalctl --user -u hermes-gateway.service -n 50 --no-pager
   ```

2. **Check what's enabled in .env:**
   ```bash
   grep -E '^[A-Z].*ENABLED|^[A-Z].*TOKEN' ~/.hermes/.env
   ```

3. **Check package versions in venv:**
   ```bash
   /home/ubuntu/.hermes/hermes-agent/venv/bin/python -m pip list 2>&1 | grep -iE 'telegram|httpx|whatsapp'
   ```

4. **Check gateway status:**
   ```bash
   hermes gateway status
   ```

5. **Restart cleanly:**
   ```bash
   hermes gateway stop && sleep 2 && hermes gateway start
   ```
