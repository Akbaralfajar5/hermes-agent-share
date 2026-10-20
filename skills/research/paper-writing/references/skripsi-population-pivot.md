# Skripsi Population Pivot Pattern

## When This Applies
User needs to revise an existing Indonesian skripsi draft to change the research population or focus. Common scenarios:
- Community-focused → Student-focused (measuring learning outcomes instead of public awareness)
- Student-focused → Teacher-focused (professional development instead of learning)
- General population → Specific stakeholder group

## Systematic Changes Required

When pivoting research population, changes must cascade through multiple sections. **Do not just search-and-replace** - each section needs contextually appropriate modifications.

### BAB 1 Changes

#### 1.1 Latar Belakang
**Add 1-2 paragraphs** explaining the new population's relationship to the research object:
- Why this population matters
- What gap exists for this population
- How the research addresses their specific needs

**Example (community → students):**
```
bagi siswa kelas XI Program Keahlian Pengawasan Mutu. Melalui website, siswa dapat 
mempelajari konsep brand awareness, strategi pemasaran digital, dan pentingnya positioning 
produk di pasar secara kontekstual.

Namun, siswa belum memiliki pengalaman langsung dalam memahami bagaimana brand awareness 
terbentuk dan bagaimana strategi pemasaran digital diterapkan. Oleh karena itu, pengembangan 
pemahaman siswa tentang konsep brand awareness melalui pembelajaran yang kontekstual.
```

**Technical approach:**
- Find the paragraph before "1.2 Identifikasi Masalah"
- Use `addnext()` with `deepcopy(pPr)` to preserve formatting
- Build paragraphs with mixed italic/bold segments for foreign terms

#### 1.3 Rumusan Masalah
**Modify research question 2** (or whichever question addresses effectiveness/impact):

**Before (community):**

**After (students):**

**Pattern:** Change the outcome measure and target population. For students, shift from "meningkatkan X di kalangan Y" to "sebagai media pembelajaran X bagi Y".

#### 1.4 Tujuan Penelitian
**Mirror the changes from Rumusan Masalah** - change verb from "Mengetahui efektivitas ... dalam meningkatkan" to "Mengetahui efektivitas ... sebagai media pembelajaran".

#### 1.5 Manfaat Penelitian
**Add a new stakeholder section** for the new population:

**Example (adding "Bagi Siswa"):**
```
Bagi Siswa
Meningkatkan pemahaman siswa tentang konsep brand awareness dan strategi pemasaran digital 
melalui pembelajaran kontekstual, memberikan pengalaman praktis dalam mengembangkan dan 
mengelola media pemasaran digital, serta meningkatkan kompetensi siswa dalam bidang 
kewirausahaan dan pemasaran digital yang relevan dengan dunia kerja.
```

**Insertion point:** After "Bagi Sekolah" or before "1.6 Batasan Masalah".

### BAB 2 Changes

#### Add Population-Specific Measurement Frameworks

When pivoting to students, you typically need to add **learning effectiveness measurement** tables/frameworks:

**Tabel 2.X: Indikator [Concept] untuk [Population]**
- Adapt existing indicators to the new population's context
- Example: Brand Awareness indicators with student-specific measurement examples

**Tabel 2.Y: Kategori Pengukuran Efektivitas**
- For students: N-Gain categories (Hake, 1999)
- For community: Gain Score or percentage increase
- For teachers: Professional competency rubrics

**Example N-Gain table:**
| Nilai N-Gain | Kategori | Interpretasi |
|--------------|----------|--------------|
| g ≥ 0,70 | Tinggi | Peningkatan pemahaman sangat efektif |
| 0,30 ≤ g < 0,70 | Sedang | Peningkatan pemahaman cukup efektif |
| g < 0,30 | Rendah | Peningkatan pemahaman kurang efektif |

**Insertion point:** Before "Kerangka Berpikir" or in a dedicated "Indikator Pengukuran" subsection.

#### Update Kerangka Berpikir
The conceptual framework diagram needs to reflect:
- New population in the "Proses" box
- New measurement approach (pre-test → intervention → post-test for students)
- New outcome indicators

## Technical Implementation Pattern

```python
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from copy import deepcopy

# 1. Find insertion point
idx_target = find_paragraph_by_text(doc, "1.2")  # or other anchor

# 2. Create new paragraph with preserved formatting
ref_p = doc.paragraphs[idx_target - 1]._element
new_p = OxmlElement('w:p')
ref_pPr = ref_p.find(qn('w:pPr'))
if ref_pPr is not None:
    new_p.append(deepcopy(ref_pPr))
ref_p.addnext(new_p)

# 3. Populate with mixed formatting
for i, p in enumerate(doc.paragraphs):
    if p._element is new_p:
        segments = [
            ('Regular text ', False, False),
            ('italic term', False, True),
            (' more text', False, False),
        ]
        for text, bold, italic in segments:
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.bold = bold
            run.italic = italic
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.27)
        set_line_spacing(p, 360)
        break

# 4. For modifying existing paragraphs (e.g., Rumusan Masalah)
p = doc.paragraphs[target_idx]
# Clear all runs
for r in list(p._element.findall(qn('w:r'))):
    p._element.remove(r)
# Rebuild with new content
for text, bold, italic in new_segments:
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = bold
    run.italic = italic
```

## Verification Checklist

After pivoting, verify consistency:
- [ ] All mentions of old population replaced in BAB 1
- [ ] Rumusan Masalah and Tujuan Penelitian mirror each other
- [ ] Manfaat section includes new population
- [ ] BAB 2 has appropriate measurement framework for new population
- [ ] Kerangka Berpikir reflects new population and measurement approach
- [ ] BAB 3 Metode Penelitian updated (partisipan, instrumen, analisis data)
- [ ] All foreign terms properly italicized

## Common Pitfalls

1. **Incomplete cascade**: Changing Rumusan Masalah but forgetting to update Tujuan Penelitian
2. **Wrong measurement framework**: Using N-Gain for community studies (should be Gain Score or percentage)
3. **Inconsistent terminology**: Mixing "siswa", "peserta didik", "pelajar" - pick one and stick to it
4. **Missing context in Latar Belakang**: Just stating the new population without explaining WHY they matter
5. **Forgetting BAB 3**: Partisipan section must match the new population

## Population-Specific Measurement Frameworks

| Population | Typical Framework | Citation |
|------------|-------------------|----------|
| Siswa (students) | N-Gain (pre-test/post-test) | Hake, 1999 |
| Masyarakat (community) | Gain Score, % peningkatan | Durianto dkk., 2017 |
| Guru (teachers) | Kompetensi profesional rubric | Permendikbud No. X |
| Industri (industry) | Kepuasan stakeholder, ROI | - |
