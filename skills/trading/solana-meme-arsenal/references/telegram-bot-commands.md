# Telegram Bot Command Handler for Trade History

## Overview

Auto-trading bots can expose query commands via Telegram long-polling. Users send `/history`, `/stats`, etc. and the bot responds with GMGN portfolio data.

## Available Commands

| Command | Handler | GMGN CLI |
|---------|---------|----------|
| `/positions` | Open holdings | `portfolio holdings --wallet <W> --chain sol` |
| `/history` | Recent trades | `portfolio activity --wallet <W> --chain sol` |
| `/stats` | Winrate, PnL | `portfolio stats --wallet <W> --chain sol` |
| `/orders` | Active TP/SL | `order strategy list --group-tag STMix` + `LimitOrder` |
| `/full` | All of above | Combined report |
| `/help` | Command list | Static text |

## Menu Pattern: ReplyKeyboardMarkup (Persistent Buttons)

**Preferred over text commands.** ReplyKeyboardMarkup puts persistent buttons next to the input box — user just clicks, no typing needed.

```python
# Reply Keyboard — persistent menu next to input box
MENU_KB = json.dumps({
    "keyboard": [
        [{"text": "\U0001f4ca Posisi"}, {"text": "\U0001f4dc Sajarah"}],
        [{"text": "\U0001f4c8 Statistik"}, {"text": "\U0001f4cb Pesenan"}],
        [{"text": "\U0001f4d1 Laporan Lengkep"}],
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False,         # stays visible after click
    "input_field_placeholder": "Pilih menu...",
})

# Inline keyboard for "Refresh" button inside response messages
BACK_INLINE = json.dumps({
    "inline_keyboard": [[{"text": "\U0001f504 Refresh", "callback_data": "refresh"}]]
})

# Send with reply keyboard (kb= for persistent, inline_kb= for inline buttons in message)
def send(token, cid, text, kb=None, inline_kb=None):
    d = {"chat_id": cid, "text": text, "parse_mode": "HTML"}
    if kb:
        d["reply_markup"] = kb          # ReplyKeyboardMarkup (persistent)
    elif inline_kb:
        d["reply_markup"] = inline_kb   # InlineKeyboardMarkup (in-message)
    api(token, "sendMessage", d)

# Handle both message text (from button click) and callback_query (from inline button)
def handle_msg(token, msg):
    text = msg.get("text", "")
    handler = find_handler(text)       # match button text to handler
    if handler:
        send(token, cid, handler(), kb=MENU_KB, inline_kb=BACK_INLINE)

def handle_cb(token, cb):
    data = cb.get("data", "")          # callback_data from inline button
    if data == "refresh":
        edit(token, cid, mid, handler(), BACK_INLINE)
```

**Key differences:**
| Feature | ReplyKeyboardMarkup | InlineKeyboardMarkup |
|---------|--------------------|--------------------|
| Position | Below input box (persistent) | Inside message |
| Action | Sends text message | Sends callback_query |
| Use case | Menu navigation | Per-message actions (Refresh, Back) |
| Handler | Match `message.text` | Match `callback_query.data` |


## Long-Polling Pattern

```python
import json, urllib.request, os

BOT_TOKEN_PATH = os.path.expanduser("~/.config/gmgn/bot_token.txt")
LAST_UPDATE_PATH = os.path.expanduser("~/.hermes/data/bot_last_update.json")

def poll_loop():
    token = get_bot_token()
    offset = load_last_update()
    while True:
        url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset+1}&timeout=30"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read())
        for update in data.get("result", []):
            uid = update["update_id"]
            if "callback_query" in update:
                handle_cb(token, update["callback_query"])    # inline button click
            elif "message" in update:
                handle_msg(token, update["message"])           # text/button message
            save_offset(uid)
            offset = uid
```

## Key Portfolio Fields for Bot Output

### Holdings (`portfolio holdings`)
- `token.symbol` — ticker
- `token.token_address` — CA
- `balance` — human-readable amount
- `usd_value` — current USD value
- `accu_cost` — total SOL spent
- `unrealized_profit_pnl` — PnL ratio (0.16 = +16%)

### Activity (`portfolio activity`)
- `event_type` — "buy" / "sell"
- `token.symbol` — ticker
- `token_amount` — tokens traded
- `quote_amount` — SOL spent/received
- `cost_usd` — USD value
- `buy_cost_usd` — original buy cost (for PnL calc on sells)
- `timestamp` — Unix timestamp

### Stats (`portfolio stats`)
- `realized_profit` — total realized PnL (USD)
- `winrate` — ratio 0-1
- `pnl_stat.token_num` — total tokens traded
- `pnl_stat.pnl_lt_nd5_num` — trades < -50%
- `pnl_stat.pnl_nd5_0x_num` — trades -50% to 0%
- `pnl_stat.pnl_0x_2x_num` — trades 0% to +100%
- `pnl_stat.pnl_2x_5x_num` — trades +100% to +500%
- `pnl_stat.pnl_gt_5x_num` — trades > +500%

## Telegram Message Limit

Telegram limits messages to 4096 chars. Split long reports at newline boundaries:

```python
max_len = 4000
while len(text) > max_len:
    idx = text.rfind("\n", 0, max_len)
    if idx == -1: idx = max_len
    send_chunk(text[:idx])
    text = text[idx:].lstrip("\n")
send_chunk(text)
```

## Running as Background Process

Start as Hermes background process (auto-restarts):
```bash
cd ~/.hermes/scripts && python3 bot_commands.py
```

Or as systemd service for persistence:
```ini
[Unit]
Description=GMGN Trade Bot Commands
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/ubuntu/.hermes/scripts/bot_commands.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Script Location

- **Menu bot (primary):** `~/.hermes/scripts/bot_menu.py` — ReplyKeyboardMarkup + inline callback handling
- Data query: `~/.hermes/scripts/trade_history.py`
- Bot token: `~/.config/gmgn/bot_token.txt`
- Last update offset: `~/.hermes/data/bot_last_update.json`

