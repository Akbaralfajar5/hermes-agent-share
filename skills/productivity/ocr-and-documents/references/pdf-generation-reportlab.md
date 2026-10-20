# PDF Generation with ReportLab

For **creating** PDFs from scratch (not editing existing ones), use `reportlab`.

## Install

```bash
pip install reportlab
```

## Quick Start

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Create document
doc = SimpleDocTemplate(
    "output.pdf",
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm
)

# Get base styles
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=28,
    spaceAfter=20,
    alignment=TA_CENTER,
    textColor=HexColor('#1a1a2e'),
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=11,
    spaceAfter=8,
    alignment=TA_JUSTIFY,
    leading=16  # line height
)

# Build content
story = []
story.append(Paragraph('Document Title', title_style))
story.append(Spacer(1, 1*cm))
story.append(Paragraph('This is body text with <b>bold</b> and <i>italic</i>.', body_style))
story.append(PageBreak())

# Build PDF
doc.build(story)
```

## Common Elements

### Tables

```python
data = [
    ['Header 1', 'Header 2', 'Header 3'],
    ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
    ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3'],
]

table = Table(data, colWidths=[4*cm, 5*cm, 5*cm])
table.setStyle(TableStyle([
    # Header row
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#16213e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('TOPPADDING', (0, 0), (-1, 0), 10),
    # Data rows
    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f5f5f5')),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('TOPPADDING', (0, 1), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    # Grid
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(table)
```

### Bullet Lists

```python
bullet_style = ParagraphStyle(
    'BulletStyle',
    parent=styles['Normal'],
    fontSize=11,
    spaceAfter=6,
    leftIndent=20,
    bulletIndent=10,
    leading=15
)

story.append(Paragraph('• First bullet point', bullet_style))
story.append(Paragraph('• Second bullet point', bullet_style))
story.append(Paragraph('• Third bullet point', bullet_style))
```

### Highlighted/Quote Box

```python
highlight_style = ParagraphStyle(
    'Highlight',
    parent=styles['Normal'],
    fontSize=11,
    spaceAfter=10,
    spaceBefore=10,
    leftIndent=15,
    rightIndent=15,
    backColor=HexColor('#f5f5f5'),
    borderPadding=10,
    leading=16,
    fontName='Helvetica-Oblique'
)

story.append(Paragraph('"This is a highlighted quote or important note."', highlight_style))
```

### Code Block Style

```python
code_style = ParagraphStyle(
    'CodeStyle',
    parent=styles['Normal'],
    fontSize=10,
    spaceAfter=8,
    leftIndent=20,
    fontName='Courier',
    backColor=HexColor('#f0f0f0'),
    leading=14
)

story.append(Paragraph('pip install reportlab', code_style))
```

## Available Fonts (built-in)

- `Helvetica`, `Helvetica-Bold`, `Helvetica-Oblique`, `Helvetica-BoldOblique`
- `Times-Roman`, `Times-Bold`, `Times-Italic`, `Times-BoldItalic`
- `Courier`, `Courier-Bold`, `Courier-Oblique`, `Courier-BoldOblique`

## HTML-like Tags in Paragraphs

ReportLab Paragraph supports basic HTML:
- `<b>bold</b>`
- `<i>italic</i>`
- `<u>underline</u>`
- `<br/>` line break
- `<font color="red">colored text</font>`
- `<font size="14">sized text</font>`

## Page Size Options

```python
from reportlab.lib.pagesizes import A4, letter, legal, A3

# A4 = (595.27, 841.89) points = 21cm x 29.7cm
# letter = (612, 792) points = 8.5" x 11"
```

## Pitfalls

1. **Module not found in execute_code sandbox** — reportlab installs to system Python but execute_code uses isolated env. Use `terminal()` with inline Python instead:
   ```bash
   python3 -c "from reportlab... ; ..."
   ```

2. **Unicode characters** — reportlab's built-in fonts don't support all Unicode. For non-Latin scripts, register TTF fonts:
   ```python
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   pdfmetrics.registerFont(TTFont('NotoSans', '/path/to/NotoSans-Regular.ttf'))
   ```

3. **Long text overflow** — Paragraph auto-wraps, but very long single words may overflow. Use `wordWrap='CJK'` for CJK text.

## When to Use What

| Task | Tool |
|------|------|
| Create PDF from scratch | reportlab |
| Edit existing PDF text | nano-pdf CLI |
| Extract text from PDF | pymupdf / marker-pdf |
| Convert PDF to images | pymupdf |
| Merge/split PDFs | pymupdf |
