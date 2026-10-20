#!/usr/bin/env python3
"""
Generate a consolidated PDF combining Ponyin Trading Intel (ponyin.id) with the
Charon repo configuration, for offline study or hand-off.

Usage:
    /usr/bin/python3 scripts/generate_ponyin_charon_pdf.py [output.pdf]

IMPORTANT: Use /usr/bin/python3 (system Python with `pip install --user reportlab`),
NOT Hermes' venv `python3` (different Python version, won't see ~/.local packages).
See SKILL.md "Pitfalls" section.

The text content is embedded inline so this script is self-contained — re-run any
time the source material at ponyin.id changes (re-scrape, paste in TOPICS).
"""
import os
import re
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# Output path
OUT = sys.argv[1] if len(sys.argv) > 1 else "Ponyin_x_Charon_Consolidation.pdf"

# Styling
GOLD = HexColor("#d4af37")
DARK = HexColor("#0f0f14")
INK = HexColor("#1a1a22")
ACCENT = HexColor("#5b6cff")
MUTED = HexColor("#6b7280")
CODEBG = HexColor("#f5f5f7")

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "titulo", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=28, textColor=DARK, leading=34, alignment=TA_CENTER, spaceAfter=10,
)
subtitle_style = ParagraphStyle(
    "subtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=13, textColor=MUTED, alignment=TA_CENTER, spaceAfter=30, leading=18,
)
h1 = ParagraphStyle(
    "h1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=20, textColor=DARK, leading=26, spaceBefore=18, spaceAfter=10,
)
h2 = ParagraphStyle(
    "h2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=15, textColor=INK, leading=20, spaceBefore=12, spaceAfter=8,
)
h3 = ParagraphStyle(
    "h3", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=12, textColor=ACCENT, leading=16, spaceBefore=8, spaceAfter=4,
)
body = ParagraphStyle(
    "body", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, textColor=INK, leading=15.5, alignment=TA_JUSTIFY, spaceAfter=6,
)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=3)
code = ParagraphStyle(
    "code", parent=styles["Code"], fontName="Courier", fontSize=9,
    textColor=INK, leading=12, backColor=CODEBG, borderPadding=6,
    leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=6,
)
quote = ParagraphStyle(
    "quote", parent=body, fontName="Helvetica-Oblique", textColor=MUTED,
    leftIndent=16, rightIndent=16, spaceBefore=4, spaceAfter=8,
)


def para_text(text):
    """Convert raw plaintext (with optional ```code``` blocks, bullets, **bold**,
    `inline-code`) into a list of reportlab flowables."""
    parts = []
    in_code = False
    code_buf = []
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            if in_code:
                rendered = "<br/>".join(
                    (c or " ").replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;")
                    for c in code_buf
                )
                parts.append(Paragraph(rendered, code))
                code_buf, in_code = [], False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(ln)
            continue
        s = ln.strip()
        if not s:
            parts.append(Spacer(1, 4))
            continue
        if s.startswith('"') and s.endswith('"') and len(s) > 20:
            parts.append(Paragraph(s.replace("<", "&lt;").replace(">", "&gt;"), quote))
            continue
        if s.startswith("- ") or s.startswith("* "):
            parts.append(Paragraph("• " + s[2:].replace("<", "&lt;").replace(">", "&gt;"), bullet))
            continue
        if s[:2] in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.") and s[2:3] in (" ", ")"):
            parts.append(Paragraph(s.replace("<", "&lt;").replace(">", "&gt;"), bullet))
            continue
        if s.isupper() and len(s) < 80 and not s.endswith("."):
            parts.append(Paragraph(s, h3))
            continue
        safe = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"`([^`]+)`", r'<font name="Courier" size="9.5">\1</font>', safe)
        parts.append(Paragraph(safe, body))
    if in_code and code_buf:
        rendered = "<br/>".join((c or " ").replace(" ", "&nbsp;") for c in code_buf)
        parts.append(Paragraph(rendered, code))
    return parts


# ---------------------------------------------------------------------------
# CONTENT — keep sections short. Full Ponyin lessons live in
# `references/ponyin-trading-intel.md`. Mapping detail in
# `references/ponyin-gap-analysis.md`. This PDF is for hand-off / printing.
# ---------------------------------------------------------------------------

OVERVIEW = """
Charon (github.com/yunus-0x/charon) is a Telegram-controlled Solana meme coin
trading bot that screens Pump.fun token flow against strategy filters and
optionally a small LLM, then routes buys through dry_run / confirm / live modes.

This document consolidates the Ponyin Trading Intel (ponyin.id) lessons with the
Charon configuration surface, listing for each lesson:
- the corresponding Charon parameter (if any), and
- the gap (if Charon does not implement that lesson).

Full lesson text is preserved in the skill reference
`references/ponyin-trading-intel.md`. The mapping table and patch opportunities
are in `references/ponyin-gap-analysis.md`.
"""

PLAYBOOK = """
RECOMMENDED `/stratset` PLAYBOOK (Ponyin-faithful sniper)

```
/stratset sniper tp_percent 50
/stratset sniper sl_percent -25
/stratset sniper partial_tp true
/stratset sniper partial_tp_at_percent 35
/stratset sniper partial_tp_sell_percent 35
/stratset sniper trailing_enabled true
/stratset sniper trailing_percent 25
/stratset sniper max_top20_holder_percent 85
/stratset sniper trending_max_bundler_rate 0.35
/stratset sniper trending_max_rug_ratio 0.25
/stratset sniper min_gmgn_total_fee_sol 15
/stratset sniper min_saved_wallet_holders 1
```

CABAL WALLET REGISTRATION

```
/walletadd cupsey  <address>
/walletadd cented  <address>
/walletadd log     <address>
/walletadd decu    <address>
/walletadd marcel  <address>
/walletadd duvel   <address>
```

GAPS TO PATCH (see references/ponyin-gap-analysis.md for code path):
- BAB 3: mint/freeze authority check (no direct Charon equivalent)
- BAB 6: 10% mark position (Charon buys full size in one shot)
- A6 : rent refund auto-close after position exit
- A7 filter 1: gas fee gate
- A7 filter 2: funded wallet age detection
"""


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Ponyin x Charon Consolidation",
    )
    story = []

    # Cover
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("PONYIN TRADING INTEL", title_style))
    story.append(Paragraph(
        "x CHARON CONSOLIDATION",
        ParagraphStyle("cover2", parent=title_style, fontSize=20, textColor=GOLD),
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Audit ponyin.id (Vol.1 + Vol.2 Advance) mapped to Charon bot configuration",
        subtitle_style,
    ))
    story.append(PageBreak())

    # Overview
    story.append(Paragraph("Overview", h1))
    for p in para_text(OVERVIEW):
        story.append(p)
    story.append(PageBreak())

    # Playbook
    story.append(Paragraph("Action Playbook", h1))
    for p in para_text(PLAYBOOK):
        story.append(p)
    story.append(PageBreak())

    # Pointer to live references
    story.append(Paragraph("Source Material", h1))
    story.append(Paragraph(
        "Authoritative scraped Ponyin lessons are kept in the Hermes skill at "
        "<font name='Courier'>~/.hermes/skills/trading/charon-trading-bot/"
        "references/ponyin-trading-intel.md</font> — that file is the canonical "
        "knowledge bank, updated when ponyin.id changes.",
        body,
    ))
    story.append(Paragraph(
        "Gap analysis + patch opportunities: "
        "<font name='Courier'>references/ponyin-gap-analysis.md</font>",
        body,
    ))

    doc.build(story)
    print(f"PDF generated: {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    build()
