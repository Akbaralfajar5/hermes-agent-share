# rpow2 API Protocol (Reverse Engineered)

Complete API protocol for rpow2.com mining, reverse-engineered from Rust miner source code.

## API Endpoints

**Base URL:** `https://api.rpow2.com`

### POST /challenge

Get mining challenge.

**Request:**
```bash
curl -X POST https://api.rpow2.com/challenge \
  -H "Cookie: rpow_session=YOUR_SESSION_COOKIE"
```

**Response (200 OK):**
```json
{
  "challenge_id": "965d517b-3526-4b8a-9f7f-4fd79f02017c",
  "nonce_prefix": "a3f2c1",
  "difficulty_bits": 25
}
```

**Error responses:**
- `401 Unauthorized` — Invalid or expired session cookie
- `503 Service Unavailable` — API down (common, retry after 5-10s)

### POST /mint

Submit found nonce to mint tokens.

**Request:**
```bash
curl -X POST https://api.rpow2.com/mint \
  -H "Cookie: rpow_session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "965d517b-3526-4b8a-9f7f-4fd79f02017c",
    "solution_nonce": "618501"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "balance": 171002136120
}
```

**Error responses:**
- `400 Bad Request` — Invalid nonce or challenge_id
- `503 Service Unavailable` — API down

### GET /me

Get account info and balance.

**Request:**
```bash
curl https://api.rpow2.com/me \
  -H "Cookie: rpow_session=YOUR_SESSION_COOKIE"
```

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "balance": 171002136120,
  "minted": 171002136120,
  "sent": 0,
  "received": 0
}
```

**Balance units:** Base units (divide by 1,000,000,000 for rpow2 tokens)

## Mining Algorithm

### Step 1: Get Challenge

POST to `/challenge` to get:
- `challenge_id` (UUID)
- `nonce_prefix` (hex string, e.g., "a3f2c1")
- `difficulty_bits` (typically 25)

### Step 2: Find Valid Nonce

**Goal:** Find a nonce such that `SHA256(prefix_bytes + nonce_bytes)` has at least `difficulty_bits` trailing zero bits.

**Implementation (Python):**

```python
import hashlib

def find_nonce(nonce_prefix, difficulty, start_nonce, end_nonce):
    # Convert hex prefix to bytes
    prefix_bytes = bytes.fromhex(nonce_prefix)
    
    for nonce in range(start_nonce, end_nonce):
        # Create hash: prefix + nonce (little endian)
        data = prefix_bytes + nonce.to_bytes(8, byteorder='little')
        hash_result = hashlib.sha256(data).digest()
        
        # Count trailing zero bits
        trailing_zeros = 0
        for byte in reversed(hash_result):
            if byte == 0:
                trailing_zeros += 8
            else:
                # Count trailing zeros in this byte
                trailing_zeros += (byte & -byte).bit_length() - 1
                break
        
        if trailing_zeros >= difficulty:
            return nonce
    
    return None
```

**Key details:**
- Nonce is encoded as **8-byte little-endian** integer
- Hash is SHA256 (not double SHA256 like Bitcoin)
- Trailing zeros are counted from the **end** of the hash (reverse byte order)
- Difficulty 25 bits = ~33 million hashes on average

### Step 3: Submit Nonce

POST to `/mint` with:
- `challenge_id` (from step 1)
- `solution_nonce` (as string, e.g., "618501")

**Important:** `solution_nonce` must be a string, not an integer.

## Multi-Threading Strategy

**Pattern:** Divide nonce search space among threads.

```python
threads = 3
chunk_size = 100_000_000  # 100M nonces per thread

for i in range(threads):
    start = i * chunk_size
    end = start + chunk_size
    # Thread i searches nonces from start to end
```

**Why this works:** Nonce space is huge (2^64), so collision between threads is negligible.

**Optimization:** Use `concurrent.futures.ThreadPoolExecutor` with `as_completed()` to cancel other threads as soon as one finds a valid nonce.

## Session Cookie Format

**Cookie name:** `rpow_session`

**Format:** JWT (JSON Web Token)

**Example:**
```
rpow_session=eyJlbWFpbCI6ImFrYmFyYWxwYWphcjVAZ21haWwuY29tIiwiZXhwIjoxNzgwODQzNjU4fQ.GShkyCeG_9TMhkFL5uLua5iPDmWm_xlWNhTpup3trtU
```

**Decoded payload:**
```json
{
  "email": "you@example.com",
  "exp": 1780843658
}
```

**Expiry:** Check `exp` field (Unix timestamp). Cookie expires ~30 days after login.

**How to get cookie:**
1. Login to rpow2.com in browser
2. Open DevTools (F12) → Application → Cookies → rpow2.com
3. Copy value of `rpow_session` cookie

## API Reliability

**Common issues:**
- `503 Service Unavailable` — API down for maintenance (happens frequently)
- `502 Bad Gateway` — Cloudflare/nginx error (transient)
- `401 Unauthorized` — Cookie expired (get new cookie)

**Mitigation:**
- Retry on 503/502 with exponential backoff (5s, 10s, 30s)
- Never exit on API errors — log and retry
- Use watchdog to auto-restart if miner crashes

## Performance Benchmarks

| Hardware | Threads | Speed | Blocks/min |
|----------|---------|-------|------------|
| VPS (2 cores, 2 GHz) | 2 | 0.06-3.31s | 6-10 |
| Zo.computer (3 cores, 1.8 GHz) | 3 | 0.5-2.5s | 8-12 |
| Threadripper PRO 7985WX | 6 | 0.06-0.47s | ~20 |

**Key insight:** Python miner is only 2-3x slower than Rust for this workload (SHA256 is CPU-bound, not language-bound).

## Reward Economics

**Reward per block:** 0.000015258 rpow2 (fixed)

**Nerf history:**
- Before nerf: ~1 rpow2 per 5 minutes = 288 rpow2/day
- After nerf (99.84%): 0.001555 rpow2 per 5 minutes = 0.448 rpow2/day

**Break-even analysis:**
- VPS cost: $101/month (QuickPod Threadripper)
- Earnings: 13.44 rpow2/month
- Break-even price: $7.51 per rpow2

**Conclusion:** Only profitable if rpow2 lists at $10+ per token.
