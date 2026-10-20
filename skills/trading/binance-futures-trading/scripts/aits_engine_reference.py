#!/usr/bin/env python3
"""
AITS Engine - Advanced Institutional Trading System
Location on server: /home/ubuntu/aits_engine.py

Key functions:
- analyze_aits(symbol) → Full multi-TF analysis (4H/1H/15M/5M) using SMC + S/D + Fib + Volume + Liquidity
- score_setup(tf_results, direction) → Score 0-100 based on confluence
- generate_entry(symbol, tf_results, direction) → Entry/SL/TP calculation
- scan_and_execute(btc_bias, risk_rating, wallet, max_pos, current_pos) → Full scan + filter + execute

Usage in cronjob:
```python
import sys
sys.path.insert(0, '/home/ubuntu')
from aits_engine import *

# Analyze BTC first
btc_results = analyze_aits("BTCUSDT")
btc_bias = btc_results['4h']['trend']  # 'bullish', 'bearish', 'ranging'

# Scan and execute
setups = scan_and_execute(btc_bias, 'safe', wallet_balance, 5, current_positions)
```

Components analyzed per timeframe:
1. Swing Points (fractal-based, lookback varies by TF)
2. Market Structure (BOS/CHoCH detection)
3. Order Blocks (demand/supply zones with strength scoring)
4. Fibonacci OTE (0.618-0.786 retracement zone)
5. VWAP (institutional benchmark)
6. Volume Divergence (healthy trend vs divergence)
7. Liquidity Sweeps (stop hunt detection)

Scoring weights:
- 4H Bias: 25pts (from BOS/CHoCH)
- 1H Confirm: 20pts (structure alignment)
- 15M OB Quality: 20pts (zone strength)
- VWAP: 10pts (alignment)
- Volume: 10pts (confirmation)
- 5M Trigger: 10pts (entry timing)
- Liquidity Sweep: 5pts (bonus)

Minimum entry score: 60/100
Minimum R:R: 1:2
"""
# See /home/ubuntu/aits_engine.py for full implementation
