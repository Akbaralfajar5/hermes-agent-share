# Telegram File Delivery — Beyond MEDIA: Tag

## Problem

The Hermes `MEDIA:` tag in `send_message` only supports:
- Images: `.png`, `.jpg`, `.webp` → sent as photos
- Audio: `.ogg` → sent as voice bubbles
- Video: `.mp4` → sent inline

**Anything else (`.zip`, `.txt`, `.pdf`, `.py`, `.json`, etc.) silently fails** — returns `"No deliverable text or media remained after processing MEDIA tags"`.

Renaming files (e.g. `.zip` → `.zip.png`) sends the file as a corrupt image, not a document.

## Solution: Direct Bot API via python-telegram-bot

Use the Telegram Bot API `send_document` method directly:

```python
import asyncio
from telegram import Bot

async def send_file(file_path, filename, caption="", chat_id="<telegram_user_id>"):
    """Send any file type as Telegram document."""
    token = "YOUR_BOT_TOKEN"  # From TELEGRAM_BOT_TOKEN in ~/.hermes/.env
    bot = Bot(token=token)
    with open(file_path, 'rb') as f:
        await bot.send_document(
            chat_id=chat_id,
            document=f,
            filename=filename,
            caption=caption
        )

# Usage
asyncio.run(send_file('/path/to/file.zip', 'file.zip', 'Here is the file'))
```

## Inline Script (copy-paste ready for terminal)

```bash
python3 -c "
import asyncio
from telegram import Bot

async def send():
    bot = Bot(token='BOT_TOKEN_HERE')
    with open('FILE_PATH', 'rb') as f:
        await bot.send_document(chat_id=CHAT_ID, document=f, filename='FILENAME', caption='CAPTION')

asyncio.run(send())
print('SENT!')
"
```

## Key Details

- `python-telegram-bot` package is already installed in Hermes venv
- Bot token: read from `~/.hermes/.env` → `TELEGRAM_BOT_TOKEN`
- Chat ID: user's Telegram chat ID (from gateway config)
- Works for ALL file types: zip, txt, pdf, py, json, csv, xlsx, etc.
- Max file size: 50MB (Telegram Bot API limit)
- For files >50MB: use `bot.send_document` with `local_mode=True` (requires local bot API server) or split the file

## When to Use

- User asks "kirim file" / "send me the file" / "transfer file ke gw"
- MEDIA: tag returns the "No deliverable text or media" error
- Need to deliver scripts, archives, documents, or any non-image/audio/video file
- Always try MEDIA: first (faster, integrated), fall back to Bot API for non-media files
