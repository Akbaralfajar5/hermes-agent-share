# rpow2 API Protocol

Reverse-engineered from Rust miner source code (`rizkypujir/miner`).

## Base URL
```
https://api.rpow2.com
```

## Authentication
All requests require session cookie:
```
Cookie: rpow_session=eyJlbWFpbCI6...
```

## Endpoints

### GET /me
Get account information.

**Request:**
```http
GET /me HTTP/1.1
Host: api.rpow2.com
Cookie: rpow_session=...
```

**Response:**
```json
{
  "email": "user@example.com",
  "balance": 171002136120
}
```

**Notes:**
- Balance in base units (divide by 1e9 for display value)
- Returns 401 if cookie invalid/expired

### POST /challenge
Request mining challenge.

**Request:**
```http
POST /challenge HTTP/1.1
Host: api.rpow2.com
Cookie: rpow_session=...
```

**Response:**
```json
{
  "challenge_id": "965d517b-3526-4b8a-9f7e-4fd79f02017c",
  "nonce_prefix": "a3f2c1",
  "difficulty_bits": 25
}
```

**Notes:**
- `challenge_id`: UUID for this challenge
- `nonce_prefix`: Hex string to prepend to nonce
- `difficulty_bits`: Required trailing zero bits in hash (typically 25)
- Challenge expires after ~5 minutes
- Returns 503 if API overloaded

### POST /mint
Submit solution nonce.

**Request:**
```http
POST /mint HTTP/1.1
Host: api.rpow2.com
Cookie: rpow_session=...
Content-Type: application/json

{
  "challenge_id": "965d517b-3526-4b8a-9f7e-4fd79f02017c",
  "solution_nonce": "618501"
}
```

**Response (Success):**
```http
HTTP/1.1 200 OK
```

**Response (Failure):**
```http
HTTP/1.1 400 Bad Request
{"error": "Invalid nonce"}
```

**Notes:**
- `solution_nonce` must be string, not integer
- Returns 400 if nonce invalid
- Returns 409 if challenge already solved
- Returns 410 if challenge expired

## Mining Algorithm

### Step 1: Get Challenge
```python
resp = requests.post('https://api.rpow2.com/challenge', 
                     headers={'Cookie': 'rpow_session=...'})
data = resp.json()
challenge_id = data['challenge_id']
nonce_prefix = data['nonce_prefix']
difficulty = data['difficulty_bits']
```

### Step 2: Find Valid Nonce
```python
import hashlib

prefix_bytes = bytes.fromhex(nonce_prefix)

for nonce in range(0, 100_000_000):
    # Combine prefix + nonce (little-endian 8 bytes)
    data = prefix_bytes + nonce.to_bytes(8, byteorder='little')
    
    # SHA256 hash
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
    
    # Check if valid
    if trailing_zeros >= difficulty:
        return nonce  # Found valid nonce!
```

### Step 3: Submit Nonce
```python
resp = requests.post('https://api.rpow2.com/mint',
                     headers={'Cookie': 'rpow_session=...'},
                     json={
                         'challenge_id': challenge_id,
                         'solution_nonce': str(nonce)
                     })

if resp.status_code == 200:
    print("Minted!")
```

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue mining |
| 400 | Invalid nonce | Bug in mining logic |
| 401 | Unauthorized | Cookie expired, re-login |
| 404 | Endpoint not found | Check URL/method |
| 409 | Challenge already solved | Get new challenge |
| 410 | Challenge expired | Get new challenge |
| 503 | Service unavailable | Wait 5-10 min, retry |

## Rate Limiting

No explicit rate limits observed, but:
- API may return 503 under heavy load
- Multiple accounts from same IP work fine
- Same cookie on multiple VPS works fine (no per-device limit)

## Reward Structure

- **Reward per block:** 0.000015258 rpow2 (fixed)
- **Blocks per minute:** ~6-20 (depends on CPU speed)
- **Earnings per day:** ~0.13-0.48 rpow2 (2-8 cores)

**Note:** Reward was nerfed 99.84% in May 2026 (was ~1 rpow2 per 5 min, now 0.001555 rpow2 per 5 min).

## Multi-Threading Strategy

Divide nonce search space across threads:

```python
chunk_size = 100_000_000  # 100M nonces per thread
threads = 4

for i in range(threads):
    start_nonce = i * chunk_size
    end_nonce = start_nonce + chunk_size
    # Search range [start_nonce, end_nonce) in thread i
```

First thread to find valid nonce cancels others and submits.

## Cookie Expiration

- Cookies expire after ~30 days
- Expiry timestamp in JWT payload: `{"email":"...","exp":1780843658}`
- Decode: `echo 'eyJlbWFpbCI6...' | base64 -d`
- When expired, re-login to get new cookie

## Getting Cookie

1. Login to rpow2.com
2. Open DevTools (F12)
3. Application → Cookies → rpow2.com
4. Copy `rpow_session` value
5. Format: `rpow_session=eyJlbWFpbCI6...`
