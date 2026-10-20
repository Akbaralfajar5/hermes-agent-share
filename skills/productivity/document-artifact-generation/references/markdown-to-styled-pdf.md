# Markdown to Styled PDF Conversion

## When to Use
Convert long-form markdown content (summaries, reports, books) into clean, styled PDF documents. Best for Indonesian-language content or any document that needs good typography.

## Method: pandoc + wkhtmltopdf

### Step 1: Convert markdown → styled HTML (with custom CSS)
```bash
pandoc input.md -o output.html --standalone --metadata title="Title Here"
```

### Step 2: Inject custom CSS into the HTML
Use `execute_code` to read the HTML, inject `<style>` block, write back:
```python
css = """
@page { margin: 2cm; size: A4; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; line-height: 1.8; color: #333; padding: 0 40px; }
h1 { color: #1a1a2e; font-size: 22pt; text-align: center; border-bottom: 3px solid #e94560; padding-bottom: 10px; }
h2 { color: #0f3460; font-size: 14pt; border-left: 4px solid #e94560; padding-left: 12px; margin-top: 28px; }
h3 { color: #16213e; font-size: 12pt; }
p { text-align: justify; margin: 6px 0; }
blockquote { border-left: 3px solid #e94560; padding: 10px 15px; color: #555; font-style: italic; background: #f9f9f9; }
strong { color: #0f3460; }
"""
# Inject before </head>
html = html.replace('</head>', f'<style>{css}</style></head>')
```

### Step 3: HTML → PDF via wkhtmltopdf
```bash
wkhtmltopdf --enable-local-file-access --margin-top 20mm --margin-bottom 20mm \
  --margin-left 20mm --margin-right 20mm --encoding UTF-8 --page-size A4 \
  output.html output.pdf
```

## Full Pipeline (execute_code)

```python
from hermes_tools import read_file, write_file, terminal
import re

# Read markdown
result = read_file("input.md")
md = result["content"]

# Build styled HTML
html = """<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><title>Title</title>
<style>
@page { margin: 2cm; size: A4; }
body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.8; color: #333; padding: 0 40px; }
h1 { color: #1a1a2e; font-size: 22pt; text-align: center; border-bottom: 3px solid #e94560; }
h2 { color: #0f3460; font-size: 14pt; border-left: 4px solid #e94560; padding-left: 12px; margin-top: 28px; }
p { text-align: justify; }
blockquote { border-left: 3px solid #e94560; padding: 10px 15px; background: #f9f9f9; }
strong { color: #0f3460; }
</style></head><body>
"""

for line in md.split('\n'):
    s = line.strip()
    if s.startswith('<a id='): continue
    if s.startswith('# ') and not s.startswith('## '): html += f'<h1>{s[2:]}</h1>\n'
    elif s.startswith('## '): html += f'<h2>{s[3:]}</h2>\n'
    elif s.startswith('### '): html += f'<h3>{s[4:]}</h3>\n'
    elif s == '---': html += '<hr>\n'
    elif s.startswith('> '):
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[2:])
        html += f'<blockquote><p>{t}</p></blockquote>\n'
    elif s.startswith('- '):
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[2:])
        html += f'<ul><li>{t}</li></ul>\n'
    elif s:
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
        t = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', t)
        html += f'<p>{t}</p>\n'

html += "</body></html>"
write_file("styled_output.html", html)

# Convert to PDF
terminal("wkhtmltopdf --enable-local-file-access --margin-top 20mm --margin-bottom 20mm --margin-left 20mm --margin-right 20mm --encoding UTF-8 --page-size A4 styled_output.html output.pdf")
```

## Pitfalls
- ❌ `pandoc --pdf-engine=wkhtmltopdf` with `--css` flag fails (blocked file access error) — use the 2-step approach instead
- ❌ `wkhtmltopdf` without `--enable-local-file-access` blocks local CSS/images
- ✅ Always build HTML first, then convert to PDF separately
- ✅ Use `execute_code` for the full pipeline (handles file I/O + terminal in one script)
- ✅ For sending PDF via Telegram, use Bot API `sendDocument` (not `hermes send`)
