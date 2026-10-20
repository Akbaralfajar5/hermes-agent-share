# Skripsi/Thesis → Journal Article Conversion

Convert a full Indonesian skripsi (BAB I–V, ~60-150 pages) into a publishable IMRAD journal article (~8-15 pages).

## When to Use

- User says "buat artikel dari skripsi saya" or "jadikan artikel jurnal"
- User has a completed skripsi and wants to submit to a national/accredited journal
- Target: national journals (Sinta, accredited) or conference proceedings

## Conversion Mapping

| Skripsi Chapter | Journal Section | Notes |
|---|---|---|
| Cover + Judul | Title | Shorten if needed, remove "Skripsi" label |
| Abstrak (ID + EN) | Abstract (EN + ID) | Restructure into Objective/Method/Results/Conclusion |
| BAB I Pendahuluan | 1. PENDAHULUAN | Condense latar belakang → 3-4 paragraphs. Keep only: context, problem, gap, contribution. Cut institutional details. |
| BAB II Kajian Pustaka | → merged into Pendahuluan | DO NOT keep as separate section. Extract ONLY concepts needed to contextualize the study (1-2 paragraphs max in Introduction). |
| BAB III Metode | 2. METODE | Condense: ADDIE/design, subjects, instruments, analysis technique. Keep replication-sufficient detail. |
| BAB IV Hasil & Pembahasan | 3. HASIL DAN PEMBAHASAN | Keep 3 main findings max. Lead with the strongest quantitative result. Merge temuan + pembahasan per sub-section. |
| BAB V Simpulan | 4. SIMPULAN | Condense 3 conclusions into one flowing paragraph + 1 implication paragraph. |
| Daftar Pustaka | DAFTAR PUSTAKA | Pare down from 30+ to 10-12 most essential references. Keep only cited in article body. |

## Workflow

### 1. READ the skripsi
Extract key data points before writing:

```
Content to extract           | Source
─────────────────────────────|────────────────────
Full abstract text           | Abstrak
Research title               | Cover
Research questions (3 max)   | BAB I (1.2 Rumusan Masalah)
Method (design, samples,     | BAB III
  instruments, analysis)
Validation scores (%)        | BAB IV (Kelayakan sub-section)
Pre-test / Post-test means   | BAB IV (Efektivitas sub-section)
Gain score + %               | BAB IV (Efektivitas sub-section)
Statistical test results     | BAB IV (t-value, p-value)
Student response scores      | BAB IV (Tanggapan Siswa)
Core conclusions              | BAB V (5.1 Simpulan)
```

### 2. STRUCTURE the article

**Title** — 12-16 words, no "Skripsi" label. Drop institutional abbreviation unless essential.

**Abstract (EN + ID)** — Each ~200 words, structured:
- *EN:* Objective / Method / Results / Conclusion / Keywords
- *ID:* Tujuan / Metode / Hasil / Kesimpulan / Kata Kunci
- Self-contained (no citations, no undefined acronyms)

**1. PENDAHULUAN** — 4-6 paragraphs:
2. Problem: what's missing in current practice
3. Theoretical grounding: brand awareness theory
4. Research gap + ADDIE framework
5. Research questions (3 concise statements)

**2. METODE** — 3-4 paragraphs:
1. Design and development model (ADDIE steps summary)
2. Subjects and sampling (who, how many, how selected)
3. Instruments (what was measured, how)
4. Data analysis (descriptive, gain score, t-test/Wilcoxon)

**3. HASIL DAN PEMBAHASAN** — 3 sub-sections:
- 3.1 Kelayakan — expert validation scores (individual + average + category)
- 3.2 Tanggapan Siswa — per-indicator scores + overall
- 3.3 Efektivitas — pre/post means, gain score, t-test results, significance

Each sub-section: present data FIRST, then interpret (compare with prior studies).

**4. SIMPULAN** — 1 paragraph:
- Restate 3 findings as complete sentences
- 1-2 sentences on implications/practical significance

**DAFTAR PUSTAKA** — 10-12 references max:
- Keep: foundational references (Arikunto, Sugiyono, Keller, Kotler, Branch)
- Keep: directly compared prior studies (Nurmilah, Cartoyo)
- Cut: peripheral references only used in BAB II lit review
- Cut: redundant citations of the same concept

### 3. FORMAT for journal submission

| Element | Standard |
|---|---|
| Font | Times New Roman 12pt |
| Spacing | Double (2.0) — some journals want 1.5 |
| Margins | 2.54 cm all sides |
| Title | Bold, 14pt, centered |
| Abstract | Justified, 12pt, italic label prefixes (Objective/Method) |
| Headings | Bold, 12pt, centered (H1) or left-aligned (H2) |
| Body | Justified, first-line indent 1.27 cm |
| References | Single spacing, hanging indent 1.27 cm, APA style |

### 4. Write bilingual abstract

```python
# Pattern for abstract sections
def add_abstract_block(doc, label, text):
    p = doc.add_paragraph()
    r1 = p.add_run(f"{label}: ")
    r1.bold = True
    r2 = p.add_run(text)
    # both TNR 12pt
```

### 5. Pare references strategically

Keep ≈10-12 from the original 30+. Selection rubric:
- **Always keep:** method references (Sugiyono, Arikunto, Branch), brand theory (Keller, Durianto), digital marketing (Chaffey, Kotler)
- **Keep if cited in body:** directly-compared prior studies (Nurmilah, Cartoyo)
- **Cut safely:** peripheral theories only cited in BAB II, redundant citations for same concept, institutional documents (Direktorat PSMK) unless key to the argument

## Pitfalls

- ❌ Keeping BAB II as a separate "Kajian Pustaka" section — journals use IMRAD; lit review goes into Introduction (2-3 sentences max)
- ❌ Including all 3+ research questions verbatim — condense into one paragraph
- ❌ Reporting every sub-indicator score — only report the most meaningful (highest, lowest, and overall)
- ❌ Keeping the full 30+ references — journals limit to 10-20, and reviewers notice padding
- ❌ Writing abstract before the body — always write abstract LAST (it summarises what you actually wrote)
- ❌ Using "Skripsi" or "Tugas Akhir" language in the article — this is a journal article, not a thesis
- ❌ Explaining ADDIE in too much detail — journals want the method, not a textbook explanation of the model
