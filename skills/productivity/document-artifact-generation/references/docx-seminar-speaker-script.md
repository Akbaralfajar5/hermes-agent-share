# DOCX Seminar Speaker Script Generation

## When to Use
User has a presentation (HTML/PPTX/PDF) for seminar hasil/proposal/sidang and needs:
1. A timed speaker script (what to say per slide)
2. Anticipated dosen penguji questions + suggested answers
3. Delivered as a printable DOCX

## Workflow

1. **Extract slide content** — read the HTML/PPTX source to get:
   - Slide titles and order
   - Data tables, numbers, percentages
   - Theory references (authors, years)
   - Method descriptions (design, samples, instruments)
   - Dosen names (pembimbing, penguji)

2. **Generate DOCX** with python-docx:
   - **Cover page**: Title, student info, "Waktu: X Menit"
   - **Daftar isi**
   - **Time allocation table**: per slide with duration
   - **Script per slide**: use `add_script()` for spoken text (italic, indented, gray)
   - **Anticipated questions**: grouped by category (Methodology, Results, Technical, "Hardball")
   - **Tips page**: angka kunci table, presentation tips

3. **Deliver via Telegram Bot API** (NOT send_message MEDIA: tag — see pitfalls)

## DOCX Structure Template

```
Page 1:  Cover (judul, NIM, dosen, tahun)
Page 2:  Daftar Isi
Page 3+: Alokasi Waktu table
         Script per Slide (each as: heading → italic script body → navigation note)
         Prediksi Pertanyaan (grouped: Metodologi, Hasil, Teknis, Hardball)
         Tips Presentasi + Angka Kunci table
```

## Script Formatting Convention
- **Spoken text** = italic, indented 0.5cm, gray color (#333333), 10.5pt
- **Slide navigation** = normal body text, e.g. "[Klik → Slide 3]"
- **Section headers** = H2 with colored accent
- **Question text** = H3, quote-style ("Mengapa X?")

## Time Allocation Guide (10-minute seminar)
| Phase | Duration |
|-------|----------|
| Opening (salam, intro, judul) | 30s |
| Per Rumusan Masalah | 30-45s each |
| Landasan Teori | 60s |
| Penelitian Terdahulu | 45s |
| Metode | 90s |
| Hasil per RM | 60-120s each |
| Simpulan | 30s |
| Demo + Closing | 15s |

## Anticipated Questions Pattern

Always generate 10-15 questions grouped into:
- **Methodology** (design choice, sample size, statistical test justification)
- **Per RM** (why certain indicators, interpretation of numbers, low/high scores)
- **Technical** (tool/tech stack choices, sustainability)
- **Hardball** (weaknesses, contributions, "what would you do differently")

Each answer should:
1. Acknowledge the question
2. Give a reasoned academic answer
3. Reference the data/standard when applicable
4. Acknowledge limitations honestly where relevant

## Key Pitfalls
- Don't read script verbatim — script is a guide, not a teleprompter
- Always include "angka kunci" that must be memorized (percentages, t-value, p-value, n)
- For Indonesian academic context: include formal salam opening/closing
- Dosen penguji names must match the presentation exactly
