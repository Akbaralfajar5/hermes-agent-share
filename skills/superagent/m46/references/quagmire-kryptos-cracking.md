# Quagmire III / Kryptos Cipher Cracking

## Context
The CIA Kryptos sculpture (and Paradigm's Kryptos CTF) uses **Quagmire III** cipher:
- A keyed alphabet (e.g., keyword "KRYPTOS" → `KRYPTOSABCDEFGHIJLMNQUVWXZ`)
- A separate encryption key (e.g., "PROVENANCE")
- Decrypt: `P[i] = alpha[(alpha.index(C[i]) - alpha.index(K[i%kl])) % 26]`

## Identification Signals
- IC ≈ 0.04 (polyalphabetic, not monoalphabetic)
- Grid displayed in 26 columns (matches alphabet length)
- "Kryptos-style" mentioned in challenge description
- Best IC per key-length analysis shows spike at true key length

## Proven Cracking Workflow (PK1 solved in session)

### Step 1: Extract & Analyze
```python
from collections import Counter

# IC calculation
freq = Counter(ciphertext)
n = len(ciphertext)
ic = sum(f*(f-1) for f in freq.values()) / (n*(n-1))
# English: ~0.0667, Random: ~0.0385, Vigenere: ~0.04

# Find key length via average IC per group
for kl in range(1, 25):
    groups = [ct[i::kl] for i in range(kl)]
    avg_ic = mean([ic_of(g) for g in groups])
    # Spike above 0.06 = likely key length
```

### Step 2: Dictionary Attack with Keyed Alphabet
```python
def make_keyed_alphabet(keyword):
    seen = set()
    alpha = []
    for c in keyword.upper():
        if c not in seen:
            alpha.append(c); seen.add(c)
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if c not in seen:
            alpha.append(c); seen.add(c)
    return ''.join(alpha)

def quagmire3_decrypt(ct, key, alphabet):
    result = []
    for i, c in enumerate(ct):
        key_pos = alphabet.index(key[i % len(key)])
        ct_pos = alphabet.index(c)
        result.append(alphabet[(ct_pos - key_pos) % 26])
    return ''.join(result)

# Attack: try all dictionary words as keys
# with known alphabet keyword (e.g., KRYPTOS)
kryptos_alpha = make_keyed_alphabet('KRYPTOS')
for word in dictionary:
    plain = quagmire3_decrypt(ct, word, kryptos_alpha)
    if score_english(plain) > threshold:
        print(f"Key={word}: {plain}")
```

### Step 3: Score English Plaintext
```python
def score_english(text):
    score = 0
    trigrams = ['THE','AND','ING','HER','FOR','THA','ENT','ION','TER','WAS',...]
    for t in trigrams: score += text.count(t) * 3
    quadgrams = ['TION','THER','WITH','THAT','THIS','HAVE','FROM','THERE',...]
    for q in quadgrams: score += text.count(q) * 6
    return score
```

### Step 4: If Alphabet Unknown — Multi-Alphabet Sweep
Try multiple alphabet keywords × full dictionary:
- Kryptos-related: KRYPTOS, PALIMPSEST, ABSCISSA, SANBORN
- Theme-related: PARADIGM, CIPHER, CRYPTO, ENIGMA, ARCHIVE, PROVENANCE
- From solved puzzle plaintexts (each puzzle may hint at next)

## Key Findings from Paradigm Kryptos CTF
- PK1: alphabet=KRYPTOS, key=PROVENANCE (10 letters), 192 chars
- Puzzles get progressively harder (PK1 easiest, PK10 hardest)
- PK8-10 likely use different cipher types or combination ciphers
- IC analysis: PK8 best KL=16, PK9 best KL=7 or 14, PK10 very flat IC
- Standard dictionary attacks fail on PK8+ (scores stay below 30)
- Harder puzzles may use: multi-word keys, different alphabet per puzzle,
  combination ciphers (Vigenere + transposition), or entirely different cipher types

## Pitfalls
- `bs58` npm v5 exports `bs58.decode` directly, NOT `bs58.default.decode`
- Quagmire III ≠ standard Vigenere — the keyed alphabet changes letter positions
- IC spike at KL=N also means KL=2N is valid — always check divisors
- Hill climbing with bigram scoring can find false positives (score 90+ but garbled)
- For CTF puzzles: check if solved puzzles' plaintexts contain hints for later puzzles
