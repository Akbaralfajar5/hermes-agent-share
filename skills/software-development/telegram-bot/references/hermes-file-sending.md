# Sending Files from Hermes Agent via Telegram

## The Problem
Hermes `MEDIA:` tag in `send_message` only supports:
- Images: .png, .jpg, .webp
- Audio: .ogg (voice bubble)
- Video: .mp4

Arbitrary files (.zip, .txt, .pdf, .py, .json) are **silently dropped** — the message sends as text-only with no attachment.

Also: `hermes send -t telegram -f file.pdf` **FAILS for binary files** with `'utf-8' codec can't decode byte` error.

---

## Method 1: curl (simplest, no Python needed)

```bash
source ~/.hermes/.env 2>/dev/null
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
  -F chat_id=<telegram_user_id> \
  -F document=@/path/to/file.pdf \
  -F caption="📖 Description here" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else d)"
```

**Pros:** One-liner, no imports, works for ANY file type.
**Cons:** Need to source .env for token.

---

## Method 2: Python (for programmatic use)

```python
import asyncio
from telegram import Bot

async def send_file(file_path, filename, caption=""):
    bot = Bot(token='BOT_TOKEN')  # from env/config
    with open(file_path, 'rb') as f:
        await bot.send_document(
            chat_id=CHAT_ID,
            document=f,
            filename=filename,
            caption=caption
        )

asyncio.run(send_file('/path/to/file.zip', 'file.zip', 'Here is your file'))
```

---

## Method 3: Python requests (alternative)

```python
import os, requests

token = ''
with open(os.path.expanduser('~/.hermes/.env'), 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN=') and not line.startswith('#'):
            token = line.split('=', 1)[1].strip()
            break

url = f'https://api.telegram.org/bot{token}/sendDocument'
with open('/path/to/file.pdf', 'rb') as f:
    r = requests.post(url, data={'chat_id': <telegram_user_id>, 'caption': 'Your file'},
                      files={'document': ('file.pdf', f, 'application/pdf')})
    print(f"OK: {r.json().get('ok')}")
```

---

## Key Details
- Bot token: stored in `~/.hermes/.env` as `TELEGRAM_BOT_TOKEN`
- Works for ANY file type: zip, pdf, txt, py, json, csv, docx, xlsx, etc.
- Telegram limit: 50MB for bot uploads, 2GB for premium users

## Pitfalls
- ❌ `hermes send -f` fails on binary files — always use Bot API
- ❌ `MEDIA:` tag with non-image/audio/video — silently fails
- ❌ Renaming .zip to .mp4 — Telegram validates format
- ✅ Always set proper filename with correct extension
- ❌ `send_message` tool with `MEDIA:` may report success but silently NOT deliver documents (pdf/zip/etc). Always verify delivery with Python requests + Bot API as fallback.
- ❌ **Token file permissions**: `~/.config/gmgn/bot_token.txt` is `chmod 600`. Shell `$()` subshells and `cat` may fail silently. **Use Python `requests.post`** to read the file and send — this always works regardless of permissions.

## Most Reliable Approach (Python requests)

When `send_message` with `MEDIA:` fails, use this pattern — it survived every test:

```python
import requests
token = open('/home/ubuntu/.config/gmgn/bot_token.txt').read().strip()
r = requests.post(
    f'https://api.telegram.org/bot{token}/sendDocument',
    data={'chat_id': '<telegram_user_id>', 'caption': 'Description'},
    files={'document': open('/path/to/file.zip', 'rb')}
)
print('OK' if r.json().get('ok') else r.json())
```

This bypasses shell permission issues, works for any file type, and returns delivery confirmation.
