# Paradigm Kryptos CTF — Cipher Cracking Methodology

## Context
Paradigm's Kryptos CTF (paradigm.xyz/kryptos-ctf) features 10 puzzles (PK1-PK10) of increasing difficulty.
All are "Kryptos-style" — based on the CIA Kryptos sculpture cipher techniques.
$1,000 prize per puzzle (first solver wins).

## PK1 Solution (Solved)
- **Cipher**: Quagmire III (same as original Kryptos K1/K2)
- **Alphabet keyword**: KRYPTOS → keyed alphabet: KRYPTOSABCDEFGHIJLMNQUVWXZ
- **Encryption key**: PROVENANCE (dictionary word)
- **Plaintext**: "INVESTIGATION LOG ITEM EIGHT KNOT TIGHTLY WOUND ITS THREAD INSCRIBED WITH LETTERS THE ACCESSION LOG SAYS ONCE UNRAVELED IT REVEALS THE ROUTE TO THE LOST ARCHIVE OF PELLEGRIN TWELVE PRIOR ARCHIVISTS TRIED TO UNRAVEL IT ALL FAILED"

## Cracking Approach (Quagmire III / Keyed Vigenere)

### Step 1: Index of Coincidence
```python
# IC close to 0.04 (random) = polyalphabetic cipher
# Test IC for different key lengths — peak indicates correct length
for kl in range(1, 20):
    avg_ic = ic_for_keylength(ciphertext, kl)
```

### Step 2: Identify Cipher Type
- IC ≈ 0.04 + "Kryptos-style" = Quagmire III with keyed alphabet
- Original Kryptos uses: KRYPTOS keyed alphabet + dictionary word key

### Step 3: Dictionary Attack on Key
```python
# Load /usr/share/dict/american-english (104K words)
# apt-get install wamerican if missing
# For each word, try as key with KRYPTOS keyed alphabet
# Score plaintext with English trigram/word frequency
for word in dictionary:
    plain = quagmire3_decrypt(ciphertext, word, kryptos_alpha)
    score = score_english(plain)
```

### Step 4: Quagmire III Decrypt Function
```python
def make_keyed_alphabet(keyword):
    seen = set()
    alpha = []
    for c in keyword.upper():
        if c not in seen and c.isalpha():
            alpha.append(c)
            seen.add(c)
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if c not in seen:
            alpha.append(c)
            seen.add(c)
    return ''.join(alpha)

def quagmire3_decrypt(ct, key, alphabet):
    result = []
    for i, c in enumerate(ct):
        key_pos = alphabet.index(key[i % len(key)])
        ct_pos = alphabet.index(c)
        offset = (ct_pos - key_pos) % 26
        result.append(alphabet[offset])
    return ''.join(result)
```

### Step 5: Scoring Function
```python
def score_english(text):
    score = 0
    for p in ['THE','AND','ING','HER','FOR','THA','ENT','ION','TER','WAS']:
        score += text.count(p) * 3
    for p in ['TION','THER','WITH','THAT','THIS','HAVE','FROM','THERE','WHICH']:
        score += text.count(p) * 6
    return score
```

## Key Insights for Harder Puzzles (PK8-PK10)
1. Alphabet keyword might NOT be "KRYPTOS" for later puzzles
2. Key might be multi-word or non-dictionary
3. Could use different Quagmire variants (I, II, IV)
4. Could layer ciphers (transposition + substitution)
5. Submission requires X (Twitter) login on paradigm.xyz
6. PK1-PK7 already solved; PK8-PK10 still open

## Submission
- Sign in with X account at paradigm.xyz/kryptos-ctf
- Click "Decrypt PKn" button
- Submit plaintext (likely uppercase, no spaces)
