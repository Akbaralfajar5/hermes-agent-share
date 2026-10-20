# rpow2 Mining Protocol

Reverse-engineered from Rust miner source (rizkypujir/miner).

## API Endpoints

Base URL: `https://api.rpow2.com`

### POST /challenge
Get mining challenge.

**Request:**
```
POST /challenge
Cookie: rpow_session=<token>
```

**Response (200):**
```json
{
  "challenge_id": "uuid-string",
  "nonce_prefix": "hex-string",
  "difficulty_bits": 25
}
```

### POST /mint
Submit solution.

**Request:**
```json
{
  "challenge_id": "uuid-from-challenge",
  "solution_nonce": "integer-as-string"
}
```

**Response (200):** Success (minted)
**Response (503):** API temporarily unavailable (retry after 5s)

### GET /me
Get account info.

**Response:**
```json
{
  "email": "user@example.com",
  "balance": 171002136120  // base units, divide by 1e9 for tokens
}
```

## Mining Algorithm

1. **Get challenge** via POST /challenge
2. **Find nonce** that produces valid hash:
   - Concatenate: `nonce_prefix_bytes + nonce_u64_little_endian`
   - Hash with SHA256
   - Count trailing zero bits in hash
   - Valid if `trailing_zeros >= difficulty_bits`
3. **Submit nonce** via POST /mint

### Trailing Zero Bit Counting

```python
def count_trailing_zeros(hash_bytes):
    count = 0
    for byte in reversed(hash_bytes):
        if byte == 0:
            count += 8
        else:
            count += (byte & -byte).bit_length() - 1
            break
    return count
```

## Performance Notes

- Difficulty typically 25 bits
- Python miner: 1-2s per block (2-3 cores)
- Rust miner: 0.06-3s per block (comparable)
- Reward: 0.000015258 rpow2 per block (heavily nerfed from original)
- API occasionally returns 503 (server overload) — auto-retry recommended

## Cookie Format

```
rpow_session=eyJlbWFpbCI6IjxlbWFpbD4iLCJleHAiOjx0aW1lc3RhbXA+fQ.<signature>
```

JWT-like structure. Expires after ~30 days.
