# Indonesian Skripsi (Undergraduate Thesis) Writing Guide

## When This Applies
- User is writing a skripsi (S1 thesis) at an Indonesian university
- Common triggers: mentions "skripsi", "BAB I", "UPI", "ADDIE", "R&D", Indonesian university names
- The user likely needs Word (.docx) output, not LaTeX

## Standard Skripsi Structure (BAB I–V)

### BAB I PENDAHULUAN
1. Latar Belakang Penelitian
2. Identifikasi Masalah
3. Rumusan Masalah Penelitian
4. Tujuan Penelitian
5. Manfaat Penelitian (Teoritis + Praktis)
6. Batasan Masalah
7. Definisi Operasional
8. Struktur Organisasi Skripsi

### BAB II KAJIAN PUSTAKA
1. Landasan teori (grouped by key concepts)
2. Penelitian Terdahulu yang Relevan
3. Kerangka Berpikir

### BAB III METODE PENELITIAN
1. Desain Penelitian
2. Metode Penelitian (e.g., R&D with ADDIE model)
3. Partisipan dan Lokasi Penelitian
4. Instrumen Penelitian
5. Prosedur Penelitian
6. Teknik Pengumpulan Data
7. Teknik Analisis Data

### BAB IV HASIL PENELITIAN DAN PEMBAHASAN
1. Temuan Penelitian
2. Pembahasan

### BAB V SIMPULAN, IMPLIKASI, DAN REKOMENDASI
1. Simpulan
2. Implikasi
3. Rekomendasi

## Common R&D Models in Indonesian Education Research

### ADDIE (Most common for media/product development in education)
- **Analysis**: Needs analysis, learner analysis, context analysis
- **Design**: Blueprint, wireframe, storyboard, content mapping
- **Development**: Build the product, expert validation (ahli media + ahli materi)
- **Implementation**: Deploy/test with real users, collect data
- **Evaluation**: Measure effectiveness (pre-test/post-test), user satisfaction

**When to use ADDIE**: Developing educational media, learning tools, websites for educational purposes, teaching materials. Includes expert validation + effectiveness measurement.

### Waterfall (For pure software engineering theses)
- Requirements → Design → Implementation → Testing → Maintenance
- **When to use**: Pure software/app development without educational effectiveness measurement. More common in Teknik Informatika/Ilmu Komputer departments.

### Key difference for advising users:
- Education department (FPTK, FKIP, etc.) → ADDIE
- Computer Science/Engineering department → Waterfall or Agile
- If the thesis measures "effectiveness" or "impact" → ADDIE
- If the thesis only builds and tests software functionality → Waterfall

## UPI (Universitas Pendidikan Indonesia) Formatting Rules
Source: Pedoman Penulisan Karya Ilmiah UPI 2024

### Typography
- **Font**: Times New Roman, 12pt body text
- **Chapter titles**: 14pt or bold
- **Line spacing**: 1.5 for body; 1.0 for abstract, long quotes, references
- **First-line indent**: 1.27 cm (0.5 inch) — standard, not explicitly stated in pedoman

### Page Setup
- **Paper**: A4 (21 × 29.7 cm)
- **Margins**: Left 4cm, Right 3cm, Top 4cm, Bottom 3cm

### Foreign Words (Huruf Miring)
All non-Indonesian words/phrases MUST be italicized:
- English terms: *website*, *brand awareness*, *online*, *digital marketing*, *framework*, *hosting*, *deployment*, *cloud*, *user-friendly*
- Technical names: *Next.js*, *React*, *Vercel*, *server-side rendering*
- Academic terms: *Teaching Factory*, *Research and Development*, *brand recognition*, *brand recall*
- Model names: *Analysis, Design, Development, Implementation, Evaluation*

### Citation Style
- APA Style (recommended by UPI)
- Other styles allowed (MLA, Chicago, Harvard, Vancouver, IEEE) but must be consistent
- Indonesian adaptation: use "dkk." instead of "et al.", "hlm." instead of "p."

### Numbering
- Use hierarchical numbering: 1.1, 1.1.1, etc.
- Tables: "Tabel 2.1" (chapter.sequence)
- Figures: "Gambar 3.1" (chapter.sequence)
- Table captions above, figure captions below

## Technical: Generating .docx with python-docx on Hermes

### Environment Pitfall
The Hermes venv Python (`/home/ubuntu/.hermes/hermes-agent/venv/bin/python3`) has broken lxml imports and no pip. **Always use system Python**:
```bash
/usr/bin/python3 -m pip install python-docx  # one-time
/usr/bin/python3 script.py                    # for execution
```

### Script Writing Pitfall — NEVER use write_file for large scripts
`write_file` silently fails mid-response for large Python scripts, producing repeated `[Tool: write_file] {"path":...` output with no execution. User gets very frustrated. **Always write scripts via terminal heredoc:**

```bash
cat > /tmp/rev_bab1.py << 'EOF'
# ... script content ...
EOF
/usr/bin/python3 /tmp/rev_bab1.py
```

For multi-pass revisions, use `/tmp/r1.py`, `/tmp/r2.py`, etc. to keep scripts short and focused.

**CRITICAL — write_file loop is a hard failure mode.** When `write_file` fails (tool call appears but nothing executes), the agent enters a loop retrying the same call. User gets extremely frustrated: *"bug lagi?"*, *"tolol bgt"*, *"woy bego"*, *"lu bug mulu"*. This is a recurring pattern that has caused serious user frustration multiple times.

**Rule: if `write_file` fails ONCE → immediately switch to `terminal` with `cat > /tmp/script.py << 'EOF'` heredoc. Never retry `write_file` a second time. Never reply to the user explaining the bug — just fix it silently and execute.**

**Also CRITICAL:** Do NOT reply to the user between tool calls when doing a long multi-step task. User explicitly said: *"kamu ga usah balas dulu saya. proses aja dulu bro. baru kirim kalo sudah"* and *"ga usah jawab dulu. kerjakan langsung kirim nanti kalo sudah selesai"*. Execute all steps silently, send the file when done. Any intermediate reply that isn't the final file delivery is unwanted.

### Mixed Formatting (italic foreign words)
Use segment-based paragraph building for mixed bold/italic runs:
```python
def add_mixed_paragraph(doc, segments, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_indent=True):
    """segments = list of (text, bold, italic) tuples"""
    p = doc.add_paragraph()
    for text, bold, italic in segments:
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.bold = bold
        run.italic = italic
    p.alignment = alignment
    if first_line_indent:
        p.paragraph_format.first_line_indent = Cm(1.27)
    set_line_spacing(p, 360)  # 1.5 spacing
    return p
```

### Line Spacing Helper
python-docx doesn't have a simple 1.5 spacing setter. Use OxmlElement:
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_line_spacing(paragraph, spacing=360):
    """360 = 1.5 line spacing in OpenXML units"""
    pPr = paragraph._p.get_or_add_pPr()
    spacing_elem = OxmlElement('w:spacing')
    spacing_elem.set(qn('w:line'), str(spacing))
    spacing_elem.set(qn('w:lineRule'), 'auto')
    pPr.append(spacing_elem)
```

### Delivery
Write the full script to a .py file, execute with `/usr/bin/python3`, then send via:
```
send_message(message="MEDIA:/path/to/file.docx", target="telegram", action="send")
```

## Population Pivot: Changing Research Focus (Masyarakat ↔ Siswa)

**When this applies:** User asks to change thesis focus from one population to another (e.g., "masyarakat sekitar sekolah" → "siswa kelas XI" or vice versa). This is NOT a simple find-replace — it's a fundamental research redesign.

**Workflow for population pivots:**

1. **Research first, revise second.** User explicitly expects you to "pelajari dulu cari referensi" before executing. For major pivots:
   - Search for 3-5 relevant references about the NEW population context (e.g., if pivoting to siswa, find references about website sebagai media pembelajaran, efektivitas pembelajaran digital, etc.)
   - Understand the theoretical framework shift (marketing effectiveness → learning effectiveness)
   - Identify appropriate measurement instruments (brand awareness survey → learning outcome assessment)

2. **Scope the cascade.** A population pivot affects:
   - **BAB 1:** Latar belakang (add learning context), rumusan masalah (change population), tujuan (align with new rumusan), manfaat (add "Bagi Siswa" section)
   - **BAB 2:** Add learning theory sections (e.g., media pembelajaran, efektivitas pembelajaran), add pedagogical references, potentially change effectiveness indicators (marketing metrics → learning metrics like N-Gain)
   - **BAB 3:** Partisipan (change from masyarakat to siswa), sampling (change from purposive community sampling to class-based sampling), instruments (change from community survey to pre-test/post-test learning assessment), analysis (potentially change from descriptive + gain score to paired t-test / Wilcoxon + N-Gain)
   - **Referensi:** Add 5-10 new references about learning/pedagogy

3. **Verify statistical alignment.** If pivoting to siswa + learning context:
   - Check if N-Gain is more appropriate than simple gain score (see `brand-awareness-pretest-posttest.md`)
   - Verify pre-test/post-test design still uses one-group design (no control group)
   - Confirm statistical test: paired t-test (normal) or Wilcoxon (non-normal)

4. **Maintain ADDIE consistency.** If the original used ADDIE for product development, the pivot to siswa doesn't change the development model — it changes the **evaluation phase** from "marketing effectiveness" to "learning effectiveness."

**Common pivot patterns:**

| From | To | Key Changes |
|------|-----|-------------|
| Masyarakat (marketing) | Siswa (learning) | Add learning theory in BAB 2, change instruments to pre-test/post-test, add N-Gain analysis, add pedagogical references |
| Siswa (learning) | Masyarakat (marketing) | Remove learning theory, change instruments to brand awareness survey, use gain score + percentage, add marketing references |

**Pitfall:** Don't just find-replace "masyarakat" → "siswa" in rumusan masalah. The entire research logic changes. Marketing effectiveness ≠ learning effectiveness.

## python-docx TOC Insert Order — CRITICAL BUG

`reversed()` + `addprevious()` in a loop produces **reversed output**. Use moving-anchor pattern instead:

```python
anchor = heading_elem
for text, page, bold, indent in entries:
    e = make_entry(text, page, bold, indent)
    anchor.addnext(e)
    anchor = e  # advance anchor
```

**DO NOT** inject `w:updateFields=true` into settings.xml — user explicitly rejected this. It causes Word to refresh all fields and can corrupt the document.

## PIL Image Generation — Always Vertical Layout

Never use horizontal multi-column layouts for generated images — text overflows boxes.
- Canvas width: 1800px, margin: 60px, content width: 1680px
- Always measure text height before drawing the box:
```python
def text_height(d, text, font, max_w):
    words = text.split(); lines = []; line = ''
    for w in words:
        test = (line+' '+w).strip()
        bb = d.textbbox((0,0), test, font=font)
        if bb[2]-bb[0] > max_w and line: lines.append(line); line = w
        else: line = test
    if line: lines.append(line)
    lh = d.textbbox((0,0),'Ag',font=font)[3]-d.textbbox((0,0),'Ag',font=font)[1]
    return len(lines)*(lh+4)
```
- Crop canvas to actual content height at the end: `img.crop((0,0,W,y+20))`

## Image Position Verification

Always verify images are BEFORE their caption after any insert operation:
```python
for i in range(bab1_idx, dp_idx):
    if doc.paragraphs[i]._element.findall('.//' + qn('w:drawing')):
        nt = doc.paragraphs[i+1].text.strip()
        print(f"P{i}: '{nt[:60]}'")  # must start with 'Gambar X.Y'
```
Fix wrong position: `body.remove(img_elem); caption_elem.addprevious(img_elem)`

## File Size — Compress Images Before Sending via Telegram

Documents >5MB fail to send. Compress all images before final save:
```python
from PIL import Image; import io
for rel in doc.part.rels.values():
    if "image" in rel.reltype:
        try:
            img = Image.open(io.BytesIO(rel.target_part.blob)).convert('RGB')
            if img.width > 1400:
                img = img.resize((1400, int(img.height*1400/img.width)), Image.LANCZOS)
            buf = io.BytesIO(); img.save(buf, format='JPEG', quality=80)
            rel.target_part._blob = buf.getvalue()
        except: pass
```

## Iterative Italic Pass: Avoid Over-Italicizing Indonesian

**Pitfall encountered repeatedly.** When you build a script that scans paragraphs and italicizes foreign words, a naive guard like:

```python
if all(run.italic for run in p.runs if run.text.strip()):
    return False  # skip — assume already correctly italicized
```

…fails on paragraphs that imported into the document with EVERY run already flagged italic (a common artifact of paste-from-source or incremental edits). The skip-condition never re-rebuilds them, and Indonesian-language sentences stay italic.

**Symptom user will report:** "Itu masih ada tulisan yang italic semua padahal itu ada bahasa Indonesia."

**Fix pattern:** When ALL runs in a long paragraph are italic AND the paragraph contains > ~30 chars of text AND it's not a heading / Daftar Pustaka entry / cover page, rebuild it from scratch using the foreign-word regex — segments that don't match the regex get `italic=False`.

```python
def fix_italic_paragraph(p, foreign_pattern):
    text = p.text
    if not text.strip():
        return False
    runs = [r for r in p.runs if r.text.strip()]
    if not runs or not all(r.italic for r in runs):
        return False
    # Skip headings, citations, cover
    if 'Heading' in p.style.name:
        return False
    import re
    if re.search(r'^[A-Z][a-zA-Z]+,\s+[A-Z]\.', text):  # DP entry pattern
        return False
    # Rebuild with regex match-driven italic
    matches = list(foreign_pattern.finditer(text))
    if not matches:
        return False  # don't strip italic if no foreign matches
    segments = []
    pos = 0
    for m in matches:
        if m.start() > pos:
            segments.append((text[pos:m.start()], False))
        segments.append((m.group(), True))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], False))
    # Clear runs, rebuild
    from docx.oxml.ns import qn
    for r in list(p._element.findall(qn('w:r'))):
        p._element.remove(r)
    baseline_size = Pt(12)
    for seg_text, italic in segments:
        run = p.add_run(seg_text)
        run.font.name = 'Times New Roman'
        run.font.size = baseline_size
        run.italic = italic
    return True
```

**KBBI exclusion list** (do NOT italicize — these are Indonesian loanwords):
internet, digital, platform, data, email, video, foto, audio, media, file, aplikasi, sistem, web, situs, mobile, smartphone, laptop, komputer, online (sudah masuk KBBI sebagai daring tapi sering dipakai apa adanya).

Always run a verification pass after italicizing — print all paragraphs whose runs are all italic, and visually check a sample.

## Explicit Numbering vs Auto-Numbering for Rumusan Masalah / Tujuan

**User preference (encountered explicitly):** "Untuk format penomoran lihat lagi itu harusnya di rumusan masalah no 1, 2. Tujuan penelitian poinnya no 1, 2."

When users say the numbers "missing" but the source XML clearly has `numPr` decimal numbering, the issue is **rendering inconsistency** — auto-numbering via `<w:numPr>` requires the consumer (Word, LibreOffice, Google Docs preview) to resolve the abstractNum definition, and many viewers display the items unindented or unnumbered.

**Default policy: prepend explicit text "1. ", "2. ", "3. "** instead of relying on auto-numbering. This is what the user actually wants visible on the page.

```python
def remove_numbering(p):
    pPr = p._element.find(qn('w:pPr'))
    if pPr is not None:
        numPr = pPr.find(qn('w:numPr'))
        if numPr is not None:
            pPr.remove(numPr)

def prepend_explicit_number(p, prefix):
    for run in p.runs:
        if run.text.strip():
            run.text = prefix + run.text
            return
    if p.runs:
        p.runs[0].text = prefix + p.runs[0].text

# Apply to Rumusan Masalah, Tujuan Penelitian, Batasan Masalah, etc.
for idx, num in [(217, '1.'), (218, '2.')]:
    p = doc.paragraphs[idx]
    remove_numbering(p)
    prepend_explicit_number(p, num + ' ')
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.first_line_indent = Cm(1.27)
```

**Apply to:** Rumusan Masalah (1.2), Tujuan Penelitian (1.3), Batasan Masalah (1.5), and any 3.9.x sub-section bold headings the user wants numbered.

## Table Styling Consistency Across Document

When you ADD a new table to an existing skripsi (e.g. user's dosen requests "Tabel 2.5 Metrik Web Analytics"), match the existing table conventions exactly. Mismatches scream "this was added later" to the dosen.

**Standard UPI/Indonesian academic table pattern:**

1. **Header row:** Solid fill `#4472C4` (blue), white bold text, centered horizontally and vertically, font size ~11pt.
2. **Caption ABOVE the table:** Style "Tabel Caption" (or fall back to bold + centered Normal), format `Tabel X.Y <Description>`. Italic foreign words in description.
3. **Source row BELOW the table:** Italic, format `(Sumber: <Author>, <Year>)`.
4. **Description sentence BEFORE the caption:** A regular Normal paragraph stating "Adapun <thing> disajikan pada Tabel X.Y berikut." — Indonesian academic convention.

**Detection script:**
```python
from docx.oxml.ns import qn
for i, table in enumerate(doc.tables):
    first_cell = table.rows[0].cells[0]
    tcPr = first_cell._element.find(qn('w:tcPr'))
    fill = "NONE"
    if tcPr is not None:
        shd = tcPr.find(qn('w:shd'))
        if shd is not None:
            fill = shd.get(qn('w:fill'))
    is_bold = any(r.font.bold for r in first_cell.paragraphs[0].runs if r.text.strip())
    print(f"Table {i:2d}: fill={fill} bold={is_bold}")
# All academic tables should have fill=4472C4 + bold (except formula tables like O₁→X→O₂)
```

**Fix script for inconsistent table:**
```python
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

table = doc.tables[N]
header_row = table.rows[0]
for cell in header_row.cells:
    tcPr = cell._element.find(qn('w:tcPr'))
    if tcPr is None:
        tcPr = OxmlElement('w:tcPr')
        cell._element.insert(0, tcPr)
    # Remove existing shd
    for old in tcPr.findall(qn('w:shd')):
        tcPr.remove(old)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '4472C4')
    tcPr.append(shd)
    for para in cell.paragraphs:
        for run in para.runs:
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## TOC Entry Consolidation After Heading Text Change

When you rename a heading, also update its Daftar Isi (TOC) entry. **Pitfall:** TOC entries often have multiple `<w:t>` runs split by italic boundaries (e.g. `[3.9.2 Analisis Data ][Brand Awareness][ (][Pre-test][ dan ][Post-test][)][33]`). Setting `paragraph.text = new_text` doesn't work because TOC paragraphs are hyperlinks with internal structure.

**Safe pattern: enumerate `<w:t>` elements, replace one with full new title, blank the rest, leave page-number element alone.**

```python
target = doc.paragraphs[160]  # the TOC entry
all_ts = target._element.findall('.//' + qn('w:t'))
# Last w:t is typically the page number — preserve it
title_ts = all_ts[:-1]
page_t = all_ts[-1]

title_ts[0].text = '3.9.2 Analisis Data Efektivitas Website'
for t in title_ts[1:]:
    t.text = ''
# page_t stays as '33' (or whatever)
```

## Inserting New Citations into Daftar Pustaka

Find the alphabetical predecessor (e.g. "Durianto" before "Google. (2026)..."), then `addnext(new_p)`. Use `deepcopy` of an existing entry's `pPr` to preserve hanging indent (1.27cm) and 1.0 line spacing.

```python
from copy import deepcopy
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

# Find predecessor
pred_idx = None
for j in range(dp_start, len(doc.paragraphs)):
    if doc.paragraphs[j].text.strip().startswith('Durianto'):
        pred_idx = j
        break
target = doc.paragraphs[pred_idx]

new_p = OxmlElement('w:p')
ref_pPr = target._element.find(qn('w:pPr'))
if ref_pPr is not None:
    new_p.append(deepcopy(ref_pPr))
target._element.addnext(new_p)

# Find the new para object and add italicized title segments
for j, p in enumerate(doc.paragraphs):
    if p._element is new_p:
        new_para = p
        break

segments = [
    ('Google. (2026). ', False),
    ('Google Analytics Help: Analytics Reporting', True),  # italic per APA
    ('. Diakses pada 5 Mei 2026 dari https://support.google.com/analytics', False),
]
for text, italic in segments:
    run = new_para.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.italic = italic
```

## Full-Document Rebuild: Large Script Syntax Pitfalls

When building large Python scripts via terminal heredoc for docx revision, these syntax errors appear frequently:

**1. Bare string after tuple in list** — the most common error:
```python
# WRONG — bare string literal after tuple breaks the list
p([('Teknik pengambilan sampel menggunakan ', False, False), ('purposive sampling', False, True), ' (Sugiyono, 2019)...'])
#                                                                                                  ^ missing ( and False, False)

# CORRECT
p([('Teknik pengambilan sampel menggunakan ', False, False), ('purposive sampling', False, True), (' (Sugiyono, 2019)...', False, False)])
```

**2. Colon immediately after italic tuple** — breaks list parsing:
```python
# WRONG
p([..., ('website', False, True), ': Persentase...', False, False])
# CORRECT  
p([..., ('website', False, True), (': Persentase...', False, False)])
```

**3. Unicode escapes in heredoc** — `\u00d7` works in Python strings but NOT in heredoc if the shell interprets it. Use actual Unicode characters or write the file with `write_file` for unicode-heavy content.

**Workflow:** Always run `python3 -m py_compile /tmp/script.py && echo OK` before executing. Fix syntax errors before running.

## Full-Document Population Pivot: Multi-Pass Revision Workflow

When the user asks for a **full revision** of an existing .docx (not just a patch), use this 3-pass approach. Each pass saves an intermediate file so you can recover if a later pass breaks something.

### Pass structure

```
rev_bab1.py  → saves _v1.docx   (BAB 1: judul, latar belakang, rumusan, tujuan, manfaat, batasan)
rev_bab2.py  → saves _v2.docx   (BAB 2: teori, efektivitas, kerangka berpikir, penelitian terdahulu)
rev_bab3.py  → saves _v3.docx   (BAB 3: partisipan, populasi, sampel, prosedur, instrumen, analisis)
rev_final.py → saves _FINAL.docx (referensi baru, scan sisa teks lama, verifikasi)
```

### Core helper pattern (use in every pass)

```python
def find_idx(search, start=0):
    for i in range(start, len(paras)):
        if search in paras[i].text:
            return i
    return None

def clear_runs(p):
    for r in list(p._element.findall(qn('w:r'))):
        p._element.remove(r)

def add_runs(p, segments):
    """segments = [(text, bold, italic)]"""
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.bold = bold
        r.italic = italic
```

### Final scan pass (mandatory)

After all passes, always run a scan for leftover old-population text:

```python
# Scan for leftover old text in BAB 1-3 (paragraphs 140-425 approx)
old_fragments = ['masyarakat sekitar sekolah', 'masyarakat di sekitar', 'warga sekitar']
for i, p in enumerate(doc.paragraphs):
    if 140 < i < 425:
        for frag in old_fragments:
            if frag.lower() in p.text.lower():
                print(f"  [P{i}] LEFTOVER: {p.text[:150]}")

# Scan for old judul
for i, p in enumerate(doc.paragraphs):
    if 'Pengembangan Media Pemasaran Melalui Website untuk Meningkatkan' in p.text:
        print(f"  [P{i}] OLD JUDUL: {p.text[:200]}")
```

### Pitfall: `insert_para_after` uses stale `paras` list

After calling `insert_para_after`, the `paras` variable (assigned at script start as `doc.paragraphs`) does NOT update — it's a snapshot. If you call `find_idx` after an insert, it may miss the newly inserted paragraph or return wrong indices. **Solution:** Re-assign `paras = doc.paragraphs` after any batch of inserts, or do all inserts in a single pass at the end.

### Pitfall: Hamalik/Smaldino "MISSING" after insert

When inserting multiple references in sequence (A → B → C), each `insert_para_after` call uses the current `paras` snapshot. If B is inserted after A, and then you search for B to insert C after it, `find_idx` won't find B because `paras` is stale. **Fix:** Save the document and reload it between insert batches, or collect all insertions and do them in reverse alphabetical order (so earlier inserts don't shift later targets).

```python
# Safe pattern: insert in reverse order so indices don't shift
# Or: save + reload between batches
doc.save(INTERMEDIATE)
doc = Document(INTERMEDIATE)
paras = doc.paragraphs
```

## BAB 2 Restructuring: Moving Whole Section Blocks


```python
body = doc.element.body
all_children = list(body)

# Identify start and end elements of the block to move
start_elem = doc.paragraphs[idx_block_start]._element
end_elem   = doc.paragraphs[idx_block_end]._element   # exclusive

# Collect all XML children in the range (paragraphs + tables)
block_to_move = []
collecting = False
for child in all_children:
    if child is start_elem:
        collecting = True
    if child is end_elem:
        break
    if collecting:
        block_to_move.append(child)

# Remove from current position
for elem in block_to_move:
    body.remove(elem)

# Insert before target position
insert_before = doc.paragraphs[idx_target]._element
for elem in block_to_move:
    insert_before.addprevious(elem)
```

**Pitfall:** After the move, `doc.paragraphs` indices are completely reshuffled. Re-run `find_idx` from scratch after any block move. Do NOT cache indices across a block move.

**Pitfall:** Tables between the start and end paragraphs are included automatically because they are XML siblings in `body`. You don't need to handle them separately.



```
2.1 Media Pemasaran
  2.1.1 Strategi Pemasaran
  2.1.2 Bauran Pemasaran
  2.1.3 Bauran Promosi
  2.1.4 Pemasaran Digital

2.2 Website sebagai Media Pemasaran
  2.2.1 Metode Pembuatan Website


2.4 Brand Awareness (Kesadaran Merek)
  2.4.1 Strategi Meningkatkan Brand Awareness

2.5 Efektivitas Website terhadap Peningkatan Brand Awareness
  2.5.1 Indikator Pengukuran Efektivitas
  2.5.2 Kriteria Efektivitas

2.6 Penelitian Terdahulu yang Relevan

2.7 Kerangka Berpikir
```

**Rationale from dosen pembimbing:**

## BAB 3 Structure Per Rumusan Masalah

When the user (or dosen pembimbing) asks to restructure BAB 3 per rumusan masalah, each RM gets its own full sub-chapter with identical sub-sections:

```
3.1 [Judul RM 1]
  3.1.1 Desain Penelitian
  3.1.2 Tempat Penelitian dan Partisipan
  3.1.3 Populasi dan Sampel
  3.1.4 Instrumen Penelitian
  3.1.5 Prosedur Penelitian
  3.1.6 Analisis Data

3.2 [Judul RM 2]
  3.2.1 Desain Penelitian
  ... (same sub-sections)

3.3 [Judul RM 3]
  3.3.1 Desain Penelitian
  ... (same sub-sections)
```

**Implementation pattern:** Delete the entire old BAB 3 body (keep the BAB III heading), then insert new content before DAFTAR PUSTAKA using `insert_before_dp()`. This is cleaner than trying to rename/reorder existing sections.

```python
# Delete old BAB 3 content
body = doc.element.body
bab3_elem = doc.paragraphs[fi('BAB III METODE PENELITIAN')]._element
dp_elem = doc.paragraphs[fi('DAFTAR PUSTAKA')]._element

to_delete = []
collecting = False
for child in list(body):
    if child is bab3_elem:
        collecting = True
        continue  # keep BAB III heading
    if child is dp_elem:
        break
    if collecting:
        to_delete.append(child)

for elem in to_delete:
    body.remove(elem)

# Insert new content before DAFTAR PUSTAKA
def insert_before_dp(segs, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, line=360):
    new_p = OxmlElement('w:p')
    dp_elem.addprevious(new_p)
    for p in doc.paragraphs:
        if p._element is new_p:
            ar(p, segs)
            p.alignment = align
            if indent:
                p.paragraph_format.first_line_indent = Cm(1.27)
            sp(p, line)
            return p
    return None
```

- 3.1 = Kelayakan Website (validasi ahli + responden)
- 3.2 = Efektivitas Brand Awareness (pre-test/post-test masyarakat)
- 3.3 = Tanggapan Siswa (kuesioner online via Google Form)

## Adding RM/Tujuan ke-3 (Third Research Question)

When dosen asks to add a new rumusan masalah, the cascade is:
1. **BAB 1 RM** — insert after RM ke-2 using `ins_after`
2. **BAB 1 Tujuan** — insert after Tujuan ke-2 using `ins_after`
3. **BAB 1 Batasan Masalah** — update to reflect new scope
4. **BAB 3 Partisipan** — update to mention new respondent group
5. **BAB 3 Sampel** — add kelompok ke-3 with criteria
6. **BAB 3 Instrumen** — add new section (e.g. 3.7.6 Kuesioner Tanggapan Siswa)
7. **BAB 3 Teknik Pengumpulan Data** — update procedure for new group
8. **BAB 3 Analisis Data** — update 3.9.1 to include new data type

**Pattern for online kuesioner (tanggapan siswa):**
- Delivery: Google Form link, no need to enter class
- Respondents: siswa kelas XI Program Keahlian, ~30 orang
- Analysis: same persentase kelayakan formula as validasi ahli (≥61% = positif)
- Instrument section: 3.7.6 Kuesioner Tanggapan Siswa terhadap Website

## Italic Rules: Foreign Words vs Indonesian


**Words that ARE italic** (foreign/English terms):
- *website*, *brand awareness*, *online*, *pre-test*, *post-test*, *framework*, *Next.js*, *Google Form*, *Google Analytics*, *usability*, *purposive sampling*, *Research and Development*, *Analysis, Design, Development, Implementation, Evaluation*, *sitemap*, *wireframe*, *smartphone*, *bounce rate*, *unique visitors*, *Gain Score*, *Paired Sample T-Test*, *Wilcoxon Signed Rank Test*, *brand recognition*, *brand recall*, *top of mind*, *surfaktan*, *biodegradable*, *Linear Alkylbenzene Sulfonate*, *deployment*, *server-side rendering*

**Words that are NOT italic** (Indonesian loanwords / common usage):

**Italic audit workflow:**
1. Build a regex pattern of all known foreign terms
2. For each paragraph in BAB 1–3: split into segments matching/not-matching the pattern
3. Rebuild runs: matching segments → italic=True, non-matching → italic=False
4. Special case: if ALL runs in a paragraph are already italic AND paragraph is long (>30 chars), it's likely a paste artifact — rebuild from scratch using the regex

## Storyboard vs Sitemap in BAB 3


1. Beranda (homepage, hero banner, navigasi)
2. Halaman Produk (daftar produk, foto, harga)
3. Detail Produk (komposisi, manfaat, pemesanan)
5. Halaman Kontak (alamat, WhatsApp, form)
6. Admin Panel Login
7. Dashboard Admin
8. Kelola Produk (CRUD)
9. Google Analytics (data untuk pengukuran efektivitas RM 2)


**Text update cascade when replacing sitemap → storyboard:**
- Caption Gambar 3.4
- Daftar Gambar entry
- Prosedur penelitian paragraph that references sitemap: change "sitemap yang menggambarkan hierarki dan hubungan antar halaman" → "storyboard yang menggambarkan alur penggunaan website oleh pengguna"
- Any paragraph referencing "Gambar 3.4 Sitemap"

**PIL generation:** Use a **vertical single-column layout** (one frame per row, full canvas width). Do NOT use multi-column grid layouts — text overflows the box boundaries when columns are too narrow. User explicitly said: *"itu ada yg tidak masuk ke box teks nya kurang rapih bro, tolong kalo misal ke samping itu bikin mepet karena margin, buat aja ke bawah gambarnya"*.

Each frame: numbered circle on left, title + divider + bullet list. Canvas height is calculated dynamically from content (measure text height before drawing, not fixed H). Standard canvas width: **1800px** with 60px margin each side = 1680px content width — wide enough for Indonesian text without overflow.

**This vertical layout rule applies to ALL diagrams** — kerangka berpikir, storyboard, ADDIE, prosedur, alur, wireframe, struktur project. Every diagram should use vertical stacking with dynamic height. The wireframe is the only exception: it uses a 2-column layout INSIDE each page section (left=image placeholder, right=info text), but the page sections themselves are still stacked vertically.

## ADDIE Scope: Only for RM 1 (Kelayakan)

**Critical correction from dosen review:** Model ADDIE is used ONLY to answer RM 1 (kelayakan/development). RM 2 and RM 3 have their own separate research designs.

**Gambar 3.1 ADDIE — Implementation step should contain ONLY:**
- Uji kelayakan website oleh 10 responden masyarakat umum
- Responden mengisi kuesioner pengujian website

**Do NOT include in ADDIE Implementation:**
- Pre-test / post-test brand awareness (→ belongs in RM 2 design)
- Kuesioner tanggapan siswa (→ belongs in RM 3 design)

**Add a note at the bottom of the ADDIE diagram:**
> "Catatan: Model ADDIE digunakan untuk menjawab RM 1 (Kelayakan Website). RM 2 (Efektivitas Brand Awareness) dan RM 3 (Tanggapan Siswa) menggunakan desain penelitian terpisah."

**Gambar 3.2 Prosedur Penelitian** — same scope as ADDIE. Only covers the development + kelayakan process. Pre-test/post-test and tanggapan siswa are NOT part of the prosedur ADDIE.

**Gambar 3.3 Alur Penelitian** — this is a SEPARATE diagram from Gambar 3.2. If dosen says "tidak perlu alur penelitian di prosedur", remove Gambar 3.3 entirely and renumber subsequent figures (3.4→3.3, 3.5→3.4, 3.6→3.5). Update all caption references and Daftar Gambar entries.

**Renumbering cascade when removing a figure:**
```python
# Update captions in body
renumber = [
    ('Gambar 3.4 Storyboard...', 'Gambar 3.3 Storyboard...'),
    ('Gambar 3.5 Wireframe...', 'Gambar 3.4 Wireframe...'),
    ('Gambar 3.6 Tampilan Struktur...', 'Gambar 3.5 Tampilan Struktur...'),
]
# Update text references (e.g. "disajikan pada Gambar 3.4 berikut")
# Update Daftar Gambar entries (paragraphs 100-bab1_idx)
# Delete: image paragraph + caption paragraph + teks referensi paragraph
```

## Wireframe: Only Show Actual Products


**Admin panel stat card:** "Total Produk: 1 Produk" (not 5 or multiple).

**Product grid in wireframe:** Show 1 product card only, centered, not a 3-column grid.

## PIL Diagram Generation: All Research Diagrams

When user asks to "buat ulang semua gambarnya" or "gambar tidak sesuai konten", generate ALL diagrams from scratch with PIL. Do NOT keep old images from the original docx — they reflect the old research design.


| Gambar | Isi | PIL size | Notes |
|--------|-----|----------|-------|
| 2.2 Kerangka Berpikir | Kondisi Awal → Solusi → ADDIE → 3 kotak RM → Hasil | 1800×2200 | Must show all 3 RM |
| 3.1 ADDIE Diagram | 5 tahap vertikal, Implementation = uji kelayakan 10 responden ONLY | 1800×2200 | ADDIE = RM 1 only |
| 3.2 Prosedur Penelitian | 5 tahap ADDIE vertikal, detail per tahap | 1800×2200 | No pre-test/post-test here |
| 3.3 Storyboard | 9 frame vertikal dengan browser mockup | 1800×2900 | Include Frame 5: Brand Awareness |
| 3.4 Wireframe | 4 halaman: Beranda, Detail Produk, Brand Awareness, Admin | 1800×2900 | Only sabun cuci piring |
| 3.5 Struktur Project | Folder tree (kiri) + penjelasan komponen (kanan) | 1800×2200 | Include app/brand-awareness/ |

**Note:** Gambar 3.3 Alur Penelitian was removed per dosen feedback ("tidak perlu di prosedur"). If it was previously Gambar 3.3, renumber: old 3.4→3.3, old 3.5→3.4, old 3.6→3.5.

**Key content rules:**
- Gambar 3.1 ADDIE Implementation step: **ONLY uji kelayakan 10 responden** — no pre-test/post-test, no tanggapan siswa
- Gambar 3.2 Prosedur: same scope as ADDIE — development + kelayakan only
- Gambar 3.3 Storyboard MUST include "Halaman Pembelajaran Brand Awareness" frame (Frame 5) — website has dual function: pemasaran + pembelajaran brand awareness siswa
- Gambar 3.4 Wireframe MUST include halaman brand awareness siswa as one of the pages; ONLY show sabun cuci piring (not multiple products)
- Gambar 3.5 Struktur Project MUST include `app/brand-awareness/` folder in the tree

**PIL color palette (consistent across all diagrams):**
```python
BD='#1F4E79'  # dark blue — primary headers
BM='#2E75B6'  # medium blue — RM 1 / secondary
BL='#DEEAF1'  # light blue — RM 1 background
GD='#375623'  # dark green — RM 2 / ADDIE
GL='#E2EFDA'  # light green — RM 2 background
OR='#C55A11'  # orange — RM 3 / warnings
OL='#FCE4D6'  # light orange — RM 3 background
YD='#7F6000'  # dark yellow — kondisi awal
YL='#FFF2CC'  # light yellow — kondisi awal background
GRB='#BFBFBF' # gray border
GRL='#F2F2F2' # gray background (mockup)
```

**Font loading (always try DejaVu, fallback to default):**
```python
try:
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
    FM = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 38)
    FR = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
    FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
    FL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    FMono = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 22)
except:
    FB=FM=FR=FS=FL=FMono=ImageFont.load_default()
```

**Save all to `/tmp/gambar_baru/` then insert into docx in one pass.**

## PIL Diagram: Dynamic Canvas Height Pattern

Always calculate canvas height BEFORE creating the Image object. Fixed heights cause clipping or excessive whitespace.

```python
def measure_section_height(d_tmp, title, items, font_h3, font_small, inner_w, pad=25):
    """Measure total height of a section box before drawing."""
    th = text_height(d_tmp, title, font_h3, inner_w) + 10
    items_h = sum(max(text_height(d_tmp, it, font_small, inner_w-20), 28) + 6 for it in items)
    return pad + th + 12 + items_h + pad

# Pattern: measure on a throwaway canvas, then create real canvas
tmp = Image.new('RGB', (W, 100), 'white')
d_tmp = ImageDraw.Draw(tmp)
y_est = 145  # header height
for title, items, bg, border, tc_col in sections:
    y_est += measure_section_height(d_tmp, title, items, F['h3'], F['small'], bw-40) + 50
H = y_est + 80  # bottom padding

img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)
# ... draw content ...
img_cropped = img.crop((0, 0, W, actual_y + 20))  # crop to actual content if needed
```

**text_height helper:**
```python
def text_height(d, text, font, max_w):
    words = text.split(); lines = []; line = ''
    for w in words:
        test = (line + ' ' + w).strip()
        bb = d.textbbox((0,0), test, font=font)
        if bb[2]-bb[0] > max_w and line:
            lines.append(line); line = w
        else:
            line = test
    if line: lines.append(line)
    if not lines: return 0
    lh = d.textbbox((0,0), 'Ag', font=font)[3] - d.textbbox((0,0), 'Ag', font=font)[1]
    return len(lines) * (lh + 4)
```

## Embedding and Moving Images Between .docx Files

When rebuilding BAB 3 from scratch (delete old content, insert new), all embedded images are lost because they lived in the deleted paragraphs. To restore them:

```python
from copy import deepcopy
from docx.oxml.ns import qn

doc_orig = Document('original.docx')
doc_new  = Document('rebuilt.docx')

# Find image paragraphs in original by context
for i, p in enumerate(doc_orig.paragraphs):
    drawings = p._element.findall('.//' + qn('w:drawing'))
    if drawings:
        next_t = doc_orig.paragraphs[i+1].text.strip()[:80]
        print(f"P{i}: next='{next_t}'")  # use next caption to identify which image

# Insert image before its caption in new doc
def insert_image_before_caption(doc_new, caption_search, orig_para_elem, bab_start=0):
    for i in range(bab_start, len(doc_new.paragraphs)):
        if caption_search in doc_new.paragraphs[i].text:
            cap_elem = doc_new.paragraphs[i]._element
            cap_elem.addprevious(deepcopy(orig_para_elem))
            return True
    return False

insert_image_before_caption(doc_new, 'Gambar 3.1 Diagram Alur Model ADDIE',
                             doc_orig.paragraphs[280]._element, bab_start=285)
```

**CRITICAL: Do NOT reload the document between insert calls.** Each `Document()` call creates a new in-memory object. If you call `doc_new = Document(path)` again after inserting images, all inserts are lost. Load once, insert all images, save once.

**CRITICAL: Load BOTH documents at the start of the image-transfer script, before any inserts.** Pattern:
```python
doc_new  = Document('/path/to/rebuilt.docx')
doc_orig = Document('/path/to/original.docx')
# Now do all inserts using deepcopy from doc_orig into doc_new
# Save doc_new ONCE at the end
doc_new.save('/path/to/rebuilt.docx')
```
If you reload `doc_new` mid-script (e.g. to "refresh" after a previous save), all prior inserts are lost.

**Pitfall: Images nyasar ke TOC area.** If `insert_image_before_caption` is called when the document has duplicate caption text (e.g. caption appears in both Daftar Gambar and body), the image may be inserted before the TOC entry instead of the body caption. Fix: always pass `bab_start=fi('BAB III METODE')` to restrict search to body only.

**Pitfall: Image inserted AFTER caption instead of before.** When `addprevious` is called on the wrong element (e.g. the paragraph AFTER the caption instead of the caption itself), the image ends up after the caption. Always verify: `next_text_of_image_para == caption_text`. If `next_text == ''`, the image is misplaced.

**Fix for misplaced image (wrong position in body):** Use body-level element move — do NOT delete and re-insert (that loses the image data). Instead:
```python
body = doc.element.body
img_elem = doc.paragraphs[img_idx]._element
target_cap_elem = doc.paragraphs[cap_idx]._element
body.remove(img_elem)
target_cap_elem.addprevious(img_elem)
# Verify: doc.paragraphs[new_img_idx+1].text should == caption text
```

**Detection script for misplaced images:**
```python
bab1_idx = fi(doc, 'BAB I PENDAHULUAN')
for i, p in enumerate(doc.paragraphs):
    if p._element.findall('.//' + qn('w:drawing')):
        if i < bab1_idx:
            print(f"MISPLACED: P{i} (before BAB I)")
        else:
            next_t = doc.paragraphs[i+1].text.strip()[:60] if i+1 < len(doc.paragraphs) else ''
            print(f"OK: P{i} -> '{next_t}'")
```

**Generating a new Kerangka Berpikir diagram with PIL:**
When the research design changes (new RM, new population), the old kerangka berpikir image is stale. Generate a new one with PIL and replace it:

```python
from PIL import Image, ImageDraw, ImageFont
from docx.shared import Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Generate diagram
img = Image.new('RGB', (2200, 2800), 'white')
draw = ImageDraw.Draw(img)
# ... draw boxes, arrows, text ...
img.save('/tmp/kerangka_berpikir_new.png', 'PNG', dpi=(150, 150))

# Replace old image in docx
idx_cap = fi(doc, 'Gambar 2.2 Kerangka Berpikir')
# Find and remove old image paragraph before caption
for i in range(max(0, idx_cap-5), idx_cap):
    if doc.paragraphs[i]._element.findall('.//' + qn('w:drawing')):
        doc.paragraphs[i]._element.getparent().remove(doc.paragraphs[i]._element)
        break
# Insert new image
new_p = OxmlElement('w:p')
doc.paragraphs[fi(doc, 'Gambar 2.2 Kerangka Berpikir')]._element.addprevious(new_p)
for p in doc.paragraphs:
    if p._element is new_p:
        p.add_run().add_picture('/tmp/kerangka_berpikir_new.png', width=Inches(5.5))
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        break
```

**Standard Kerangka Berpikir layout for 3-RM website thesis:**
```
                                                              ↓
                    [RM1: Kelayakan] | [RM2: Efektivitas BA] | [RM3: Tanggapan Siswa]
                                                              ↓
                                          [HASIL YANG DIHARAPKAN]
```

## Kerangka Berpikir Diagram Updates

When research focus changes (e.g. adding RM ke-3, changing population), update the Kerangka Berpikir text AND note that the diagram image (Gambar 2.X) needs to be regenerated. The text description of the kerangka berpikir should reflect all 3 RMs:

```
  1. Website layak (validasi ahli ≥61%)
  2. Brand awareness masyarakat meningkat (p<0.05)
  3. Tanggapan siswa positif (≥61%)
```

For BAB 3 diagrams (Gambar 3.1 ADDIE, Gambar 3.2 Prosedur, Gambar 3.3 Alur Penelitian): when BAB 3 is restructured per RM, the alur penelitian diagram caption should be updated to reference the new structure. The actual image placeholder stays — note to user that diagram images need manual update in Word.

**Pitfall:** Diagram images (Gambar 3.1, 3.2, etc.) are embedded as image objects in the docx. python-docx cannot regenerate them — it can only update the caption text. For images that CAN be regenerated (kerangka berpikir, storyboard, any diagram whose content you know), generate them with PIL and replace the image object. For images that cannot be regenerated (screenshots, wireframes, ADDIE diagrams from the user's own work), keep the original image and only update the caption text if needed.

**When user asks "apakah gambar sudah sesuai konten?"** — extract all images from the docx, send a grid preview to Telegram, and ask the user to confirm which ones are wrong. Do NOT assume images are correct just because captions match. The user's own diagrams (ADDIE, prosedur, alur, wireframe, struktur project) are their own work and cannot be verified programmatically.




For sabun cuci piring, required content:
1. Definisi produk + SNI reference (SNI 06-2048-1990)
2. Bahan-bahan utama: surfaktan (LAS/AOS), builder (NaCl), foam booster (CAPB), pengawet (MIT), air
3. Teknologi pembuatan: penimbangan → saponifikasi/netralisasi → aditif → QC (pH, viskositas, daya bersih) → pengemasan
4. Manfaat dan fungsi produk
5. Closing paragraph connecting product knowledge to website content

**References to cite:**
- Hambali, E., Bunasor, T. K., Suryani, A., & Kusumah, G. A. (2005). Aplikasi Dietanolamida dari Asam Laurat Minyak Inti Sawit pada Pembuatan Sabun Transparan. *Jurnal Teknologi Industri Pertanian*, 15(2), 46-53.
- Standar Nasional Indonesia. (1990). *SNI 06-2048-1990: Sabun Cair*. Jakarta: Badan Standardisasi Nasional.


## Lampiran Ordering Logic

When adding a new lampiran (e.g. web analytics tracker form), place it according to **instrument hierarchy**, not creation order:

1. Validasi Ahli (Media → Materi → Bahasa)  — Lampiran 1, 2, 3
2. Kuesioner Pengujian Website Responden — Lampiran 4
3. Kuesioner Brand Awareness Pre-test → Post-test — Lampiran 5, 6
4. **Instrumen pendukung pengukuran efektivitas** (e.g. Format Pemantauan Web Analytics) — Lampiran 7 (paling akhir)

User explicitly questioned ordering ("urutan lampiran sudah benar?") — confirm body matches Daftar Lampiran TOC, both numerically and by section label.

## BAB 3 Heading Styles: Apply Programmatically

When BAB 3 is rebuilt from scratch (delete + reinsert), all paragraphs come in as `Normal` style with bold runs. They look like headings visually but are NOT recognized by Word's TOC or navigation pane. Apply heading styles explicitly after rebuild:

```python
import re
from docx import Document

doc = Document(path)
bab3 = fi('BAB III METODE')
dp   = fi('DAFTAR PUSTAKA')

for i in range(bab3, dp):
    p = doc.paragraphs[i]
    t = p.text.strip()
    if not t: continue

    if 'BAB III' in t:
        p.style = doc.styles['Heading 1']
    elif re.match(r'^3\.\d+\s', t) and not re.match(r'^3\.\d+\.\d+', t) and len(t) < 120:
        p.style = doc.styles['Heading 2']   # 3.1, 3.2, 3.3
    elif re.match(r'^3\.\d+\.\d+\s', t) and len(t) < 120:
        p.style = doc.styles['Heading 3']   # 3.1.1, 3.2.1, etc.
```

Also fix any BAB 2 sub-sub-headings that were inserted as `Normal` bold (e.g. 2.1.1, 2.3.1):
```python
    idx = fi(search)
    if idx and doc.paragraphs[idx].style.name != 'Heading 3':
        doc.paragraphs[idx].style = doc.styles['Heading 3']
```

**Why this matters:** Without proper heading styles, the TOC field (`TOC \o "1-3"`) cannot pick up BAB 3 entries, and the navigation pane in Word shows BAB 3 as flat body text.

## Daftar Isi / Daftar Tabel / Daftar Gambar / Daftar Lampiran Update

**Context:** The original v15 docx uses a mix of manual entries (Daftar Isi, Daftar Tabel, Daftar Lampiran) and a TOC field (Daftar Gambar). After major restructuring, all four need updating.

**Strategy:** Update manually (not via TOC field regeneration) because:
1. The Daftar Isi is already manual — no TOC field to update
2. TOC field regeneration requires Word COM automation (not available on Linux)
3. Manual update gives exact control over what appears

**Inject `updateFields=true`** so Word auto-refreshes page numbers when opened:
```python
settings_part = doc.settings.element
update_fields = settings_part.find(qn('w:updateFields'))
if update_fields is None:
    update_fields = OxmlElement('w:updateFields')
    update_fields.set(qn('w:val'), 'true')
    settings_part.append(update_fields)
else:
    update_fields.set(qn('w:val'), 'true')
```

**Pattern for updating each Daftar:**
1. Find the heading paragraph (e.g. `fi('DAFTAR ISI')`)
2. Find the next heading paragraph (e.g. `fi('DAFTAR TABEL')`)
3. Delete all paragraphs between them
4. Insert new entries in reverse order using `addprevious` on the next heading

```python
# Delete old entries
idx_di = fi('DAFTAR ISI'); idx_dt = fi('DAFTAR TABEL')
for elem in [doc.paragraphs[i]._element for i in range(idx_di+1, idx_dt)]:
    if elem.getparent(): elem.getparent().remove(elem)

# Insert new entries (reversed so addprevious gives correct order)
ref = doc.paragraphs[fi('DAFTAR TABEL')]._element
for text, page, level in reversed(toc_entries):
    new_p = OxmlElement('w:p')
    ref.addprevious(new_p)
    for p in doc.paragraphs:
        if p._element is new_p:
            r = p.add_run(text + '\t' + page)
            r.font.name = 'Times New Roman'; r.font.size = Pt(12)
            r.bold = (level == 0)
            p.paragraph_format.left_indent = {0: Cm(0), 1: Cm(0.5), 2: Cm(1.0)}.get(level, Cm(0))
            break
```

**Note on page numbers:** Page numbers in the manual Daftar Isi are estimates. Tell the user: *"Nomor halaman adalah estimasi. Setelah dibuka di Word, tekan Ctrl+A lalu F9 untuk update semua field dan nomor halaman akan menyesuaikan otomatis."*

**Daftar Lampiran update:** When adding a new lampiran (e.g. Kuesioner Tanggapan Siswa, Format Web Analytics), update both the Daftar Lampiran entries AND the lampiran body section at the end of the document. Lampiran ordering: Validasi Ahli (1-3) → Kuesioner Responden (4) → Kuesioner BA Pre/Post (5-6) → Kuesioner Tanggapan Siswa (7) → Format Web Analytics (8).

## insert_para_after Helper Pattern

When inserting new paragraphs into an existing document, use `addnext` relative to an anchor element. This is the complement of `insert_before_dp` (which uses `addprevious`).

```python
def insert_para_after(segments, anchor_elem):
    """Insert a new paragraph with mixed runs after anchor_elem.
    segments = [(text, bold, italic), ...]
    Returns the new paragraph object.
    """
    new_p = OxmlElement('w:p')
    anchor_elem.addnext(new_p)
    for p in doc.paragraphs:
        if p._element is new_p:
            for text, bold, italic in segments:
                r = p.add_run(text)
                r.font.name = 'Times New Roman'
                r.font.size = Pt(12)
                r.bold = bold
                r.italic = italic
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.27)
            pPr = p._p.get_or_add_pPr()
            sp = OxmlElement('w:spacing')
            sp.set(qn('w:line'), '360')
            sp.set(qn('w:lineRule'), 'auto')
            pPr.append(sp)
            return p
    return None
```

**Insertion order pitfall:** When inserting multiple paragraphs AFTER an anchor, insert in REVERSE desired order. Each `addnext` puts the new element immediately after the anchor, so the last inserted appears first in the document.

**Sub-heading separation pitfall:** When inserting content between a sub-heading (e.g. "7) Struktur Proyek") and a later element (e.g. "Gambar 4.5"), the sub-heading's description paragraph may get separated from it. After inserting, verify the order is: sub-heading → description → new content → later element. If separated, use `body.remove()` + `addnext()` to move the description back.

## Heading Style Pitfall: Sub-items vs Headings

**Common mistake:** Using Heading 3 for sub-items that should be Normal+bold.

**Wrong:**
```
4.1.1 Temuan          ← Heading 3 ✓
  a. Tahap Analysis   ← Heading 3 ✗ (same level as 4.1.1!)
  b. Tahap Design     ← Heading 3 ✗
```

**Correct:**
```
4.1.1 Temuan          ← Heading 3
  a. Tahap Analysis   ← Normal + bold (sub-item, not a heading)
  b. Tahap Design     ← Normal + bold
```

**Rule of thumb:** If the label starts with a letter (`a.`, `b.`) or a number in parentheses (`1)`, `2)`), it's a sub-item, NOT a heading. Use Normal + bold + first-line indent.

**Fix script:**
```python
for marker in ['a. Tahap Analysis', 'b. Tahap Design', '1) Sitemap', '2) Wireframe']:
    idx = fi(marker)
    if idx:
        paras[idx].style = doc.styles['Normal']
        for run in paras[idx].runs:
            run.bold = True
        paras[idx].paragraph_format.first_line_indent = Cm(1.27)
        set_line_spacing(paras[idx])
```

**Why this matters:** Wrong heading levels appear in Word's navigation pane and TOC, making the document structure confusing. Sub-items under 4.1.1 should NOT appear as peers of 4.1.1 in the TOC.

## BAB IV Title Convention

**Pitfall:** The BAB IV heading is often just "BAB IV" without the full title. UPI pedoman requires the full title.

**Wrong:** `BAB IV`
**Correct:** `BAB IV\nHASIL PENELITIAN DAN PEMBAHASAN`

**Fix:**
```python
idx = fi('BAB IV')
clear_runs(paras[idx])
r = paras[idx].add_run('BAB IV\nHASIL PENELITIAN DAN PEMBAHASAN')
r.font.name = 'Times New Roman'; r.font.size = Pt(14); r.bold = True
paras[idx].alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## Section-Heading Numbering Convention

Indonesian academic sections sometimes need explicit numbering INSIDE the body (not the heading itself):

```
3.9.2 Analisis Data Efektivitas Website  ← Heading 3 style, no number prefix in heading

Data efektivitas website dianalisis melalui dua pendekatan...

1. Analisis Data Web Analytics  ← bold + explicit "1. " prefix, NOT a heading
   <description>

2. Analisis Data Brand Awareness (Pre-test dan Post-test)  ← bold + "2. " prefix
   <list of steps>
```

The bold sub-section labels are NOT Heading 4 — they're Normal paragraphs with bold runs, manually numbered. Don't try to apply Heading 4 style.

## Cross-Chapter Audit: BAB 1-4 Consistency Check

When user asks "cek semuanya sudah sesuai belum" or "audit skripsi", run a systematic cross-chapter consistency check. Do NOT just skim — run programmatic checks.

### Audit checklist (run in order):

**1. Heading structure per BAB:**
```python
for i in range(bab_start, bab_end):
    if paras[i].style.name.startswith('Heading'):
        print(f"  P{i} [{paras[i].style.name}] {paras[i].text.strip()[:70]}")
```
Check for: wrong heading levels (e.g. `2.1.4` as Heading 2 instead of Heading 3), missing sections, inconsistent numbering.

**2. Tabel/Gambar numbering gaps:**
```python
tabel_nums = sorted([re.match(r'Tabel (\d+\.\d+)', p.text.strip()).group(1)
                     for p in paras if re.match(r'Tabel \d+\.\d+', p.text.strip())])
# Check for gaps: expect 2.1, 2.2, 2.3, 2.4... not 2.1, 2.2, 2.3, 2.6
```

**3. Cross-reference integrity:**
- Find all "Gambar X.Y" and "Tabel X.Y" mentions in text
- Verify each referenced figure/table actually exists as a caption
- Verify no orphan captions (caption exists but never referenced in text)

**4. BAB 3 vs BAB 4 method alignment:**
- Extract all statistical methods mentioned in BAB 3 (e.g. "Wilcoxon", "Paired Sample T-Test", "Gain Score")
- Extract all methods mentioned in BAB 4
- Flag: methods in BAB 3 but NOT in BAB 4, or vice versa
- **Pitfall:** If data hasn't been collected yet, BAB 4 can't specify which test was used — see "Statistical Test Description" section below.

**5. BAB 4 content depth:**
- Count paragraphs per section (4.1, 4.2, 4.3)
- Flag sections with <5 substantive paragraphs
- Check for placeholder text (`____`, `___`, `[diisi]`, `belum`)
- Check for empty Temuan sections (only describing development, not presenting data)

**6. Sub-heading style consistency:**
- Check if sub-sub-headings like "a. Tahap Analysis", "1) Sitemap" use Heading 3 (wrong) or Normal+bold (correct)
- Pattern: `a.` prefix = sub-item under a numbered section, NOT a heading

### Common findings from audits:

| Finding | Severity | Fix |
|---------|----------|-----|
| Section numbering gap (2.4→2.6) | Critical | Renumber subsequent sections + all references |
| Tabel/Gambar number gap | Critical | Renumber or add missing table |
| Placeholder ____ in BAB 4 | Critical | Fill with data or template |
| Sub-heading wrong style | Medium | Change Heading 3 → Normal + bold |
| BAB 3 method not in BAB 4 | Medium | Add method mention in BAB 4 or remove from BAB 3 |
| BAB 4 too thin | Medium | Add template tables |
| BAB IV title incomplete | Low | Add "HASIL PENELITIAN DAN PEMBAHASAN" |

## Section Renumbering Cascade

When a section is deleted (e.g. Section 2.5 removed, leaving 2.4→2.6), ALL subsequent sections must be renumbered. This cascades to:

1. **Section headings** (2.6→2.5, 2.7→2.6)
2. **Table captions** (Tabel 2.6→2.4 if tables were numbered by section)
3. **Text references** ("pada Tabel 2.6" → "pada Tabel 2.4")
4. **Daftar Isi entries** (manual TOC)
5. **Daftar Tabel entries**

**Script pattern:**
```python
# Renumber section headings
renumber_map = {
    '2.6 Penelitian Terdahulu': '2.5 Penelitian Terdahulu yang Relevan',
    '2.7 Kerangka Berpikir': '2.6 Kerangka Berpikir',
}
for old, new in renumber_map.items():
    idx = fi(old)
    if idx:
        clear_runs(paras[idx])
        r = paras[idx].add_run(new)
        r.font.name = 'Times New Roman'; r.font.size = Pt(12); r.bold = True

# Renumber table captions (careful: runs may be split)
for i in range(bab_start, bab_end):
    if 'Tabel 2.6' in paras[i].text and paras[i].text.strip().startswith('Tabel'):
        old_text = paras[i].text
        new_text = old_text.replace('Tabel 2.6', 'Tabel 2.4')
        for r in list(paras[i]._element.findall(qn('w:r'))):
            paras[i]._element.remove(r)
        r = paras[i].add_run(new_text)
        r.font.name = 'Times New Roman'; r.font.size = Pt(12); r.bold = True

# Fix text references (runs may be split across multiple run elements)
for i in range(bab_start, bab_end):
    for run in paras[i].runs:
        if 'Tabel 2.6' in run.text:
            run.text = run.text.replace('Tabel 2.6', 'Tabel 2.4')
```

**Pitfall:** Table caption text is often split across multiple runs (e.g. "Tabel " in one run, "2.6 Penelitian..." in another). Setting `run.text` on individual runs won't work. **Solution:** Clear all runs and rebuild from full text.

## Statistical Test Description: When Data Not Yet Collected

**Common scenario:** User writes BAB 3 before collecting data. BAB 3 describes the statistical method, but BAB 4 can't present actual results yet.

**Correct approach in BAB 3:** Describe BOTH possible outcomes:
```
Uji Hipotesis
Uji hipotesis dilakukan dengan membandingkan skor pre-test dan post-test.
Apakah data berdistribusi normal ditentukan melalui uji Shapiro-Wilk.
Jika data berdistribusi normal, maka digunakan uji Paired Sample T-Test.
Sebaliknya, jika data tidak berdistribusi normal, maka digunakan uji
Wilcoxon Signed-Rank Test (Sugiyono, 2019). Hipotesis penelitian ini adalah:
H₀: Tidak terdapat perbedaan signifikan skor brand awareness...
H₁: Terdapat perbedaan signifikan skor brand awareness...
```

**Wrong approach:** Committing to one test ("menggunakan uji Wilcoxon") before knowing if data is normal or not.

**In BAB 4 (template mode):** Create template tables with "___" placeholders:
- Tabel 4.X Hasil Uji Normalitas Shapiro-Wilk (Statistik, df, Sig., Keputusan)
- Tabel 4.Y Hasil Uji Paired Sample T-Test / Wilcoxon (N, Z/t, Sig., Keputusan)

Tell user: "Kolom ___ diisi setelah data terkumpul dan dianalisis."

## BAB 4 Template Tables (Pre-Data Collection)

When BAB 4 needs to be structured before data is available, create template tables with placeholder values. Use `insert_table_before(anchor_elem, headers, rows, caption_text)` pattern.


**RM 1 — Kelayakan (Tabel 4.1–4.4):**
- 4.1: Hasil Penilaian Kelayakan Ahli Media (Aspek | Skor Maks | Skor Ahli | % | Kategori)
- 4.2: Hasil Penilaian Kelayakan Ahli Materi (same structure)
- 4.3: Hasil Pengujian Kelayakan Responden (same structure)
- 4.4: Rekapitulasi Hasil Kelayakan Website (Sumber | Rata-rata | % | Kategori)

**RM 2 — Efektivitas (Tabel 4.5–4.9):**
- 4.5: Skor Pre-test dan Post-test Brand Awareness (Responden | Pre | Post | Gain)
- 4.6: Hasil Gain Score (Rata-rata Pre/Post/Gain + Kategori)
- 4.7: Hasil Uji Normalitas Shapiro-Wilk (Uji | Statistik | df | Sig. | Keputusan)
- 4.8: Hasil Uji Hipotesis (Uji | N | Z/t | Sig. | Keputusan)
- 4.9: Metrik Google Analytics 4 (Metrik | Nilai)

**RM 3 — Tanggapan Siswa (Tabel 4.10):**
- 4.10: Hasil Kuesioner Tanggapan Siswa (Aspek | Skor Maks | Rata-rata | % | Kategori)

### Manual XML table insertion (when `add_table()` positions wrong):

`doc.add_table()` appends tables at the END of the document body, not at a specific position. To insert at a specific position, build the table XML manually and use `addprevious()`:

```python
def insert_table_before(anchor_elem, headers, rows, caption_text):
    """Insert a styled table with caption before anchor_elem."""
    # 1. Insert caption paragraph
    cap_p = OxmlElement('w:p')
    anchor_elem.addprevious(cap_p)
    # ... add caption runs with bold, centered ...

    # 2. Build table XML manually
    tbl = OxmlElement('w:tbl')
    # tblPr (style, width, borders)
    # tblGrid (gridCol per column)
    # Header row with blue fill #4472C4 + white bold text
    # Data rows with centered text
    # ... see full pattern in the skill ...

    # 3. Insert table before anchor
    anchor_elem.addprevious(tbl)
```

**Key XML elements for a styled table:**
```python
# Header cell styling
tcPr = OxmlElement('w:tcPr')
shd = OxmlElement('w:shd')
shd.set(qn('w:val'), 'clear')
shd.set(qn('w:color'), 'auto')
shd.set(qn('w:fill'), '4472C4')  # UPI blue
tcPr.append(shd)

# Cell text with font
r = OxmlElement('w:r')
rPr = OxmlElement('w:rPr')
rFonts = OxmlElement('w:rFonts')
rFonts.set(qn('w:ascii'), 'Times New Roman')
rFonts.set(qn('w:hAnsi'), 'Times New Roman')
rPr.append(rFonts)
# For header: add <w:b/> and <w:color w:val="FFFFFF"/>
```

**Pitfall:** After inserting tables manually, `doc.tables` (python-docx accessor) may not find them if the XML structure is slightly off. Verify by counting `w:tbl` elements directly:
```python
body = doc.element.body
count = sum(1 for child in body if child.tag == qn('w:tbl'))
```


