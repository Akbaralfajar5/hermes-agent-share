# Custom Python Miner for rpow2

## Overview

Alternative to Rust GitHub miner (`rizkypujir/miner`). No compile time, instant deployment, comparable performance.

## Performance

- **Speed:** 1.40s per block (vs 0.06-3.31s for Rust miner on same hardware)
- **Success rate:** 100% in testing
- **Deployment time:** <1 minute (vs 3-5 minutes for Rust compile)
- **Dependencies:** Python 3 + `requests` (usually pre-installed)

## Protocol Reverse Engineering

### API Endpoints

```
POST https://api.rpow2.com/challenge
  Headers: Cookie: rpow_session=...
  Response: {
    "challenge_id": "uuid",
    "nonce_prefix": "hex_string",
    "difficulty_bits": 25
  }

POST https://api.rpow2.com/mint
  Headers: Cookie: rpow_session=...
  Body: {
    "challenge_id": "uuid",
    "solution_nonce": "integer_as_string"
  }
  Response: 200 OK on success

GET https://api.rpow2.com/me
  Headers: Cookie: rpow_session=...
  Response: {
    "email": "user@example.com",
    "balance": 171002136120  // base units
  }
```

### Mining Algorithm

1. **Get challenge:** POST /challenge returns `challenge_id`, `nonce_prefix` (hex), `difficulty_bits`
2. **Find nonce:**
   - Convert `nonce_prefix` from hex to bytes
   - For each nonce (0 to N):
     - Compute: `SHA256(prefix_bytes + nonce.to_bytes(8, 'little'))`
     - Count trailing zero bits in hash
     - If `trailing_zeros >= difficulty_bits`: valid nonce found
3. **Submit:** POST /mint with `challenge_id` and `solution_nonce` (as string)

### Key Implementation Details

**Trailing Zero Bit Counting:**
```python
trailing_zeros = 0
for byte in reversed(hash_result):
    if byte == 0:
        trailing_zeros += 8
    else:
        trailing_zeros += (byte & -byte).bit_length() - 1
        break
```

**Nonce Encoding:** Little-endian 8-byte integer (not hex string)

**Multi-threading:** Divide nonce search space by thread count, first thread to find valid nonce cancels others

## Deployment Script

See `templates/python-miner-deploy.sh` for full deployment script.

**One-liner for zo.computer:**
```bash
mkdir -p ~/rpow2-python-miner && cd ~/rpow2-python-miner && \
curl -sSL [DEPLOY_SCRIPT_URL] | bash
```

## Advantages Over Rust Miner

1. **No compile time** — 3-5 minutes saved per deployment
2. **Easier to customize** — Python vs Rust for quick tweaks
3. **Fewer dependencies** — No Rust toolchain needed
4. **Comparable performance** — Python hashlib is C-optimized
5. **Better for rapid iteration** — Edit and re-run instantly

## Disadvantages

1. **Slightly slower** — ~20-30% slower than optimized Rust (but reward already nerfed 99.84%, so speed less critical)
2. **No static binary** — Requires Python 3 runtime
3. **Memory overhead** — Python interpreter overhead vs compiled binary

## When to Use

- **Fast deployment needed** — Bulk VPS setup, time-sensitive
- **Prototyping/testing** — Quick validation before Rust implementation
- **Low-stakes mining** — Reward already nerfed, performance difference negligible
- **Python-friendly environment** — Python pre-installed, Rust not

## When to Use Rust Miner

- **Maximum performance** — Every millisecond counts
- **Long-running production** — Static binary, lower memory
- **Embedded/constrained** — Minimal runtime dependencies
