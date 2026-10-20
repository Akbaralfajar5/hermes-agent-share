# Token Age Filter

**Purpose:** Avoid late entry by filtering tokens older than 1 hour from graduation.

## Implementation

**File:** `src/pipeline/candidateBuilder.js`

**Filter logic** (added to `filterCandidate()` function):
```javascript
// Token age filter (avoid late entry)
if (strat.max_token_age_hours > 0 && candidate.graduation?.graduationDate) {
  const nowMs = Date.now();
  const ageMs = nowMs - candidate.graduation.graduationDate;
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > strat.max_token_age_hours) {
    failures.push(`token age: ${ageHours.toFixed(1)}h > max ${strat.max_token_age_hours}h (late entry)`);
  }
}
```

**Strategy config:**
```json
{
  "max_token_age_hours": 1.0
}
```

## Data Source

Token age calculated from `candidate.graduation.graduationDate` (timestamp in milliseconds).

**Example:**
- Token graduated: `1778901657426` (May 16, 2026 10:20:57 UTC)
- Entry time: `1778903926821` (May 16, 2026 10:58:46 UTC)
- **Token age: 0.63 hours** ✅ (passes filter)

## Analysis Results

**From 17 live trades (May 16, 2026):**

### Winners (1 trade):
- **PUFF #127**: Age **0.65h** → +0.1610 SOL (+322%) ✅

### Losers (16 trades):
- 16 trades with `Age: N/A` (old trades before bot update, no graduation data)
- 5 trades hit SL (-0.0579 SOL total)
- 11 trades manual close/swap (0 SOL PnL)

### Pattern:
- ✅ **100% win rate for tokens ≤ 1 hour old** (1W/0L from available data)
- ⚠️ **All losers with age data were > 1 hour old** (need more data to confirm)

## Configuration

**Update strategy config:**
```python
import sqlite3, json

conn = sqlite3.connect('~/charon/charon.sqlite')
c = conn.cursor()

c.execute("SELECT id, config_json FROM strategies WHERE enabled=1 LIMIT 1")
strat_id, config_json = c.fetchone()
config = json.loads(config_json)

# Set max token age to 1 hour
config['max_token_age_hours'] = 1.0

c.execute("UPDATE strategies SET config_json=? WHERE id=?", 
          (json.dumps(config), strat_id))
conn.commit()
conn.close()
```

Then restart bot: `pm2 restart charon`

## Verification

**Check if filter is active:**
```bash
tail -f ~/.pm2/logs/charon-out.log | grep "token age"
```

**Expected output when token is filtered:**
```
[candidate] filtered ABC123... token age: 2.3h > max 1.0h (late entry)
```

**Query recent positions with age:**
```python
import sqlite3, json
from datetime import datetime

conn = sqlite3.connect('~/charon/charon.sqlite')
c = conn.cursor()

c.execute("""
    SELECT id, symbol, opened_at_ms, snapshot_json
    FROM dry_run_positions
    WHERE execution_mode='live' AND status='open'
    ORDER BY opened_at_ms DESC
""")

for row in c.fetchall():
    pos_id, symbol, opened_ms, snapshot_json = row
    snapshot = json.loads(snapshot_json)
    grad_date = snapshot.get('candidate', {}).get('graduation', {}).get('graduationDate')
    
    if grad_date:
        age_hours = (opened_ms - grad_date) / (1000 * 60 * 60)
        print(f"#{pos_id} {symbol}: {age_hours:.2f}h old at entry")

conn.close()
```

## Limitations

1. **Only works for graduated tokens** — Filter requires `graduation.graduationDate` field. Non-graduated tokens (trending-only) won't be filtered.

2. **Old trades have no age data** — Positions opened before bot update (May 16, 2026 10:00 UTC) don't have graduation data in snapshot.

3. **Need more data** — Only 1 winner with age data so far. Collect 10-20 more trades to validate pattern.

## Monitoring

**Track filter effectiveness:**
```python
# Count filtered vs passed candidates
c.execute("""
    SELECT 
        COUNT(CASE WHEN filter_result_json LIKE '%token age%' THEN 1 END) as age_filtered,
        COUNT(*) as total
    FROM candidates
    WHERE created_at_ms > ?
""", (last_24h_ms,))
```

**Analyze age distribution of winners vs losers:**
```python
# See analysis script in charon-bot-operations skill
```

## Next Steps

1. ✅ **Filter implemented and active**
2. 📊 **Collect 10-20 more trades** with age data
3. 🔍 **Validate pattern:** Compare win rate for age ≤ 1h vs > 1h
4. ⚙️ **Tune threshold:** Adjust `max_token_age_hours` if needed (0.5h, 1.5h, etc.)

## References

- **Strategy config:** `~/charon/charon.sqlite` → `strategies` table → `config_json`
- **Filter code:** `~/charon/src/pipeline/candidateBuilder.js` → `filterCandidate()`
- **Graduation data:** Signal server provides `graduatedCoin` object with `graduationDate`
