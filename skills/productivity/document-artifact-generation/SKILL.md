---
name: document-artifact-generation
description: "Generate actual file artifacts — DOCX proposals, XLSX trackers with formulas, PPTX decks, PDF with hyperlinks, batch file ops, image processing. Always render the real file, not a preview."
version: 1.0.0
author: Hermes (adapted from SUPERAGENT v3 m8)
license: MIT
metadata:
  hermes:
    tags: [docx, xlsx, pptx, pdf, document, export, artifact, proposal, deck, report]
---

# Document & Artifact Generation

Load when: PDF, DOCX, XLSX, PPTX, generate file, dokumen, export, proposal, deck, report, invoice.

Structured output specialist. When a format is requested → render the actual artifact, not a preview.

---

## Render Targets

| Format | Use case | Library |
|--------|----------|---------|
| `.docx` | Proposals, contracts, briefs | python-docx |
| `.xlsx` | Trackers, models, budgets | openpyxl / xlsxwriter |
| `.pptx` | Decks, pitches | python-pptx |
| `.pdf` | Final delivery, invoices, certificates | reportlab |
| `.csv` | Data export | csv stdlib / pandas |
| `.html` | Reports w/ styling, landing pages | direct emit / jinja2 |

---

## DOCX Template

```python
from docx import Document
from docx.shared import Pt, RGBColor

doc = Document()
title = doc.add_heading('Proposal — Project X', level=0)

doc.add_paragraph('Executive summary:')
p = doc.add_paragraph()
p.add_run('Key benefit. ').bold = True
p.add_run('Detail in same paragraph.')

doc.add_heading('Investment', level=1)
table = doc.add_table(rows=1, cols=3)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
hdr[0].text, hdr[1].text, hdr[2].text = 'Tier', 'Price', 'Includes'
for tier, price, inc in [('Entry', 'IDR 500K', 'Basic'), ('Core', 'IDR 2.5M', 'Standard'), ('Premium', 'IDR 8M', 'Full')]:
    row = table.add_row().cells
    row[0].text, row[1].text, row[2].text = tier, price, inc

doc.save('proposal-projectx.docx')
```

---

## XLSX Template (with formulas + formatting)

> **Tip**: Prefer `execute_code` over `terminal` for openpyxl scripts — it resolves the correct Python environment automatically. If using terminal, verify `python3 -c "import openpyxl"` works first; if not, `pip3 install openpyxl` (system pip, not venv pip).

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Summary'

headers = ['Date', 'Channel', 'Revenue (IDR)', 'Conversion %']
ws.append(headers)
for c in ws[1]:
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='2E5BBA')
    c.alignment = Alignment(horizontal='center')

data = [
    ('2026-05-01', 'IG',     1_200_000, 3.2),
    ('2026-05-02', 'TikTok', 2_400_000, 2.1),
]
for row in data:
    ws.append(row)

# Formula at bottom
ws['C5'] = '=SUM(C2:C4)'
ws['C5'].font = Font(bold=True)

# Column widths
for col, w in zip('ABCD', [12, 12, 16, 14]):
    ws.column_dimensions[col].width = w

wb.save('revenue-may2026.xlsx')
```

---

## PPTX Template

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)  # 16:9

# Title slide
s = prs.slides.add_slide(prs.slide_layouts[0])
s.shapes.title.text = 'Project X'
s.placeholders[1].text = 'Q3 2026 Pitch'

# Content slide
s = prs.slides.add_slide(prs.slide_layouts[1])
s.shapes.title.text = 'Why now?'
tf = s.placeholders[1].text_frame
for i, point in enumerate(['Market timing', 'Distribution unlock', 'Cost collapse']):
    p = tf.add_paragraph() if i else tf.paragraphs[0]
    p.text = point
    p.font.size = Pt(28)

prs.save('pitch-projectx.pptx')
```

---

## PDF with Clickable Hyperlinks (ReportLab)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor

doc = SimpleDocTemplate('directory.pdf', pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm)
styles = getSampleStyleSheet()
link_style = ParagraphStyle('Link', parent=styles['Normal'],
                            textColor=HexColor('#2E5BBA'), fontSize=11)

flow = [Paragraph('<b>Project Directory</b>', styles['Title']), Spacer(1, 12)]
for name, url in [('Project A', 'https://a.xyz'), ('Project B', 'https://b.xyz')]:
    flow.append(Paragraph(f'<a href="{url}">{name}</a> — {url}', link_style))
    flow.append(Spacer(1, 4))

doc.build(flow)
```

---

## Batch File Operations

```python
import shutil
from pathlib import Path

src = Path('input')
dst = Path('output'); dst.mkdir(exist_ok=True)

for f in src.glob('**/*.pdf'):
    rel = f.relative_to(src)
    target = dst / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, target)
    print(f'✅ {rel}')
```

---

## Image Processing (Pillow + rembg)

```python
from PIL import Image, ImageOps
from rembg import remove

# Background removal
with open('input.jpg', 'rb') as fi, open('cutout.png', 'wb') as fo:
    fo.write(remove(fi.read()))

# Resize for Twitter avatar (400x400)
img = Image.open('cutout.png').convert('RGBA')
img = ImageOps.fit(img, (400, 400), Image.LANCZOS)
img.save('avatar.png', optimize=True)
```

---

## Structural Templates

### Proposal
```
1. Executive summary (1 paragraph)
2. Problem
3. Solution
4. Timeline
5. Investment (3 tiers, anchor on premium)
6. Proof / case studies
7. Next step (specific, dated)
```

### Insight report
```
1. Executive summary (1 paragraph)
2. Method
3. Findings (3–7 bullets)
4. Analysis
5. Prescriptions (exactly 3, specific, dated)
6. Appendix
```

---

## Render Protocol

```
1. Confirm scope (max 1 clarifying exchange)
2. Generate artifact
3. Save to output path with descriptive filename
4. Deliver file to user
5. Offer: "Adjust [specific section]?"
```

## Pitfalls (DOCX Image Manipulation)

### ❌ NEVER replace all images with the same file
When iterating `doc.paragraphs` to find and replace an image, do NOT write the same blob to every image relationship. This corrupts ALL images (cover logo, diagrams, charts all become the same file).

```python
# WRONG — replaces every image with the same file
for i, p in enumerate(paras):
    for run in p.runs:
        for drawing in run._element.findall('.//' + qn('w:drawing')):
            for blip in drawing.findall('.//' + qn('a:blip')):
                embed = blip.get(qn('r:embed'))
                rel = doc.part.rels.get(embed)
                rel.target_part._blob = new_image_data  # ❌ ALL images become this
```

```python
# CORRECT — only replace the specific target image
TARGET_PARA_IDX = 228  # Only the paragraph with the image to replace
p = paras[TARGET_PARA_IDX]
for run in p.runs:
    for drawing in run._element.findall('.//' + qn('w:drawing')):
        for blip in drawing.findall('.//' + qn('a:blip')):
            embed = blip.get(qn('r:embed'))
            rel = doc.part.rels.get(embed)
            rel.target_part._blob = new_image_data  # ✅ Only this one
```

### ❌ Paragraph indices shift after section removal
When you remove paragraphs (e.g., deleting Section 2.5), ALL subsequent paragraph indices change. Position-based image matching breaks.

**Fix**: Use context-based matching instead of index-based:
```python
# Build a context signature for each image (surrounding text)
# Match by context, not by index
def get_context(paras, idx):
    return [paras[j].text.strip()[:60] for j in range(max(0,idx-3), min(len(paras),idx+4)) if paras[j].text.strip()]
```

### ✅ Always verify after image operations
After any image replacement, verify:
1. All images have **unique** file sizes (if sizes are identical → corruption)
2. Cover/logo image is small (<50KB typically)
3. Use `vision_analyze` to spot-check one image from each section

### ✅ Preserve original images for rollback
Before any image edit, save originals:
```python
originals = {}
for i, p in enumerate(paras):
    for run in p.runs:
        for drawing in run._element.findall('.//' + qn('w:drawing')):
            for blip in drawing.findall('.//' + qn('a:blip')):
                embed = blip.get(qn('r:embed'))
                rel = doc.part.rels.get(embed)
                if rel and hasattr(rel, 'target_part'):
                    originals[i] = rel.target_part.blob  # Save original
```

## Pitfalls (Telegram File Delivery)

### `send_message` MEDIA tag ONLY works for images/audio/video
`.docx`, `.zip`, `.pdf`, `.xlsx` files sent via `MEDIA:/path` in `send_message` will appear as text-only (no file attached). The MEDIA tag is designed for media types, not documents.

**⚠️ `hermes send -t telegram -f file.xlsx` FAILS for binary files** with `'utf-8' codec can't decode byte` error. Do NOT use `hermes send` for .docx/.xlsx/.pdf/.zip — it tries to read them as UTF-8 text.

**PRIMARY method: Terminal curl (simplest, always works)**:
```bash
# Read token and chat_id, then send document
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | grep -v '^#' | cut -d= -f2 | tr -d '"' | tr -d "'")
CHAT_ID=$(grep TELEGRAM_HOME_CHANNEL ~/.hermes/.env | grep -v '^#' | cut -d= -f2 | tr -d '"' | tr -d "'")

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
  -F chat_id="${CHAT_ID}" \
  -F document=@"/path/to/file.docx" \
  -F caption="📄 Caption text"

# For images, use /sendPhoto instead:
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto" \
  -F chat_id="${CHAT_ID}" \
  -F photo=@"/path/to/image.png" \
  -F caption="Caption text"
```

**Alternative: Python requests** (for use inside `execute_code`):
```python
import os, requests
token = ''
with open(os.path.expanduser('~/.hermes/.env'), 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN=') and not line.startswith('#'):
            token = line.split('=', 1)[1].strip()
            break
chat_id = ''
with open(os.path.expanduser('~/.hermes/.env'), 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_HOME_CHANNEL=') and not line.startswith('#'):
            chat_id = line.split('=', 1)[1].strip()
            break
url = f'https://api.telegram.org/bot{token}/sendDocument'
with open('/path/to/file.docx', 'rb') as f:
    files = {'document': ('filename.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    data = {'chat_id': chat_id, 'caption': 'Caption text'}
    r = requests.post(url, files=files, data=data)
    print(f"Status: {r.status_code}, OK: {r.json().get('ok')}")
```

### `hermes send` does NOT work for binary files
`hermes send -t telegram -f file.xlsx` will fail with UTF-8 decode error. Always use the curl or Bot API approach above.

### ⚠️ Sending pattern: do NOT mix text and MEDIA: for documents
When `send_message` with `MEDIA:` tag fails, don't retry with text+MEDIA (same mechanism, same failure). Switch immediately to direct Bot API curl. The `MEDIA:` tag is processed by the gateway, which only handles image/audio/video natively — documents need the raw Telegram API.

## Pitfalls (Google Apps Script)

### `SpreadsheetApp.getUi()` only works in spreadsheet-bound scripts
Standalone scripts at script.google.com cannot use `SpreadsheetApp.getUi()`. It throws a reference error.

**Fix**: Use `Logger.log()` to output links, then tell user to check **View → Execution Log**.
Or save output to Drive: `DriveApp.createFile('output.txt', content)`.

## Pitfalls (DOCX Section Restructuring)

### Workflow for reorganizing sections in existing .docx
When restructuring a section (e.g., splitting dense content into numbered subsections):

1. **Extract existing data first** — read all tables and paragraphs in the section
2. **Remove old elements** — iterate `body` children, collect elements between heading markers, then `body.remove(elem)`
3. **Build new elements** — create heading/paragraph/table elements with OxmlElement
4. **Insert after the section heading** — use `heading.addnext(elem)` chain
5. **Add table captions** — insert caption + source paragraphs around each table
6. **Match existing table style** — inspect existing tables FIRST (see `references/docx-table-styling-oxml.md`)
7. **Verify** — re-read the document to confirm element order and table count

### Finding section boundaries
```python
in_section = False
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'p':
        full_text = ''.join(r.text or '' for r in child.iter(qn('w:t')))
        if '4.2 Heading Text' in full_text:
            in_section = True
        if '4.3 Next Heading' in full_text:
            break
    if in_section:
        elements_to_remove.append(child)
```

### Inserting elements in order
```python
current = heading_element
for elem in new_elements:
    current.addnext(elem)
    current = elem  # chain: each new element goes after the previous
```

## Linked References
- **references/xlsx-statistical-analysis-template.md** — Multi-sheet paired t-test Excel template (pre-post design, formulas, styling)
- **references/docx-table-styling-oxml.md** — OxmlElement table styling patterns
- **references/python-docx-numbering-preservation.md** — Numbered list preservation
- **references/docx-seminar-speaker-script.md** — DOCX speaker script generation from presentations: timed scripts, anticipated dosen questions, tips
- **references/markdown-to-styled-pdf.md** — pandoc + wkhtmltopdf pipeline for converting long markdown to styled PDF (Indonesian-friendly typography)

## Constraints

- Render the ACTUAL artifact — inline preview is not a deliverable
- Filenames descriptive: `q3-revenue-analysis.xlsx` not `output.xlsx`
- One specific edit offer after delivery, not generic "any changes?"
- For multi-file deliverables: bundle into zip when > 3 files
