#!/usr/bin/env python3
"""
check_overclaim.py — automated first-pass grader for a draft vulnerability report.

Companion to references/disproof-first-validation-gate.md (§8 overclaim detector).

What it does:
  1. Flags risky overclaim vocabulary, distinguishing terms already hedged
     ("hypothetical", "not tested") from unhedged ones.
  2. Checks that the mandatory report sections are present (EN + ID synonyms).
  3. Counts concrete evidence references (HTTP exchanges, status codes,
     artifact IDs, hashes, timestamps).

What it does NOT do:
  It does not judge whether the finding is valid. It is a triage aid that points
  a human at the sentences most likely to be rejected. A flagged phrase is not
  wrong — it just requires explicit supporting evidence.

Usage:
    python check_overclaim.py report.md
    python check_overclaim.py report.md --json

Calibration (do this before trusting it): run it against BOTH a deliberately
overclaiming draft and an honest one. If it cannot separate them, it is not
doing anything and the thresholds need work.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Vocabulary that must have explicit supporting evidence when used.
OVERCLAIM_TERMS = {
    'critical_hit': [
        'rce', 'remote code execution', 'account takeover', 'full account takeover',
        'database compromise', 'arbitrary file read', 'arbitrary file write',
        'full compromise', 'root access', 'admin access', 'sql injection',
    ],
    'scope_inflation': [
        'all users', 'any account', 'any user', 'tenant-wide', 'production-wide',
        'everyone', 'seluruh user', 'semua user', 'semua akun', 'seluruh akun',
        'semua tenant', 'lintas tenant', 'entire database',
    ],
    'certainty_inflation': [
        'guaranteed', 'trivial', 'definitely', 'certainly', 'undoubtedly',
        'pasti bisa', 'dijamin', 'tanpa syarat', 'selalu berhasil',
    ],
    'vague_severity': [
        'very critical', 'extremely critical', 'super critical', 'catastrophic',
    ],
    'hedge_without_label': [
        'could lead to', 'might allow', 'possibly allows', 'may result in',
        'bisa berujung', 'dapat menyebabkan', 'berpotensi',
    ],
}

# Markers that a claim IS already labelled as uncertain / evidenced.
# Their presence in the surrounding window downgrades a flag.
HEDGE_MARKERS = [
    'hypothetical', 'hypothetically', 'not tested', 'untested', 'unverified',
    'needs_evidence', 'hipotetis', 'belum diuji', 'tidak diuji', 'belum terbukti',
    'demonstrated', 'terbukti', 'observed', 'teramati',
]

# Mandatory report sections, mapped to EN + ID synonyms.
# A section counts as present if ANY synonym appears.
REQUIRED_SECTIONS = {
    'prasyarat / preconditions': ['precondition', 'prasyarat'],
    'reproduksi / reproduction': ['reproduction', 'reproduksi', 'langkah repro'],
    'expected behavior': ['expected behavior', 'expected', 'harapan', 'perilaku yang diharapkan'],
    'actual behavior': ['actual behavior', 'actual', 'aktual', 'perilaku aktual', 'yang terjadi'],
    'impact / dampak': ['impact', 'dampak'],
    'bukti / evidence': ['evidence', 'bukti'],
    'batasan / limitations': ['limitation', 'limitations', 'batasan', 'keterbatasan', 'tidak diuji'],
    'severity': ['severity', 'tingkat keparahan'],
}


def load(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


def find_terms(text):
    """Find overclaim phrases with context and whether they are hedged."""
    low = text.lower()
    hits = []
    for category, terms in OVERCLAIM_TERMS.items():
        for t in terms:
            for m in re.finditer(re.escape(t), low):
                start = max(0, m.start() - 90)
                end = min(len(text), m.end() + 90)
                window = low[start:end]
                hits.append({
                    'term': t,
                    'category': category,
                    'context': text[start:end].replace('\n', ' ').strip(),
                    'hedged': any(h in window for h in HEDGE_MARKERS),
                })
    return hits


def check_sections(text):
    low = text.lower()
    return [
        label for label, synonyms in REQUIRED_SECTIONS.items()
        if not any(s in low for s in synonyms)
    ]


def check_evidence_refs(text):
    """Concrete artifacts, so 'evidence' is not just an assertion."""
    patterns = {
        'http_exchange': r'(GET|POST|PUT|PATCH|DELETE)\s+/\S+',
        'status_code': r'\b[1-5]\d\d\b',
        'artifact_id': r'\bEV-\d+\b',
        'hash_or_id': r'\b[a-f0-9]{16,}\b',
        'timestamp': r'\d{4}-\d{2}-\d{2}',
    }
    return {name: len(re.findall(pat, text, re.I)) for name, pat in patterns.items()}


def main():
    ap = argparse.ArgumentParser(description="Overclaim grader for a draft vuln report.")
    ap.add_argument('file', help="Report to check (markdown/text)")
    ap.add_argument('--json', action='store_true', help="Machine-readable output")
    args = ap.parse_args()

    if not Path(args.file).exists():
        print(f"[!] File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    text = load(args.file)
    hits = find_terms(text)
    missing = check_sections(text)
    refs = check_evidence_refs(text)
    unhedged = [h for h in hits if not h['hedged']]

    if args.json:
        print(json.dumps({
            'file': args.file,
            'total_flags': len(hits),
            'unhedged_flags': len(unhedged),
            'hits': hits,
            'missing_sections': missing,
            'evidence_refs': refs,
        }, indent=2, ensure_ascii=False))
        return

    print("=" * 68)
    print(f"OVERCLAIM CHECK — {Path(args.file).name}")
    print("=" * 68)

    print(f"\n[1] RISKY PHRASES: {len(hits)} found "
          f"({len(unhedged)} not hedged as hypothetical)\n")

    if not hits:
        print("    (no risky phrases detected)")
    else:
        seen = set()
        for h in unhedged:
            key = (h['term'], h['category'])
            if key in seen:
                continue
            seen.add(key)
            print(f"  [!] [{h['category']}] \"{h['term']}\"")
            print(f"      context: ...{h['context']}...")
            print(f"      -> needs explicit evidence, or mark hypothetical, or remove.")
            print(f"         (A flagged phrase is NOT automatically wrong.)")
            print()
        hedged = [h for h in hits if h['hedged']]
        if hedged:
            print(f"  [i] {len(hedged)} phrase(s) already hedged/tested - likely OK, still review.")

    print(f"\n[2] MISSING REQUIRED SECTIONS: {len(missing)}\n")
    if not missing:
        print("    [OK] all required sections detected")
    else:
        for m in missing:
            print(f"  [!] not found: '{m}'")
        print("\n    'limitations' is the most commonly omitted section -")
        print("    and its absence is what makes a report read as an overclaim.")

    print(f"\n[3] EVIDENCE REFERENCES\n")
    for k, v in refs.items():
        print(f"  {'[OK]' if v else '[!] '} {k}: {v}")
    if refs['http_exchange'] == 0 and refs['artifact_id'] == 0:
        print("\n    No concrete request/artifact detected.")
        print("    Check: is the raw evidence preserved and referenced?")

    print(f"\n{'='*68}")
    print("NOTE: this is a triage aid. Human judgement makes the final call.")
    print("A risky phrase is not wrong - it just requires evidence.")
    print(f"{'='*68}")


if __name__ == '__main__':
    main()
