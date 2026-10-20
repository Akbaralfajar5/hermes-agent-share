# Kryptos-Style Quagmire III Cipher Cracking

## Context
Paradigm's Kryptos CTF (paradigm.xyz/kryptos-ctf) uses Quagmire III ciphers — the same type as the real CIA Kryptos sculpture (K1/K2). Successfully cracked PK1 in June 2026.

## Cipher Identification

### Indicators of Quagmire III / Kryptos-style cipher:
- Index of Coincidence (IC) ≈ 0.038-0.045 (near random, polyalphabetic)
- Best IC spike at a specific key length (e.g., KL=10 gave IC=0.076)
- Context mentions "Kryptos", cryptographic puzzles, or CIA sculpture
- Grid of uppercase letters with no spaces

### IC Analysis Steps:
```python
# 1. Calculate overall IC
ic = sum(f*(f-1) for f in freq.values()) / (n*(n-1))
# English: ~0.0667, Random: ~0.0385

# 2. Test key lengths 1-20, find which gives highest average IC per column
def ic_for_keylength(ct, kl):
    groups = ['' for _ in range(kl)]
    for i, c in enumerate(ct):
        groups[i % kl] += c
    return mean([ic_of(g) for g in groups])
```

## Quagmire III Decryption

### How it works:
- **Keyed alphabet**: Take a keyword (e.g., "KRYPTOS"), remove duplicates, append remaining letters → `KRYPTOSABCDEFGHIJLMNQUVWXZ`
- **Encryption key**: A separate word (e.g., "PROVENANCE")
- **Decrypt**: For each position i, find key_char position in keyed alphabet, find ciphertext_char position in keyed alphabet, plaintext = alphabet[(ct_pos - key_pos) % 26]

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

## Attack Strategy (Dictionary Attack)

### What worked for PK1:
1. Determine key length via IC analysis (KL=10 had IC=0.076)
2. Assume KRYPTOS keyed alphabet (standard for Kryptos-style puzzles)
3. Dictionary attack on the key word using `/usr/share/dict/american-english`
4. Score plaintext candidates with English trigram/word matching

```python
# Install wordlist: sudo apt-get install -y wamerican
# Filter: 3-12 char alpha-only words
# For each word, decrypt and score

def score_english(text):
    score = 0
    for p in ['THE','AND','ING','HER','FOR','THA','ENT','ION','TER','WAS',
              'HIS','NOT','ARE','BUT','HAD','HAS','WIT','ALL','CAN','ERE']:
        score += text.count(p) * 3
    for p in ['TION','THER','WITH','THAT','THIS','HAVE','FROM','THEY',
              'BEEN','WERE','WHAT','WHEN','THERE','WHICH','THEIR']:
        score += text.count(p) * 6
    return score
```

### Key insight: Try words starting with "PRO-" first
The PK1 key was "PROVENANCE" — thematic (provenance = origin/history of an artifact). CTF keys are often thematically related to the puzzle narrative.

## PK1 Solution (Paradigm Kryptos CTF)
- **Cipher**: Quagmire III
- **Alphabet keyword**: KRYPTOS → `KRYPTOSABCDEFGHIJLMNQUVWXZ`
- **Encryption key**: PROVENANCE (10 letters, matching IC peak)
- **Plaintext**: "INVESTIGATION LOG ITEM EIGHT KNOT TIGHTLY WOUND ITS THREAD INSCRIBED WITH LETTERS THE ACCESSION LOG SAYS ONCE UNRAVELED IT REVEALS THE ROUTE TO THE LOST ARCHIVE OF PELLEGRIN TWELVE PRIOR ARCHIVISTS TRIED TO UNRAVEL IT ALL FAILED"

## Alphabets to Try (priority order for Kryptos-style CTFs):
1. KRYPTOS → `KRYPTOSABCDEFGHIJLMNQUVWXZ` (original Kryptos)
2. PARADIGM → `PARDIGMBCEFHJKLNOQSTUVWXYZ` (CTF host)
3. Standard → `ABCDEFGHIJKLMNOPQRSTUVWXYZ` (plain Vigenere)
4. Any thematic keyword from the puzzle context

## Pitfalls
- `bs58` npm v5 exports `bs58.decode` directly, NOT `bs58.default.decode` — check version
- IC near 0.04 does NOT mean random — it means polyalphabetic with key length > 5
- Hill-climbing Vigenere works poorly on short texts (<200 chars) — dictionary attack is faster
- Standard Vigenere (no keyed alphabet) will NOT crack Quagmire III even with correct key
- Always try Quagmire III BEFORE standard Vigenere for Kryptos-themed puzzles
