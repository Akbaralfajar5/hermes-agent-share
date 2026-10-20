---
name: data-transformation
description: "Structured data transformation and insight extraction — pandas pipelines, large dataset patterns, crypto-specific analysis (holder snapshots, tx patterns, wallet bundling), output to xlsx/csv."
version: 1.0.0
author: Hermes (adapted from SUPERAGENT v3 m5)
license: MIT
metadata:
  hermes:
    tags: [data, pandas, csv, excel, dataset, snapshot, analytics, crypto, airdrop, laporan]
---

# Data Transformation & Insight Extraction

Load when: spreadsheet, excel, csv, dataset, snapshot, laporan, data, analytics, report, holder, airdrop snapshot, phone, nomor, kontak, hp, telepon, daftar nomor.

Data-to-decision specialist. Raw → cleaned → insight → prescription. Always 3 actionable outputs minimum.

---

## Processing Flow

```
1. SCOPE       → exact question being answered
2. ACQUIRE     → identify available vs required inputs
3. NORMALIZE   → dedupe, type-cast, handle nulls, fix encoding
4. PROCESS     → patterns, trends, anomalies, correlations
5. RENDER      → table / chart / file artifact
6. PRESCRIBE   → exactly 3 specific next actions
```

---

## Transformation Template (Python pandas)

```python
import pandas as pd
import numpy as np

# Load + inspect
df = pd.read_csv('input.csv', dtype_backend='numpy_nullable')
print(df.info())
print(df.describe(include='all'))
print('Nulls:', df.isnull().sum().to_dict())
print('Dups:', df.duplicated().sum())

# Clean
df = df.drop_duplicates()
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
df = df.dropna(subset=['date'])

# Transform
summary = (df.groupby('segment')
             .agg(total=('amount', 'sum'),
                  avg=('amount', 'mean'),
                  n=('amount', 'count'),
                  median=('amount', 'median'))
             .sort_values('total', ascending=False))

# Output
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as w:
    summary.to_excel(w, sheet_name='Summary')
    df.to_excel(w, sheet_name='Source', index=False)

print('✅ output.xlsx ready')
```

---

## Large Dataset Patterns (100K+ rows)

### Chunked reading (avoid memory blowup)

```python
chunks = []
for chunk in pd.read_csv('huge.csv', chunksize=50_000):
    chunks.append(chunk[chunk['active'] == True])  # filter early
df = pd.concat(chunks, ignore_index=True)
```

### O(1) lookup (eligibility checks, airdrop snapshot)

```python
import json

with open('eligible.json') as f:
    eligible = set(json.load(f))   # ~200K addresses → ~12MB RAM

def is_eligible(addr: str) -> bool:
    return addr.lower() in eligible
```

### SQLite for medium datasets (1M–10M rows)

```python
import sqlite3, pandas as pd
con = sqlite3.connect('data.db')
df.to_sql('records', con, if_exists='replace', index=False)
con.execute('CREATE INDEX idx_addr ON records(address)')

# Fast lookup
row = con.execute('SELECT * FROM records WHERE address = ?', (addr,)).fetchone()
```

### Streaming JSON (when full load won't fit)

```python
import ijson  # pip install ijson

with open('massive.json', 'rb') as f:
    for record in ijson.items(f, 'records.item'):
        process(record)
```

---

## Performance Indicators (always compute these)

```
throughput:   total + period-over-period delta (%)
activity:     active + new + lapsed units
efficiency:   input → qualified → converted (%)
acquisition:  cost per new unit
retention:    lifetime yield per unit
return:       output / input ratio (%)
distribution: p50, p90, p99 (not just mean — mean lies on skewed data)
```

---

## Crypto-Specific Patterns

### Token holder snapshot

```python
import pandas as pd
holders = pd.read_json('holders.json')
holders['balance_eth'] = holders['balance_wei'].astype(float) / 10**18
print(f'Holders: {len(holders):,}')
print(f'Top 10 hold {holders.nlargest(10, "balance_eth")["balance_eth"].sum() / holders["balance_eth"].sum():.1%}')
print('Distribution:', holders['balance_eth'].quantile([.5, .9, .99]).to_dict())
```

### Transaction pattern detection (spam/bot wallets)

```python
txs = pd.read_csv('txs.csv')
spam_signals = (txs.groupby('from_address')
                   .agg(n_txs=('hash', 'count'),
                        unique_to=('to_address', 'nunique'),
                        time_span_hr=('timestamp', lambda x: (x.max()-x.min())/3600))
                   .query('n_txs > 100 and unique_to / n_txs < 0.1'))
print(f'Spam wallets: {len(spam_signals)}')
```

### Wallet bundling (multi-wallet farming detection)

```python
from collections import defaultdict

clusters = defaultdict(set)
for _, row in funding_txs.iterrows():
    clusters[row['funded_by']].add(row['recipient'])

# Flag clusters > 10 wallets
bundles = {k: v for k, v in clusters.items() if len(v) > 10}
print(f'Bundles found: {len(bundles)}')
```

---

## Phone Number Cleaning (Indonesian)

→ read `references/phone-number-cleaning.md`
- Strip numbering prefixes, timestamps, emoji markers (❌/🔴/🔁)
- Keep only valid Indonesian mobile prefixes (08x, 8x, 9x)
- Output: one per line, grouped per 20 with blank line separator
- No spaces, no non-phone junk

---

## Output Constraints

- Always generate ACTUAL output file — never inline-only summary
- Always include delta / trend — current state alone is insufficient
- Numeric outputs: always include units + thousands separator (`123,456` not `123456`)
- Date outputs: ISO format (`2026-05-25`) not localized
- Always close with exactly 3 specific, executable prescriptions
