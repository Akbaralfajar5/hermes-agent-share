# Indonesian Seminar Proposal Presentation (Sidang Proposal Skripsi)

## When This Applies

User is an Indonesian university student preparing a slide deck for their **seminar proposal** (sidang proposal skripsi). They have a completed proposal (BAB I-III) and need a presentation summarizing it for their committee.

## Cross-Reference

The `word-documents` skill contains extensive detail on Indonesian skripsi structure (BAB I-III), UPI formatting rules, ADDIE methodology, and academic conventions. Load it alongside `powerpoint` when building a seminar proposal deck — it has the content knowledge; this file has the slide structure.

See `references/the operator-seminar-proposal-pptx-session.md` for a complete worked example (15-slide deck, 5-part incremental JS build, ADDIE two-part framing pitfall, audit results).

## ADDIE Two-Part Structure Pitfall

For R&D skripsi where ADDIE is used to develop a **website** (not a learning media), the research typically has **two separate parts**:

**Bagian 1 — Pengembangan Website (ADDIE):**
- Analysis → Design → Development → Implementation → Evaluation
- Implementation = deploy website + **uji kelayakan ~10 responden** (usability)
- Evaluation = simpulkan kelayakan dari validasi ahli + penilaian responden

**Bagian 2 — Uji Efektivitas (terpisah, setelah ADDIE selesai):**
- Desain: One-Group Pretest-Posttest (O₁ X O₂)
- Sampel: **berbeda** dari responden uji kelayakan (biasanya lebih besar, e.g. 30 warga)
- Alur: Pre-test → Treatment (akses website) → Post-test

**Common mistake:** mapping pre-test/post-test into the ADDIE Implementation phase. This is wrong — the effectiveness test is a separate research design that runs after ADDIE concludes.

**How to verify:** Read BAB III §3.5 (Prosedur Penelitian), specifically the paragraph describing Gambar 3.2. The two-part structure is usually stated explicitly there.



## Output Format Decision: HTML vs `.pptx`

**Default to native `.pptx` for sidang seminar deliverables.** Indonesian university dosen typically open the file in Microsoft PowerPoint or LibreOffice Impress on the sidang day, project from a laptop, and may need to make last-minute edits. An HTML-based deck (Reveal.js, custom HTML) does not satisfy these constraints:
- Cannot be edited natively in PowerPoint
- Requires browser + internet for CDN-loaded fonts
- May render differently across browsers
- Can't be inserted into a campus's pptx template

Use HTML decks ONLY when the user explicitly asks for one (e.g., "buat html aja", "presentasi web", "jadi web saja"). When in doubt or when the user just says "buat PPT" or "buat presentasi", produce `.pptx`.

If you've already produced an HTML version and the user requests a `.pptx`, **regenerate from scratch with python-pptx** — don't try to convert HTML→pptx programmatically (the result is invariably ugly with overlapping elements; user will say "ke tumpuk2 karena dirubah dari html").

## Tooling Choice: python-pptx vs pptxgenjs

Both work, but they have different strengths:

| Library | Strength | Weakness |
|---------|----------|----------|
| **python-pptx** (Python) | Precise coordinate control, inline `<w:t>`-equivalent XML manipulation, runs in same script as docx generation | Verbose, no built-in helpers for mixed-formatting text |
| **pptxgenjs** (Node) | Concise array-of-`{text, options}` syntax for mixed italic/bold, declarative JSON-ish | Some rendering inconsistencies in tables/shapes; need separate Node runtime |

**Default for sidang skripsi: python-pptx** — same Python runtime as docx generation, precise control prevents element overlap. Use pptxgenjs only when you need rapid mixed-formatting prototyping and the user is OK with the result.

**Critical for python-pptx:** disable shadow on every shape, set `text_frame.margin_*` to 0, use absolute Inches() positioning, set background via `slide.background.fill` (NOT a layered rect overlay).

```python
def add_round_rect(slide, x, y, w, h, fill_color, line_color=None, line_width=0.5, corner_pct=0.10):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = corner_pct  # corner radius as % of height
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color is not None:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False  # critical — disable inherited shadow
    if shape.has_text_frame:
        shape.text_frame.text = ''
    return shape
```

### Mixed italic/bold text in python-pptx

python-pptx requires building runs one-by-one inside paragraphs. Wrap it in a helper:

```python
def add_text_box(slide, x, y, w, h, segments, font='Calibri', size=14,
                 align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, font_color=TEXT_DARK):
    """segments = list of (text, fmt_dict) where fmt_dict can override
    bold, italic, color, size, font, char_spacing."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    for seg in segments:
        text, fmt = seg if isinstance(seg, tuple) else (seg, {})
        if '\n' in text:
            parts = text.split('\n')
            for pi, part in enumerate(parts):
                if pi > 0:
                    p = tf.add_paragraph()
                    p.alignment = align
                run = p.add_run()
                run.text = part
                _apply_fmt(run, fmt, font, size, font_color)
        else:
            run = p.add_run()
            run.text = text
            _apply_fmt(run, fmt, font, size, font_color)
```

### Dual-output projects (HTML + PPTX)

Some users want BOTH a polished HTML deck AND a `.pptx`. Treat them as **two independent codebases**:

- Don't try to share state between an HTML generator and a python-pptx generator
- Don't iterate on the HTML and then re-run the pptx script expecting them to stay in sync — they won't
- When the user changes content (e.g. "produksi sekarang 1× per minggu, bukan setiap semester"), update BOTH source scripts in the same turn, then regenerate both files
- When the user asks for "buat ulang lagi PPT-nya" after revisions, **delete the old `.pptx` first** and rebuild fresh — don't try to patch the existing file in place

User signal that PPT needs full rebuild: "ini ke tumpuk2 karena dirubah dari html", "rusak", "berantakan" — these mean previous edit attempts produced layout overlap, not just missing content. Always rebuild from scratch with python-pptx.

### pptxgenjs background callout

(reserved for future notes on background images / watermarks)

### Reusable pptxgenjs design system for academic decks

Standard color palette (Navy + Gold) that matches Indonesian university branding:
```js
const NAVY = '1E2761';        // primary
const NAVY_DARK = '0A0E27';   // dark slide backgrounds
const NAVY_LIGHT = '2A3A7D';  // gradients
const GOLD = 'D4A843';        // accent
const GOLD_BRIGHT = 'F0C75A'; // emphasis text on dark
const WHITE = 'FFFFFF';
const LIGHT_BG = 'FAF8F3';    // cream content slides
const TEXT_DARK = '0F172A';
const TEXT_SEC = '475569';
const TEXT_MUTED = '94A3B8';
const BORDER = 'E2E8F0';
```

Sandwich pattern: dark cover → light content → dark theory slides → light methodology → dark closing. Helps visually segment chapters of the proposal.

Standard slide layout (16:9, `LAYOUT_WIDE`, 13.333" x 7.5"):
- Eyebrow tag at y=0.4 (slide number + section label, gold caps + letter-spacing)
- Title at y=0.7, 32pt bold
- Subtitle at y=1.45, 14pt italic
- Content area starts y=2.0
- Page counter bottom-right at (12.0, 7.1)

### Italic foreign words inside pptxgenjs

pptxgenjs accepts arrays of `{text, options}` objects for mixed formatting. Build small helpers:

```js
function it(text)  { return { text, options: { italic: true } }; }
function tx(text, opts = {}) { return { text, options: opts }; }

s.addText([
  tx('Pengembangan Media Pemasaran Melalui ', { color: WHITE }),
  tx('Website', { color: GOLD_BRIGHT, italic: true }),
  tx(' untuk Meningkatkan ', { color: WHITE }),
  tx('Brand Awareness', { color: GOLD_BRIGHT, italic: true }),
  tx(' Produk ', { color: WHITE }),
  tx('Teaching Factory', { color: GOLD_BRIGHT, italic: true }),
], { x: 1.5, y: 1.4, w: 10.5, h: 2.5, fontSize: 28, fontFace: 'Calibri', bold: true, align: 'center' });
```

Apply italic to: *Website*, *Brand Awareness*, *Teaching Factory*, *Next.js*, *Vercel*, *TypeScript*, *Tailwind CSS*, *Web Analytics*, *Bounce Rate*, *Unique Visitors*, *Session Duration*, *Pages per Session*, *Returning Visitors*, *Real-time*, *R&D*, *ADDIE*, *Analysis*/*Design*/*Development*/*Implementation*/*Evaluation*, *Hand Sanitizer*, *Brand Recognition*/*Recall*, *Top of Mind*, *Marketing Mix*, *One Group Pretest-Posttest Design*, *Pre-test*/*Post-test*, *Paired Sample T-Test*, *Wilcoxon Signed Rank Test*, *p-value*, *framework*, *hosting*, *marketplace*, *web tracker*, *admin panel*, *CRUD*, etc.

Don't italicize KBBI loanwords: internet, digital, platform, data, media, file, aplikasi, sistem, mobile, smartphone, etc.

### Verification when `soffice` PDF conversion fails

In sandboxed environments, `libreoffice --headless --convert-to pdf` often errors with "javaldx" or "source file could not be loaded". **Two common root causes:**

1. **Missing `libreoffice-impress`** — the base install (e.g. on some Ubuntu sandboxes) only includes Writer + Math + Calc. Verify with `apt list --installed | grep libreoffice` and install if missing:
   ```bash
   sudo apt-get install -y libreoffice-impress
   ```
2. **Java profile lock + javaldx warning** — the warning itself is benign for plain pptx (no Java-dependent features), but profile lock conflicts cause the actual failure. Bypass with a fresh per-run user profile:
   ```bash
   libreoffice --headless \
     -env:UserInstallation=file:///tmp/lo_profile_$$ \
     --convert-to pdf deck.pptx
   ```

Once both issues are addressed, render to PNG via:
```bash
pdftoppm -jpeg -r 100 deck.pdf /tmp/qa/slide  # 100 DPI for QA inspection
# yields slide-01.jpg, slide-02.jpg, etc.
```

If LibreOffice still won't run, validate the .pptx structurally instead:

```bash
/usr/bin/python3 -c "
from pptx import Presentation
p = Presentation('/path/to/deck.pptx')
print(f'Slides: {len(p.slides)}')
print(f'Dimensions: {p.slide_width / 914400}\" x {p.slide_height / 914400}\"')
"
```

Expected for a widescreen sidang deck: 14 slides, 13.33" x 7.5". If structural validation passes, deliver the file — visual issues (if any) become a quick fix-cycle.

## Standard Slide Structure (10-15 slides)

| # | Slide | Content |
|---|-------|---------|
| 1 | **Cover** | Judul skripsi, nama, NIM, program studi, universitas, logo, tahun, nama dosen pembimbing |
| 2 | **Latar Belakang** | 3-4 bullet points summarizing the problem (from BAB I §1.1) |
| 3 | **Identifikasi & Rumusan Masalah** | Numbered list of research questions (from BAB I §1.2-1.3) |
| 4 | **Tujuan Penelitian** | Numbered list matching rumusan masalah (from BAB I §1.4) |
| 5 | **Manfaat Penelitian** | Teoritis + Praktis, brief (from BAB I §1.5) |
| 6 | **Kajian Pustaka** | Key theories — 2-3 main concepts with brief definitions (from BAB II) |
| 7 | **Penelitian Terdahulu** | Table: Author, Year, Title, Method, Key Finding (from BAB II) |
| 8 | **Kerangka Berpikir** | Visual diagram: Problem → Solution → Measurement → Expected Result |
| 9 | **Metode Penelitian** | R&D model (e.g., ADDIE), population/sample, instruments overview (from BAB III) |
| 10 | **Prosedur Penelitian** | ADDIE phases diagram or flowchart (from BAB III §3.4) |
| 11 | **Desain Produk** | Sitemap + 1-2 wireframe screenshots (from BAB III §3.4.2 / Lampiran) |
| 12 | **Instrumen Penelitian** | Summary table of instruments (from BAB III §3.5) |
| 13 | **Teknik Analisis Data** | Bagian 1: Persentase Kelayakan (Arikunto, 2013). Bagian 2: Gain Score + % Peningkatan + Uji Normalitas (Shapiro-Wilk) + Paired T-Test / Wilcoxon. **Do NOT use N-Gain** — it was rejected by dosen for brand awareness (non-cognitive variable). Use Gain Score = Post-test − Pre-test instead. |
| 14 | **Timeline Penelitian** | Gantt chart or table of research phases + months |
| 15 | **Terima Kasih** | Closing slide with contact info or university logo |

## Building the Deck — Format Choice

**Default to native `.pptx` from scratch via pptxgenjs, NOT HTML-to-PPTX conversion.**

### Why this matters
Trying to "convert" an HTML deck to PowerPoint (e.g. exporting Reveal.js → save as PPT, or screenshotting slides into PPT) consistently produces overlapping elements. The user reports "ke tumpuk-tumpuk" (everything stacked / overlapping) because:
- HTML uses CSS flex/grid which doesn't translate cleanly to PPT's absolute positioning
- Decorative animations and layered z-index become collisions
- Font/spacing don't survive the round-trip

If user wants both formats, **build them as parallel deliverables** — one HTML version (Reveal.js or game-box style), one native PPTX via pptxgenjs. Don't try to convert between them.

### pptxgenjs setup for Indonesian seminar proposal
```javascript
const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.333" x 7.5" 16:9 — standard for projector
pres.title = 'Seminar Proposal Skripsi - ...';

// Define design tokens centrally
const C = {
  navy: '1E2761', navyDark: '0A0E27', navyMid: '14193A', navyLight: '2A3A7D',
  gold: 'D4A843', goldBright: 'F0C75A', goldSoft: 'FBF3DC',
  white: 'FFFFFF', bgLight: 'FAF8F3', textDark: '0F172A',
  textSec: '475569', textMute: '94A3B8', border: 'E2E8F0',
};
const F = { head: 'Calibri', body: 'Calibri', mono: 'Consolas' };

// Helper for italic foreign words inside addText arrays
const tx = (text, opts = {}) => ({ text, options: opts });
const it = (text, opts = {}) => ({ text, options: { italic: true, ...opts } });

// Slide masters with thin gold accent line at top
pres.defineSlideMaster({
  title: 'DARK',
  background: { color: C.navyDark },
  objects: [{ rect: { x: 0, y: 0, w: 13.333, h: 0.08, fill: { color: C.gold } } }],
});
pres.defineSlideMaster({
  title: 'LIGHT',
  background: { color: C.bgLight },
  objects: [{ rect: { x: 0, y: 0, w: 13.333, h: 0.08, fill: { color: C.gold } } }],
});
```

### Italic foreign words in PPTX text
Mixed-formatting text in pptxgenjs requires array-of-objects syntax. For Indonesian slides where every foreign word must be italic:
```javascript
slide.addText([
  tx('Pengembangan Media Pemasaran Melalui ', { color: C.white }),
  it('Website', { color: C.goldBright }),  // italic
  tx(' untuk Meningkatkan ', { color: C.white }),
  it('Brand Awareness', { color: C.goldBright }),
  tx(' Produk ', { color: C.white }),
  it('Teaching Factory', { color: C.goldBright }),
], { x: 1, y: 1.6, w: 11.3, h: 2.6, fontSize: 30, bold: true, align: 'center' });
```

### Reusable header helper
```javascript
function addSlideHeader(slide, num, section, title, tagline, isDark = false) {
  const eyeColor = isDark ? C.gold : C.navy;
  const titleColor = isDark ? C.white : C.textDark;
  const tagColor = isDark ? 'B0BEC5' : C.textSec;
  slide.addText(`${num} · ${section}`, {
    x: 0.6, y: 0.4, w: 6, h: 0.3,
    fontSize: 10, bold: true, color: eyeColor, charSpacing: 6,
  });
  slide.addText(title, {
    x: 0.6, y: 0.7, w: 12.1, h: 0.7,
    fontSize: 32, fontFace: F.head, bold: true, color: titleColor,
  });
  if (tagline) {
    slide.addText(tagline, {
      x: 0.6, y: 1.45, w: 12.1, h: 0.4,
      fontSize: 14, italic: true, color: tagColor,
    });
  }
}

function addPageNum(slide, num, total = 14, isDark = false) {
  slide.addText([
    tx(String(num).padStart(2, '0'), { color: isDark ? C.gold : C.navy, bold: true }),
    tx(` / ${total}`, { color: isDark ? '6B7280' : C.textMute }),
  ], { x: 12.0, y: 7.1, w: 0.9, h: 0.3, fontSize: 10, fontFace: F.mono, align: 'right' });
}
```

### Building large scripts incrementally
For a 14+ slide deck, the JS source is ~1000 lines. Don't try to write it as one giant string. Pattern that works:
1. Write `pptx_part1.js` with header + slides 1-3
2. Write `pptx_part2.js` with slides 4-5
3. ... etc
4. Concatenate all parts: `cat pptx_part*.js > Build.js`
5. Run: `node Build.js`

This avoids hitting tool input limits and makes debugging easier — if part 4 breaks, you only re-run part 4.

### Verifying the PPTX
LibreOffice headless conversion may fail in sandboxed environments (java/javaldx errors). Validate via python-pptx instead:
```python
from pptx import Presentation
p = Presentation('output.pptx')
print(f'Slides: {len(p.slides)}')
print(f'Dimensions: {p.slide_width / 914400}" x {p.slide_height / 914400}"')
# Should be 13.33" x 7.50" for LAYOUT_WIDE
```

### Common pitfalls in pptxgenjs
- **Don't use `{0,7}` for transparency** — pptxgenjs uses `transparency: 92` (0-100, percent), not 0-1 alpha
- **Bullet code** — use `bullet: { code: '25CF' }` for filled circle (●), not `bullet: true` which gives default bullet
- **Number circles** — use `pres.ShapeType.ellipse` + addText with `align: 'center', valign: 'middle'` for badge-style numbers
- **Text inside shapes** — addText with same `x,y,w,h` as the shape automatically overlays it; no need for separate positioning
- **Text run italic in tables** — table cell text supports the same `[{ text, options }]` array syntax as addText, but tables sometimes ignore the italic option for very small fontSize. Bump to ≥10pt.
- **Right arrows between flow steps** — use `pres.ShapeType.rightArrow` filled with gold, positioned in the gap between cards. Don't try to draw with lines.



### Color Palette
- Use **university brand colors** if known (e.g., UPI uses blue/gold)
- Safe academic palette: Navy (#1E2761) + White + Gold accent (#D4A843)
- Avoid flashy/neon colors — committee expects professional, not creative
- Dark title slide + light content slides ("sandwich" structure)

### Typography
- Title slides: 36-44pt bold
- Slide headers: 28-32pt bold
- Body text: 18-22pt (must be readable from back of room)
- Minimum text size: 16pt — anything smaller won't be visible during sidang
- Font: use clean sans-serif (Calibri, Arial) or match university template if provided

### Content Rules
- **Maximum 6-7 bullet points per slide** — committee reads slides while listening
- **No full paragraphs** — use concise phrases, not sentences from the skripsi
- **Tables over text** for penelitian terdahulu and instruments
- **Diagrams over bullets** for methodology and kerangka berpikir
- **Include page/section references** (small text, bottom corner) so committee can find details in the proposal document

### Common Mistakes
- Copying entire paragraphs from skripsi onto slides (too dense)
- Missing dosen pembimbing name on cover slide
- Wrong year on cover (always verify current year!)
- No slide numbers
- Forgetting to include kerangka berpikir diagram
- Too many slides (>18) — committee gets impatient
- Too few slides (<10) — looks unprepared

### What Committee Typically Asks About
These slides should be especially strong because they draw the most questions:
1. **Rumusan masalah** — must be clear and answerable
2. **Kerangka berpikir** — logical flow from problem to solution
3. **Metodologi** — why this model? why this sample size?
4. **Instrumen** — validity, reliability plans
5. **Analisis data** — which statistical tests and why

## Year Awareness

**CRITICAL:** Always verify the current year before putting it on the cover slide. Do NOT hardcode or assume — ask the user or check context. This was a major correction in prior sessions.

### Cover-slide year/decoration overlap pitfall

Cover slides commonly stack a giant year display ("2026") in a corner over
the author/dosen-pembimbing block. Two specific failure modes seen in past
sidang decks:

- **Oversized year textbox** — e.g. `L=9.0 T=6.0 W=4.0 H=1.5` collides with
  the "Program Studi..." block at `L=1.0 T=5.5 W=11.3 H=0.85` and the
  "DOSEN PEMBIMBING" block at `L=2.5 T=6.4 W=8.3 H=0.85`. Symptoms in the
  audit: `TEXT-OVERLAP "2026" / "Program Studi..."`.
- **Decorative auto-shape off-canvas** — corner accent circles/blobs sized
  4-6" placed at slide corners often overflow the 13.33×7.5 page. Flagged
  by the audit as `OVERFLOW-PAGE` on slide 1 or the "Terima Kasih" closer.

Fix patterns:
- Move the year to a smaller textbox (e.g. `W=2.0 H=0.5`) tucked under the
  logo or above the title, NOT in the bottom-right where the dosen block
  lives.
- For decorative shapes: keep them either entirely on-canvas, or ensure
  they're meant to be clipped — if clipped they should be bottom z-order
  with no text.
- Always run `scripts/audit_layout.py` on the cover slide first; it
  exposes both issues in one shot.

## Companion Deliverable: Speaker Notes (Naskah Presentasi)

Users often need a **full speaker script** as a separate `.docx` file alongside the slide deck. This is the naskah/penjelasan they'll practice reading before the seminar.

### Structure of Speaker Notes Document

```
NASKAH PRESENTASI SEMINAR PROPOSAL
[Nama] — NIM [NIM]

SLIDE 1: COVER
[Instruksi: Berdiri, sapa dewan penguji]
"Bismillahirrahmanirrahim. Assalamualaikum..."
[Full opening script with self-introduction]

SLIDE 2: LATAR BELAKANG
[Instruksi: Klik slide berikutnya]
"Baik, saya akan mulai dari latar belakang..."
[Narration expanding on each bullet point]

... (one section per slide) ...

SLIDE N: PENUTUP
[Closing script + wassalamualaikum]

TIPS PRESENTASI
1. Waktu: 15-20 menit
2. Kontak mata: lihat penguji, jangan baca slide
3. Tempo: jangan terlalu cepat, beri jeda
4. Percaya diri

ANTISIPASI PERTANYAAN PENGUJI
Q: [Common question]
A: [Suggested answer]
... (5-8 anticipated questions)
```

### Common Anticipated Questions (R&D Website Skripsi)

Include answers for these in the speaker notes:
1. Kenapa website, bukan media sosial / marketplace?
2. Kenapa model ADDIE, bukan Waterfall / Prototype?
3. Bagaimana mengukur brand awareness? (pre-post test, Aaker pyramid)
4. Apa kelebihan framework yang dipilih vs alternatif?
5. Bagaimana validasi kelayakan? (ahli media, ahli materi, black box testing)
6. Berapa jumlah sampel dan kenapa? (Sugiyono criteria)
7. Apa batasan penelitian ini?

### Creating the Speaker Notes .docx

Use `python-docx` with formatting:
- Slide titles: Heading 1, colored (match deck primary color)
- Instructions: italic, pink/accent color, 11pt
- Speech text: normal 12pt, 1.5 line spacing
- Tips section: numbered list on new page
- Q&A section: bold questions, indented answers

**Proactively offer to create speaker notes** after delivering the slide deck — users almost always need them.

## Asking the User

Before creating, ask for:
1. Nama lengkap + NIM
2. Program studi + fakultas + universitas
3. Nama dosen pembimbing (pembimbing I dan II jika ada) — optional, skip if user doesn't mention
4. Apakah ada template PPT dari kampus/prodi?
5. Tahun berapa di cover?
6. Apakah ada logo universitas yang perlu dimasukkan?

**Note:** If the user only provides name + NIM and says "go", proceed without asking for pembimbing — they can add it later. Don't block progress on optional fields.
