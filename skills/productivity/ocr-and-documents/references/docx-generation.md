# Generating Academic .docx Files with python-docx

## When to Use

- User asks for a corrected/revised document back in Word format
- Generating skripsi/thesis chapters, academic papers, or formal reports
- Converting reviewed text into properly formatted .docx

## Critical: Use System Python

```bash
# ALWAYS use system python, not the Hermes venv
/usr/bin/python3 -m pip install python-docx -q
/usr/bin/python3 /path/to/script.py
```

The Hermes venv python often has lxml import errors or missing pip.

## Workflow Pattern

1. **Read** the user's uploaded .docx to extract content and understand structure
2. **Review** content for corrections (grammar, structure, completeness)
3. **Write** a Python script to a file (avoid inline `-c` for long scripts — bash quoting breaks)
4. **Execute** with `/usr/bin/python3 script.py`
5. **Send** the generated file back to the user

## Academic Formatting Standards (Indonesian Skripsi/Thesis)

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Margins: 4cm top, 3cm bottom, 4cm left, 3cm right
for section in doc.sections:
    section.top_margin = Cm(4)
    section.bottom_margin = Cm(3)
    section.left_margin = Cm(4)
    section.right_margin = Cm(3)

# Font: Times New Roman 12pt
# Line spacing: 1.5 (value=360 in openxml)
# First line indent: 1.27cm
# Alignment: Justify for body text
```

## Line Spacing Helper

```python
def set_line_spacing(paragraph, spacing=360):
    """360 = 1.5 lines, 480 = double, 240 = single"""
    pPr = paragraph._p.get_or_add_pPr()
    spacing_elem = OxmlElement('w:spacing')
    spacing_elem.set(qn('w:line'), str(spacing))
    spacing_elem.set(qn('w:lineRule'), 'auto')
    pPr.append(spacing_elem)
```

## Standard BAB I Structure (Indonesian Academic)

A complete BAB I (Pendahuluan) should contain:
1. Latar Belakang Penelitian
2. Identifikasi Masalah
3. Rumusan Masalah
4. Tujuan Penelitian
5. Manfaat Penelitian (Teoritis + Praktis)
6. Batasan Masalah
7. Definisi Operasional
8. Struktur Organisasi Skripsi

Common issues in student drafts:
- Missing "Identifikasi Masalah" (bridge between background and research questions)
- Missing "Batasan Masalah" (scope limitation)
- Missing "Definisi Operasional" (key term definitions)
- Missing "Struktur Organisasi Skripsi" (chapter outline)
- Inconsistent abbreviation usage (spell out first, then abbreviate)
- No sub-section numbering (1.1, 1.2, etc.)

## Pitfall: Long Scripts and Bash Quoting

Never pass long python-docx scripts via `python3 -c "..."` — triple quotes, parentheses, and docstrings break bash parsing. Always:
1. Write script to a `.py` file with `write_file`
2. Execute with `/usr/bin/python3 /path/to/script.py`

## Sending the File

After generating, send via the platform's file-sending mechanism:
```
send_message(message="MEDIA:/path/to/file.docx", target="telegram", action="send")
```
