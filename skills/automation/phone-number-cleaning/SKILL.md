---
name: phone-number-cleaning
description: >
  Clean, deduplicate, and format Indonesian phone numbers from raw dumps.
  Strips timestamps, numbering prefixes, invalid markers (❌🔴🔁), non-phone junk,
  and outputs clean number-only lists grouped per the size stated in that request
  (observed: 10 and 40; default 40 when unstated).
---

# Phone Number Cleaning

## Triggers
- Phone dumps with timestamps/numbering/emoji
- "bersihin nomor", "clean numbers", "format nomor"
- Raw WhatsApp/Telegram chat exports with phone numbers
- Indonesian phone number lists (08xx, 08x, 8x prefix)

## Input Format

Raw dumps can contain:
- Timestamps: `[7/22/2026 11:55 AM] the user: `
- Number prefixes: `1 `, `2 `, `10 `
- Invalid markers: ❌, 🔴, 🔁
- Non-phone junk text
- Mixed format: `58-4629-1844`, `+62 8xx`

## Cleaning Pipeline

1. **Strip wrapping** — Remove timestamps, sender names, emoji markers (❌, 🔴, 🔁)
2. **Strip numbering** — Remove line-number prefixes (`1 `, `10 `, `28 `)
3. **Extract numbers** — Keep only valid Indonesian phone digits (08xx, 8xx, 9xx prefix, 10-13 digits)
4. **Deduplicate** — Remove duplicates within each batch
5. **Format** — One number per line, NO spaces, NO blank lines between numbers
6. **Group** — Every 20 numbers, add one blank line separator

## Valid Indonesian Prefixes
- `08` — Standard mobile (08xxxxxxxxxx, 08xxxxxxxxxxx)
- `8` — Without leading 0 (8xxxxxxxxxx) → **normalize by prepending 0** → `08xxxxxxxxxx`
- `9` — Alternative prefix (9xxxxxxxxx) → **normalize by prepending 0** → `09xxxxxxxxx`

Normalization rule: any number starting with `8` or `9` (9-11 digits, no leading 0) gets a `0` prepended so the whole list is consistent `08xx`/`09xx`. Verified Aug 2026: `89682386509` → `089682386509`, `85833453369` → `085833453369`, `8812050620` → `08812050620`. User did not object.

## Output Format

**Group size is whatever the user says IN THAT REQUEST — read it every time, never assume.**
The user varies it: "per 40 spasi" on some batches, "per 10 spasi" on others. Both are correct
and neither is a default. If the request carries no group instruction at all, use **40**.

Observed sizes: **10** (37-number batch, Sep 2026 — "per 10 spasi") and **40** (the older
habit). Treat any stated size as authoritative for that batch only; do not carry it forward to
the next request.

```
085706036693
085805257014
... (up to N)

085137211887
081239252550
... (next group)
```

No spaces. No commas. No quotes. Just numbers. Blank line at the requested group boundary.

**Trailing partial group:** when the total is not a multiple of N (e.g. 37 numbers at N=10),
output the final 7 numbers and do NOT append a trailing blank line. Report the count in the
reply (e.g. "37 nomor, per 10 spasi") so the user can confirm the boundary without counting.

## Pitfalls

- **Group boundary is exact** — Count the cleaned numbers, not the original line labels. Place one blank line after each Nth number at the size the user asked for; do not insert a blank line earlier or carry a previous batch's size forward.
- **Flag short numbers instead of silently passing them** — Indonesian mobiles are 11–13 digits. A number that comes out 10 digits after stripping (e.g. `08212821320`, `08212823229` in a Sep 2026 batch) is genuinely truncated in the source, not a cleaning error. Keep it in the list AND call it out separately in the reply ("2 nomor kependekan"), so the user can check the original dump. Do not drop it and do not pad it.
- **Strip markers, keep numbers** — A line like `083869384207❌` or `081234336539 X` keeps the number, drops the marker. Strip trailing `❌`/`🔴`/`🔁`/` X` (with or without a space) and output the bare number. (Verified Aug 2026 — user wants the number retained, marker is just a status annotation.)
- **Normalize missing leading 0** — Numbers like `85833453369` (starts with 8/9, no leading 0) are valid but should be normalized to `085833453369` by prepending 0. Don't drop them; prepend.
- **No wrapping** — Don't add backticks, code blocks, or quotes around output. Raw numbers only.
- **One response** — Clean and output in ONE turn. Don't batch-process across multiple responses.
