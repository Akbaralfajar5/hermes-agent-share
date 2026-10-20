# Handwritten Scans & Arabic/Complex-Script DOCX


## Pipeline

1. **Extract page images from the PDF**:
   - `pdftoppm -r 100 file.pdf page` — rendered pages, good default
   - `pdfimages -png file.pdf orig` — original embedded scans (often 300dpi, highest fidelity)
2. **Pillow preprocessing** — the biggest accuracy lever for handwriting:
   ```python
   from PIL import Image, ImageOps, ImageEnhance, ImageFilter
   img = Image.open("page-1.png").convert("L")
   img = ImageOps.autocontrast(img, cutoff=2)
   img = ImageEnhance.Contrast(img).enhance(1.6)
   img = ImageEnhance.Sharpness(img).enhance(1.8)
   # If background noise still kills OCR, binarize instead:
   img = img.resize((1240, 1753))                 # ~150dpi A4 — tesseract prefers this size
   img = img.point(lambda p: 255 if p > 140 else 0)
   img = img.filter(ImageFilter.MedianFilter(3))
   img.save("page-1-bin.png")
   ```
3. **tesseract with multiple psm modes** — run several and compare outputs, don't trust a single pass (6 = uniform block, 4 = columns, 11 = sparse text, 3 = auto):
   ```bash
   for psm in 6 4 11 3; do tesseract page-1-bin.png out-$psm -l ind --psm $psm; done
   ```
4. **Better language models**: `tessdata_best` beats the default fast models. Download `<lang>.traineddata` from the `tesseract-ocr/tessdata_best` GitHub repo into a custom dir and run `TESSDATA_PREFIX=/path/to/dir tesseract ...`.

## Known limits — do not fabricate

- **Arabic-script handwriting is essentially unrecoverable** (best models recovered ~1 short line per page). Do not present guesses as text: ask the user for the Arabic text (or clear per-line photos) and insert it verbatim. Mark unverified passages in the output and tell the user exactly which parts need their verification — an honest partial reconstruction beats a confident wrong one.

## Arabic text in the output DOCX (python-docx)

1. Install an Arabic-capable font (Amiri) user-level — from `github.com/google/fonts`, folder `ofl/amiri` (Amiri-Regular.ttf, Amiri-Bold.ttf) into `~/.local/share/fonts`, then `fc-cache -f`.
2. `run.font.name` only sets `w:ascii`/`w:hAnsi`; Arabic glyphs render via the **complex-script slot** — set `w:cs` explicitly on the run's `rPr/rFonts` (keep Times New Roman on the Latin slots):
   ```python
   from docx.oxml.ns import qn
   rPr = run._element.get_or_add_rPr()
   rFonts = rPr.get_or_add_rFonts()
   rFonts.set(qn('w:cs'), 'Amiri')
   ```
3. Convert to PDF with `soffice --headless --convert-to pdf out.docx` — it renders the installed font correctly; verify the output with `pdftotext` / `pdfinfo`.
