# Sending Files via Telegram Bot API

**Discovered:** May 26, 2026

## Problem

The `send_message` tool with `MEDIA:/path/to/file` prefix doesn't reliably send files as attachments — sometimes sends as text only.

## Solution

Use `curl` directly to Telegram Bot API:

```bash
BOT_TOKEN="<from .env>"
CHAT_ID="<home channel>"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
  -F "chat_id=${CHAT_ID}" \
  -F "document=@/path/to/file.py" \
  -F "caption=Description of file"
```

## When to Use

- Sending source code files (.py, .js, .ts)
- Sending documents (.docx, .pdf)
- Sending any file that needs to be received as a downloadable attachment

## Notes

- Use `sendDocument` for files, `sendPhoto` for images
- Files must exist on disk (not URLs)
- Caption is optional but helpful
- Check `~/.hermes/.env` for `TELEGRAM_BOT_TOKEN`
- Home channel is typically `<telegram_user_id>` (check with `send_message(action='list')`)
