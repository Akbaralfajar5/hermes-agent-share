#!/usr/bin/env python3
"""
Audit a .pptx for layout problems before opening it visually.

Detects:
  1. Shapes that overflow slide bounds (right or bottom edge past page).
  2. Text-on-text overlap — two TEXT_BOX shapes whose bounding boxes
     overlap by >0.2" in both axes AND both contain non-empty text.
     Skips badge-sized boxes (<0.55") so step-circles, numbered bullets,
     and tiny accent labels don't generate false positives.

Usage:
    python audit_layout.py path/to/deck.pptx

Exit code 0 always. Prints findings to stdout, one per line.
Run before declaring a deck "done" — catches the kind of overlap users
report as "ketimpa-timpa" / "tumpang tindih" / "overlap" without you
having to render to PDF first.

Limitations:
  - Cannot detect text overflow inside a single textbox (text taller
    than container). For that, render to PDF + visual inspection.
  - Cannot detect z-order issues where a shape covers a textbox
    without their bounding boxes both containing text.
  - Treats non-textbox shapes (AUTO_SHAPE backgrounds, etc.) as
    decorative — only TEXT_BOX vs TEXT_BOX is flagged.

Tunables (edit constants below):
  EDGE_TOLERANCE_EMU — how far past the slide edge counts as overflow.
  OVERLAP_MIN_EMU    — required overlap in BOTH axes to flag.
  BADGE_AREA_EMU2    — boxes smaller than this (area) are ignored as
                       badges/icons/single-digit labels.
"""
import sys
from pptx import Presentation

EDGE_TOLERANCE_EMU = 50_000        # ~0.05"
OVERLAP_MIN_EMU = 200_000          # ~0.22"
BADGE_AREA_EMU2 = 500_000 * 500_000  # ~0.55" square


def audit(path: str) -> list[str]:
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    issues: list[str] = []

    for i, slide in enumerate(prs.slides, 1):
        boxes = []
        for j, shape in enumerate(slide.shapes):
            try:
                l = shape.left or 0
                t = shape.top or 0
                w = shape.width or 0
                h = shape.height or 0
                text = shape.text_frame.text if shape.has_text_frame else ""
                boxes.append((j, l, t, l + w, t + h, w, h, text, str(shape.shape_type)))
            except Exception:
                pass

        # 1. shapes overflowing the slide
        for j, l, t, r, bo, w, h, text, st in boxes:
            if r > sw + EDGE_TOLERANCE_EMU or bo > sh + EDGE_TOLERANCE_EMU:
                issues.append(f'S{i} #{j} OVERFLOW-PAGE "{text[:40]}"')

        # 2. text-vs-text overlap
        text_boxes = [b for b in boxes if "TEXT_BOX" in b[8]]
        for ia in range(len(text_boxes)):
            a = text_boxes[ia]
            for ib in range(ia + 1, len(text_boxes)):
                b = text_boxes[ib]
                ox = max(0, min(a[3], b[3]) - max(a[1], b[1]))
                oy = max(0, min(a[4], b[4]) - max(a[2], b[2]))
                if ox > OVERLAP_MIN_EMU and oy > OVERLAP_MIN_EMU and a[7].strip() and b[7].strip():
                    if min(a[5] * a[6], b[5] * b[6]) < BADGE_AREA_EMU2:
                        continue
                    issues.append(
                        f'S{i} #{a[0]} <-> #{b[0]} TEXT-OVERLAP '
                        f'"{a[7][:30]}" / "{b[7][:30]}"'
                    )
    return issues


def main():
    if len(sys.argv) != 2:
        print("usage: audit_layout.py <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    issues = audit(sys.argv[1])
    if issues:
        print("\n".join(issues))
    else:
        print("no major layout issues from coordinates alone")


if __name__ == "__main__":
    main()
