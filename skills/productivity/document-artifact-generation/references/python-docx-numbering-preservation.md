# Python-docx: Preserving Numbering When Copying Paragraphs

## Problem
When copying paragraphs from one Document to another using python-docx, the numbering format (bullets, numbered lists) is lost even if you copy the text and style correctly.

```python
# ❌ WRONG — numbering disappears
p_new = doc.add_paragraph(para_old.text, style=para_old.style)
```

## Root Cause
Numbering is stored in the paragraph's XML properties (`pPr` element) under a `numPr` (numbering properties) child node. Simply copying text and style does not copy this XML structure.

## Solution
Deep-copy the `numPr` element from source to destination:

```python
from copy import deepcopy

# Copy the paragraph
p_new = doc.add_paragraph(para_old.text, style=para_old.style)

# Copy numbering if it exists
pPr_old = para_old._element.pPr
if pPr_old is not None:
    numPr_old = pPr_old.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr')
    if numPr_old is not None:
        pPr_new = p_new._element.get_or_add_pPr()
        numPr_new = deepcopy(numPr_old)
        pPr_new.append(numPr_new)
```

## Additional Setup
If copying from a document with custom numbering definitions, also copy the numbering part:

```python
# Copy numbering definitions from source to destination
if doc_source.part.numbering_part:
    doc_dest.part.relate_to(
        doc_source.part.numbering_part,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering'
    )
```

## Pitfalls
- **Duplicate numbering.xml warning:** If you relate to the numbering part after already adding paragraphs, you may see a warning about duplicate names. This is harmless but can be avoided by relating to the numbering part BEFORE adding any paragraphs.
- **Namespace:** The namespace URI is required in the `find()` call — do not omit it or the search will fail silently.
- **Order matters:** Copy numbering definitions first, then copy paragraphs with their `numPr` elements.

## Example: Full Workflow
```python
from docx import Document
from copy import deepcopy

doc_source = Document('source.docx')
doc_dest = Document()

# Step 1: Copy numbering definitions
if doc_source.part.numbering_part:
    doc_dest.part.relate_to(
        doc_source.part.numbering_part,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering'
    )

# Step 2: Copy paragraphs with numbering
for para_old in doc_source.paragraphs:
    p_new = doc_dest.add_paragraph(para_old.text, style=para_old.style)
    p_new.alignment = para_old.alignment
    
    # Copy numbering
    pPr_old = para_old._element.pPr
    if pPr_old is not None:
        numPr_old = pPr_old.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr')
        if numPr_old is not None:
            pPr_new = p_new._element.get_or_add_pPr()
            numPr_new = deepcopy(numPr_old)
            pPr_new.append(numPr_new)

doc_dest.save('dest.docx')
```
