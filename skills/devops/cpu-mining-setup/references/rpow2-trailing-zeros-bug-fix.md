# RPOW2 Trailing Zeros Bug Fix (May 10, 2026)

## Critical Bug Discovery

**Date:** May 10, 2026  
**Impact:** All Python miner solutions rejected with `INVALID_SOLUTION: hash does not meet difficulty`  
**Root cause:** `count_trailing_zeros()` function counted from **wrong end** of hash

## The Bug

Original implementation (BROKEN):

```python
def count_trailing_zeros(hash_bytes):
    """Count trailing zero bits in hash (little-endian bit order)"""
    count = 0
    for byte in hash_bytes:  # ❌ WRONG: iterates from START
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count
```

**Problem:** Iterates from byte 0 (start of hash), counting **leading zeros** instead of **trailing zeros**.

Example hash: `000000bebe4b878efc7b774e51e363bd01459a30476040c20fca45c3d73525bb`
- Leading zeros (from start): 6 bytes = 48 bits ✓ (what the broken code counted)
- Trailing zeros (from end): 0 bits (ends with `bb` = `10111011`) ✗ (what RPOW2 API expects)

## The Fix

Corrected implementation:

```python
def count_trailing_zeros(hash_bytes):
    """Count trailing zero bits in hash (from the END/LSB)"""
    count = 0
    for byte in reversed(hash_bytes):  # ✅ FIXED: iterate from END
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count
```

**Key change:** `for byte in reversed(hash_bytes)` — iterate from last byte to first.

## Verification

Test case from failed mining attempt:

```python
import hashlib
import struct

prefix_hex = "9145312c7a0b5168c0afbf404a74815d"
nonce = 25716535
difficulty = 25

prefix = bytes.fromhex(prefix_hex)
data = prefix + struct.pack('<Q', nonce)
h = hashlib.sha256(data).digest()

print(f"Hash: {h.hex()}")
# Output: 000000bebe4b878efc7b774e51e363bd01459a30476040c20fca45c3d73525bb

# Broken version (counts from start)
def count_trailing_zeros_broken(hash_bytes):
    count = 0
    for byte in hash_bytes:
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count

# Fixed version (counts from end)
def count_trailing_zeros_fixed(hash_bytes):
    count = 0
    for byte in reversed(hash_bytes):
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count

broken_result = count_trailing_zeros_broken(h)
fixed_result = count_trailing_zeros_fixed(h)

print(f"Broken version: {broken_result} trailing zeros")  # 25 (WRONG)
print(f"Fixed version: {fixed_result} trailing zeros")    # 0 (CORRECT)
print(f"Required: {difficulty} bits")
print(f"Broken passes: {broken_result >= difficulty}")    # True (FALSE POSITIVE)
print(f"Fixed passes: {fixed_result >= difficulty}")      # False (CORRECT)
```

**Result:**
- Broken version: 25 trailing zeros (actually leading zeros) → passes check → **submitted to API → rejected**
- Fixed version: 0 trailing zeros → fails check → continues mining → **finds real solution**

## Impact Timeline

1. **May 10, 06:41 AM** — Miner started with v2 (broken trailing zeros)
2. **06:45 AM** — First solution found (nonce 25716535) → submitted → **rejected with 400 INVALID_SOLUTION**
3. **06:46 AM** — Bug identified via manual hash verification
4. **06:46 AM** — Fixed `count_trailing_zeros()` to use `reversed(hash_bytes)`
5. **06:47 AM** — Miner restarted with fix → **first successful mint in 30 seconds**

## Symptoms

If you see this error pattern, you have the bug:

```
[+] FOUND! Nonce: 25716535
[+] Time: 32.0s
[-] Mint failed: 400 {"error":"INVALID_SOLUTION","message":"hash does not meet difficulty"}
```

**Diagnosis:**
- Miner finds solutions quickly (good sign)
- All solutions rejected by API (bad sign)
- Hash has leading zeros but not trailing zeros

## Fix Deployment

All Python miner versions updated:

- `rpow2_miner_v2.py` → patched May 10, 06:46 AM
- `rpow2_miner_v3_windows.py` → includes fix from start
- `rpow2_miner_v4_optimized.py` → includes fix from start

**Action required:** If using old v2, re-download or apply patch manually.

## Lesson Learned

**Always verify mining logic against API requirements:**
1. Test with known challenge/nonce pairs
2. Verify hash meets difficulty before submitting
3. Check API error messages for clues ("`hash does not meet difficulty`" was the hint)

**Trailing zeros ≠ Leading zeros** in proof-of-work systems. RPOW2 uses **trailing zeros** (LSB), not leading zeros (MSB).
