# Italic Foreign Words in HTML Slide Decks

## When This Applies

Indonesian academic presentations (sidang proposal, seminar) where the
deliverable is an HTML deck. UPI 2024 pedoman requires foreign words to
be italicized in BOTH the docx proposal AND any presentation derived
from it. Dosen will check.

## The Problem with Naive Replacement

You cannot just `html = html.replace('Teaching Factory', '<em>Teaching Factory</em>')`
because:

1. **CSS class names match** — class names like `class="brand-card"` would get
   wrapped in `<em>` if you target `brand`.
2. **Already-italic runs double-wrap** — leads to `<em><em>website</em></em>`
   nesting that breaks visual hierarchy.
3. **Inside `<script>` blocks** — JavaScript variable names, console logs,
   selectors get matched and break execution.
4. **Inside HTML attribute values** — `style="..."`, `data-*`, `aria-*`
   should never be touched.

## State Machine Pattern

Walk the body character-by-character, tracking whether you are:
- Inside a tag (between `<` and `>`)
- Inside an `<em>` block (don't double-italic)

Apply pattern matching only to text nodes. Save and restore `<script>` blocks
with sentinel placeholders before processing.

```python
import re

# 1. Split body from head/tail (preserve CSS, scripts, head completely)
body_start = html.find('<body>')
body_end   = html.rfind('</body>')
head = html[:body_start + len('<body>')]
body = html[body_start + len('<body>'):body_end]
tail = html[body_end:]

# 2. Save and remove script blocks with sentinels.
script_pattern = re.compile(r'<script\b[^>]*>.*?</script>', re.DOTALL)
scripts = []
def save_script(m):
    scripts.append(m.group())
    return f'\x00SCRIPT_{len(scripts)-1}\x00'
body_no_scripts = script_pattern.sub(save_script, body)

# 3. Build foreign-term pattern (longest first, letter-boundary lookarounds).
FOREIGN_TERMS = sorted([
    'Teaching Factory', 'Brand Awareness', 'Web Analytics',
    'Next.js', 'Vercel', 'TypeScript', 'website', 'framework',
    # ... full list lives in scripts/italicize_foreign_words.py
], key=lambda x: -len(x))
escaped = [re.escape(t) for t in FOREIGN_TERMS]
PATTERN = re.compile(r'(?<![A-Za-z<])(' + '|'.join(escaped) + r')(?![A-Za-z>])')

# 4. State machine: walk and italicize.
result, text_buf = [], []
i, n = 0, len(body_no_scripts)
in_em = False

def flush_text():
    if not text_buf:
        return
    text = ''.join(text_buf)
    text_buf.clear()
    if not in_em:                                  # critical: don't double-italic
        text = PATTERN.sub(r'<em>\1</em>', text)
    result.append(text)

while i < n:
    c = body_no_scripts[i]
    if c == '<':
        flush_text()
        j = body_no_scripts.find('>', i)
        if j < 0:
            result.append(body_no_scripts[i:]); break
        tag = body_no_scripts[i:j+1]
        result.append(tag)
        if tag.startswith('<em') and not tag.startswith('<em/'):
            in_em = True
        elif tag.startswith('</em'):
            in_em = False
        i = j + 1
    else:
        text_buf.append(c)
        i += 1
flush_text()

new_body = ''.join(result)

# 5. Restore script blocks.
for idx, scr in enumerate(scripts):
    new_body = new_body.replace(f'\x00SCRIPT_{idx}\x00', scr)

# 6. Add CSS rule if base styles strip italics.
italic_css = '\nem { font-style: italic; }\n'
new_html = (head + new_body + tail).replace('</style>', italic_css + '</style>', 1)
```

## Verification Checklist

Run all four after italicizing:

```python
# 1. Tag balance
content.count('<em>')   # number of opens
content.count('</em>')  # should be >= opens (some baseline </em> may exist for styling)

# 2. HTML parser sanity
from html.parser import HTMLParser
class V(HTMLParser):
    def __init__(self): super().__init__(); self.tags=[]; self.errors=[]
    def handle_starttag(self, tag, _attrs):
        if tag not in ('img','br','hr','meta','link','input'): self.tags.append(tag)
    def handle_endtag(self, tag):
        if self.tags and self.tags[-1]==tag: self.tags.pop()
        else: self.errors.append(f"mismatched {tag}")
v = V(); v.feed(content)
assert not v.errors, v.errors[:5]

# 3. Spot-grep visible occurrences
import subprocess
subprocess.run(['grep','-oE','<em>[^<]+</em>', path]).stdout

# 4. Look for missed lowercase variants — Indonesian sentences often start
# foreign words mid-sentence with lowercase ('brand awareness rendah').
# Run a second pass with lowercase terms to catch these.
```

## Two-Pass Pattern

Real session evidence: the first pass with capitalized terms missed
lowercase mid-sentence usage. Always do TWO passes:

1. Pass 1: capitalized + canonical forms (`Brand Awareness`, `Website`)
2. Pass 2: lowercase variants (`brand awareness`, `website`, `gain score`)

Both passes share the same state machine; only the term list differs.
The `in_em` guard prevents pass 2 from re-wrapping pass 1's output.

## Pitfalls

- **Don't run pattern over the full HTML string** — CSS/script will be corrupted.
- **Don't use simple `\b` word boundaries** — `Next.js`, `R&D`, `p-value` need
  letter-boundary lookarounds (`(?<![A-Za-z])` and `(?![A-Za-z])`).
- **Don't forget `em { font-style: italic; }`** if your reset CSS or component
  styles override default italics. Some Reveal.js themes do this.
- **Don't italicize inside `<title>`, `<meta name="description">`, etc.** —
  these aren't visual content. The state machine catches `<title>` because
  it tracks tags, but verify with grep.

## Related

- `scripts/italicize_foreign_words.py` (in word-documents skill) — same logic
  but for .docx files, run-level rebuild instead of HTML state machine.
- `references/indonesian-seminar-proposal-deck.md` — slide structure that
  this italic pass typically runs against.
