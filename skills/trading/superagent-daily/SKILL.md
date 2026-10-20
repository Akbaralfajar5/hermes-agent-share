---
name: superagent-daily
description: Daily assistant — briefing, alerts, watchdog, vault, triage, voice input, screenshot analysis. SUPERAGENT v4.0 m14+m15.
---

# superagent-daily — Daily Assistant

Briefing harian, alert engine, watchdog, vault, triage, voice & screenshot input.

All scripts: `~/superagent-v4/tools/{briefing,alerts,watchdog,vault,triage,multimodal}.py`

## 1. Daily Briefing

Push ringkasan pagi otomatis via Telegram/Discord.

```python
import asyncio, os, sys
sys.path.insert(0, os.path.expanduser("~/superagent-v4"))
from tools.briefing import push_briefing
from tools.alerts import AlertEngine

async def main():
    # Inject your own providers
    async def my_portfolio():
        return {"ETH": 1.5, "USDC": 2000}
    async def my_gas():
        return {"ethereum": 25, "base": 0.01}

    await push_briefing(
        notifier=print,  # replace with Telegram notifier
        alert_engine=AlertEngine(),
        portfolio_provider=my_portfolio,
        gas_provider=my_gas
    )

asyncio.run(main())
```

Cron: `0 7 * * * cd ~/superagent-v4 && python my_briefing.py`

## 2. Alert Engine

Trigger persisten: price, gas, wallet activity, claim window.

```python
from tools.alerts import AlertEngine
ae = AlertEngine()

# Price alert
ae.add_rule("price_below", {"token": "ETH", "chain": "ethereum", "threshold": 2000},
            cooldown_s=3600, label="ETH dip")

# Gas alert
ae.add_rule("gas_below", {"chain": "ethereum", "threshold_gwei": 10},
            label="gas murah")

# Run in background
await ae.run(notifier, poll_interval_s=60, fetchers={"gas_fn": my_gas_fn})
```

## 3. Self-Healing Watchdog

```python
from tools.watchdog import Watchdog, WatchedProcess, shell_check, shell_restart
wd = Watchdog([
    WatchedProcess("charon", shell_check("pm2 show charon"),
                   shell_restart(["pm2", "restart", "charon"]), max_restarts_per_hour=5),
    WatchedProcess("meridian", shell_check("pm2 show meridian"),
                   shell_restart(["pm2", "restart", "meridian"]), max_restarts_per_hour=5),
])
await wd.run(notifier, interval_s=30)
```

## 4. Address Vault

```python
from tools.vault import Vault
v = Vault()
v.put("wallet utama", "0x52908...", kind="address")
v.put("wallet trading", "0xABC...", kind="address")

# Resolve: "kirim ke wallet utama" → auto-resolve address
addr = v.resolve_address("wallet utama")
```

## 5. Inbox Triage

```python
from tools.triage import Message, triage, format_digest
msgs = [Message(sender="bos", text="urgent: cek wallet", mentions=["@hermes"])]
d = triage(msgs, vips={"bos"}, my_handles={"@hermes"})
print(format_digest(d))
```

## 6. Voice & Screenshot

```python
# STT (Whisper lokal) — pip install faster-whisper
from tools.multimodal import transcribe
text = transcribe("/tmp/voice.ogg")

# Screenshot analysis (requires vision-capable LLM)
from tools.multimodal import describe_image
desc = describe_image("/tmp/shot.png", "error apa?", vision_fn=my_m7_vision_fn)
```

## Env Vars

```bash
HERMES_ALERTS_DB=~/.hermes/alerts.db
HERMES_BRIEFING_STATE=~/.hermes/briefing-last.txt
HERMES_BOT_HEARTBEAT=~/.hermes/bot-heartbeat
HERMES_VAULT_DB=~/.hermes/vault.db
HERMES_WHISPER_MODEL=base
HERMES_TG_BOT_TOKEN=  # bot token from @BotFather
HERMES_TG_CHAT_ID=     # target chat
```
