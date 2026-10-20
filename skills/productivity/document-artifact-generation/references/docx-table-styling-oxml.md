# DOCX Table Styling with OxmlElement (Matching Existing Document Style)

When creating tables in an existing .docx that already has styled tables, you MUST match the existing style. Use `python-docx` OxmlElement to inspect and replicate.

## Step 1: Extract Existing Table Style

```python
from docx import Document
from docx.oxml.ns import qn

doc = Document('file.docx')
table = doc.tables[TABLE_IDX]
tbl_elem = table._tbl

# Get header shading color
first_row = tbl_elem.findall(qn('w:tr'))[0]
first_tc = first_row.findall(qn('w:tc'))[0]
tcPr = first_tc.find(qn('w:tcPr'))
shd = tcPr.find(qn('w:shd'))
fill = shd.get(qn('w:fill'))  # e.g. '4472C4' (blue)

# Get header text color
p = first_tc.find(qn('w:p'))
r = p.find(qn('w:r'))
rPr = r.find(qn('w:rPr'))
color = rPr.find(qn('w:color'))
text_color = color.get(qn('w:val'))  # e.g. 'FFFFFF' (white)

# Get borders
tblPr = tbl_elem.find(qn('w:tblPr'))
tblBorders = tblPr.find(qn('w:tblBorders'))
for border in tblBorders:
    bname = border.tag.split('}')[-1]
    print(f'{bname}: val={border.get(qn("w:val"))}, sz={border.get(qn("w:sz"))}, color={border.get(qn("w:color"))}')

# Check tblLook
tblLook = tblPr.find(qn('w:tblLook'))
print(f'firstRow={tblLook.get(qn("w:firstRow"))}, noHBand={tblLook.get(qn("w:noHBand"))}, noVBand={tblLook.get(qn("w:noVBand"))}')
```

## Step 2: Create Matching Table

```python
def create_styled_table(headers, rows):
    """Create table matching existing doc style: blue header, white text, centered."""
    tbl = OxmlElement('w:tbl')
    
    # Table properties
    tblPr = OxmlElement('w:tblPr')
    tblStyle = OxmlElement('w:tblStyle')
    tblStyle.set(qn('w:val'), 'TableGrid')
    tblPr.append(tblStyle)
    
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '0')
    tblW.set(qn('w:type'), 'auto')
    tblPr.append(tblW)
    
    tblLook = OxmlElement('w:tblLook')
    tblLook.set(qn('w:val'), '04A0')
    tblLook.set(qn('w:firstRow'), '1')
    tblLook.set(qn('w:lastRow'), '0')
    tblLook.set(qn('w:firstCol'), '0')
    tblLook.set(qn('w:lastCol'), '0')
    tblLook.set(qn('w:noHBand'), '0')
    tblLook.set(qn('w:noVBand'), '1')
    tblPr.append(tblLook)
    
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tblBorders.append(border)
    tblPr.append(tblBorders)
    tbl.append(tblPr)
    
    # Grid
    tblGrid = OxmlElement('w:tblGrid')
    total = 9072
    col_w = total // len(headers)
    for _ in headers:
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), str(col_w))
        tblGrid.append(gc)
    tbl.append(tblGrid)
    
    def make_cell(text, is_header=False):
        tc = OxmlElement('w:tc')
        tcPr = OxmlElement('w:tcPr')
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:w'), '0')
        tcW.set(qn('w:type'), 'auto')
        tcPr.append(tcW)
        
        # Cell margins (40 dxa all sides)
        tcMar = OxmlElement('w:tcMar')
        for side in ['top', 'left', 'bottom', 'right']:
            mar = OxmlElement(f'w:{side}')
            mar.set(qn('w:w'), '40')
            mar.set(qn('w:type'), 'dxa')
            tcMar.append(mar)
        tcPr.append(tcMar)
        
        if is_header:
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), '4472C4')  # Match existing header color
            tcPr.append(shd)
        
        tc.append(tcPr)
        
        p = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        jc = OxmlElement('w:jc')
        jc.set(qn('w:val'), 'center')
        pPr.append(jc)
        p.append(pPr)
        
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        color = OxmlElement('w:color')
        color.set(qn('w:val'), 'FFFFFF' if is_header else '000000')
        rPr.append(color)
        if is_header:
            b = OxmlElement('w:b')
            rPr.append(b)
        r.append(rPr)
        
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = str(text)
        r.append(t)
        p.append(r)
        tc.append(p)
        return tc
    
    def make_row(cells, is_header=False):
        tr = OxmlElement('w:tr')
        for c in cells:
            tr.append(make_cell(c, is_header))
        return tr
    
    tbl.append(make_row(headers, True))
    for row in rows:
        tbl.append(make_row(row))
    return tbl
```

## Step 3: Insert Table with Caption

Pattern for academic documents:
```python
# 1. Caption paragraph (bold)
caption = make_normal_element('Tabel 4.5 Judul Tabel')  # with bold rPr
# 2. Table element
table = create_styled_table(headers, rows)
# 3. Source paragraph
source = make_normal_element('(Sumber: Diolah oleh Peneliti, 2026)')

# Insert in order: caption → table → source
current.addnext(source)
current.addnext(table)
current.addnext(caption)
```

## Common Pitfalls

- ALWAYS inspect existing tables FIRST before creating new ones
- Table caption is a NORMAL paragraph (not 'Tabel Caption' style in some templates)
- Source paragraph comes AFTER the table, not before
- Use `(Sumber: ...)` format for Indonesian academic documents
- `addnext` inserts AFTER; `addprevious` inserts BEFORE
- When replacing tables: `old_tbl.addnext(new_tbl); body.remove(old_tbl)`
