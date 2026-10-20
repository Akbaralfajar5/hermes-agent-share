# LLM Decisions Not Executing

**Symptom:** LLM returns BUY decisions with reasonable confidence, but bot does not create positions.

## Diagnosis Flow

### 1. Verify LLM Decisions Exist

```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('~/charon/charon.sqlite')
cursor = conn.cursor()

# Get recent decisions
five_min_ago = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
cursor.execute("""
    SELECT id, verdict, confidence, reason
    FROM llm_decisions
    WHERE created_at_ms > ? AND verdict = 'BUY'
    ORDER BY id DESC
    LIMIT 10
""", (five_min_ago,))

for row in cursor.fetchall():
    print(f"#{row[0]}: {row[1]} ({row[2]}%) - {row[3][:60]}...")
```

### 2. Check Positions Created

```python
cursor.execute("""
    SELECT COUNT(*) FROM dry_run_positions
    WHERE opened_at_ms > ?
""", (five_min_ago,))
print(f"Positions created: {cursor.fetchone()[0]}")
```

**If decisions exist but positions = 0**, proceed to step 3.

### 3. Check Confidence Threshold

```python
import json
cursor.execute("SELECT config_json FROM strategies WHERE enabled=1")
config = json.loads(cursor.fetchone()[0])
threshold = config.get('llm_min_confidence', 75)
print(f"Confidence threshold: {threshold}%")
```

**Common issue:** Default threshold is 75%, but LLM may return 60-72% confidence.

**Fix:**
```python
config['llm_min_confidence'] = 60  # Lower to 60%
cursor.execute("UPDATE strategies SET config_json=? WHERE enabled=1", 
               (json.dumps(config),))
conn.commit()
```

### 4. Check Agent Enabled

```python
cursor.execute("SELECT value FROM settings WHERE key='agent_enabled'")
row = cursor.fetchone()
print(f"Agent enabled: {row[0] if row else 'default (true)'}")
```

**If disabled:**
```python
cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('agent_enabled', 'true')")
conn.commit()
```

### 5. Check Max Positions

```python
cursor.execute("SELECT COUNT(*) FROM dry_run_positions WHERE status='open'")
open_count = cursor.fetchone()[0]
max_positions = config.get('max_open_positions', 3)
print(f"Open: {open_count}, Max: {max_positions}")
```

**If open >= max:**
- Close positions manually (see `bulk-position-close.md`)
- Or increase `max_open_positions` in strategy config

### 6. Check Decision Logs

```python
cursor.execute("""
    SELECT action, guardrails
    FROM decision_logs
    WHERE created_at_ms > ?
    ORDER BY id DESC
    LIMIT 5
""", (five_min_ago,))

for action, guardrails_json in cursor.fetchall():
    guardrails = json.loads(guardrails_json) if guardrails_json else {}
    print(f"Action: {action}")
    print(f"  Guardrails: {guardrails}")
```

**Common actions:**
- `entry_skipped_max_positions` → max positions reached
- `entry_not_approved` → confidence too low or agent disabled
- `no_candidate_selected` → LLM returned WATCH/PASS

## Code Flow (orchestrator.js)

```javascript
// Line 100-117 (approximate)
const confidenceThreshold = Number(strat.llm_min_confidence) || 75;

if (selectedRow && 
    boolSetting('agent_enabled', true) && 
    batchDecision.verdict === 'BUY' && 
    batchDecision.confidence >= confidenceThreshold) {
  
  if (!canOpenMorePositions()) {
    console.log(`[agent] max open positions reached...`);
    return;
  }
  
  await handleApprovedBuy(selectedRow, batchDecision, ...);
}
```

**Execution requires ALL of:**
1. ✅ `selectedRow` exists (LLM picked a candidate)
2. ✅ `agent_enabled = true`
3. ✅ `verdict = 'BUY'`
4. ✅ `confidence >= threshold`
5. ✅ `open_count < max_open_positions`

## Quick Fix Checklist

```bash
# 1. Lower confidence threshold
python3 << 'EOF'
import sqlite3, json
conn = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT config_json FROM strategies WHERE enabled=1")
config = json.loads(cursor.fetchone()[0])
config['llm_min_confidence'] = 60
cursor.execute("UPDATE strategies SET config_json=? WHERE enabled=1", (json.dumps(config),))
conn.commit()
print("✅ Threshold lowered to 60%")
EOF

# 2. Restart bot
cd ~/charon && pm2 restart charon

# 3. Monitor for execution
sleep 30
tail -50 ~/.pm2/logs/charon-out.log | grep -E "llm|BUY|entry|position.*created"
```

## Related Files

- `src/pipeline/orchestrator.js` — decision execution logic
- `src/db/positions.js` — `canOpenMorePositions()` function
- `references/bulk-position-close.md` — manual position management
