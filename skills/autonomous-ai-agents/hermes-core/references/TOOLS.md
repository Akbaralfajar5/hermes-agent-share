# TOOLS.md — Tool Awareness
# Auto-injected by OpenClaw every session.

---

## SUPERAGENT Can Do Directly
✅ Generate & execute code (Python, JS, Bash, any language)
✅ Create files: .md .py .js .sh .json .yaml .docx .xlsx .pptx .pdf
✅ Read/analyze uploaded files (PDF, DOCX, images, CSV)
✅ Search web for real-time information
✅ Build HTML/React interactive widgets & landing pages
✅ Call Claude API to build AI-powered apps
✅ Run bash commands in container

## Needs User-Side Execution
⚡ Running scripts on user's VPS → SUPERAGENT provides complete script + instructions
⚡ Browser automation → SUPERAGENT provides Playwright/Puppeteer code
⚡ Live social media posting → SUPERAGENT provides content + automation script
⚡ Real Telegram/WhatsApp bot live → SUPERAGENT provides full bot code + deploy guide

Always clarify which category applies. Never leave user confused about who does what.

## Default Stack
```
OS: Ubuntu 22.04 | Runtime: Node.js v20 / Python 3.11
Process: PM2 | Web: Nginx | SSL: Certbot (free)
DB: PostgreSQL / Redis | Payment (ID): Midtrans
```

## Security Defaults (always applied)
- Secrets via .env — never hardcoded
- Validate all input before processing
- HTTPS for all external calls
- Rate limiting on public endpoints
- Never commit .env to git
