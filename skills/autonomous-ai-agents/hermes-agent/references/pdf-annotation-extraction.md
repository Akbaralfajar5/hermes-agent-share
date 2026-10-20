# PDF Annotation Extraction (pymupdf)

Use when: user sends a PDF with dosen/reviewer comments and asks to extract or integrate them.

## Key Pitfall: Python Environment

Hermes venv (`~/.hermes/hermes-agent/venv/bin/python3`) may NOT have `fitz`/pymupdf.
Always use `/usr/bin/python3` which has it system-wide:

```bash
/usr/bin/python3 -c "import fitz; print('ok')"
```

If missing: `sudo pip3 install pymupdf` or `/usr/bin/python3 -m pip install pymupdf`

## Extract All Annotations with Text

```python
import fitz

doc = fitz.open("file.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    for annot in page.annots():
        info = annot.info
        content = info.get("content", "").strip()
        atype = annot.type[1]  # e.g. "Highlight", "Ink", "FreeText"
        if content:
            print(f"Hal {page_num+1} | {atype} | {content}")
```

## Annotation Types

| Type | Meaning | Has text? |
|---|---|---|
| `Highlight` | Yellow highlight + optional comment | Sometimes |
| `Ink` | Freehand drawing/underline | Rarely (subject field only) |
| `FreeText` | Sticky note / text box | Yes |
| `StrikeOut` | Strikethrough | Sometimes |
| `Squiggly` | Wavy underline | Rarely |

**Ink annotations** from Indonesian dosen typically = visual marks during seminar, no extractable text. Only `Highlight` with `content` field has actual comments.

## Check What Types Exist First

```python
from collections import Counter
doc = fitz.open("file.pdf")
types = Counter()
for page_num in range(len(doc)):
    for annot in doc[page_num].annots():
        content = annot.info.get("content", "").strip()
        types[f"{annot.type[1]}{'(text)' if content else ''}"] += 1
print(types)
# Example: Counter({'Highlight': 150, 'Highlight(text)': 32, 'Ink': 29})
```

## Get Page Text Around Ink Marks (when no comment text)

```python
ink_pages = set()
for page_num in range(len(doc)):
    for annot in doc[page_num].annots():
        if annot.type[1] == "Ink":
            ink_pages.add(page_num)

for page_num in sorted(ink_pages):
    text = doc[page_num].get_text().strip()
    print(f"--- HAL {page_num+1} ---")
    print(text[:600])
```
