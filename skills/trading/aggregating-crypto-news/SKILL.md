---
name: aggregating-crypto-news
description: 'Aggregate breaking cryptocurrency news from 50+ sources including CoinDesk,
  CoinTelegraph, The Block, and Decrypt.

  Use when needing to monitor crypto market news, track announcements, or find coin-specific
  updates.

  Trigger with phrases like "get crypto news", "latest Bitcoin headlines", "DeFi announcements",
  "scan for breaking news", or "check crypto updates".

  '
allowed-tools: Read, Bash(crypto:news-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
- crypto
- monitoring
- aggregating-crypto
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Aggregating Crypto News

## Overview

Aggregate cryptocurrency news from 50+ authoritative sources via RSS feeds with real-time scanning, coin/category filtering, and relevance scoring.

## Prerequisites

1. **Python 3.8+** installed
2. **Dependencies**: `pip install feedparser requests`
3. Internet connectivity for RSS feed access

## Instructions

1. **Assess user intent** - determine filters needed:
   - General news: no filters, use defaults
   - Coin-specific: extract symbol (BTC, ETH, etc.)
   - Category-specific: extract category (defi, nft, regulatory, etc.)
   - Time-specific: extract window (1h, 4h, 24h, 7d)

2. **Run the aggregator** with appropriate filters:
   ```bash
   # Default scan (top 20, past 24h, relevance sorted)
   python ~/.hermes/skills/trading/aggregating-crypto-news/scripts/news_aggregator.py

   # Coin-specific scan
   python ~/.hermes/skills/trading/aggregating-crypto-news/scripts/news_aggregator.py --coin BTC --period 4h

   # Category filter
   python ~/.hermes/skills/trading/aggregating-crypto-news/scripts/news_aggregator.py --category defi --top 30

   # Multiple filters
   python ~/.hermes/skills/trading/aggregating-crypto-news/scripts/news_aggregator.py --coin ETH --category defi --period 24h --top 15
   ```

3. **Export results** for downstream processing:
   ```bash
   python ~/.hermes/skills/trading/aggregating-crypto-news/scripts/news_aggregator.py --format json --output news.json
   ```

4. **Present results** to the user:
   - Show source, title, age, and relevance score
   - Highlight market-moving keywords if present
   - Provide links for full articles
   - Summarize meta information (sources checked, articles found)

## Output

Table showing articles ranked by relevance score (0-100) based on market-moving keyword detection, source authority, and recency:

```
==============================================================================
  CRYPTO NEWS AGGREGATOR                            Updated: 2026-01-14 15:30  # 2026 - current year timestamp
==============================================================================

  TOP CRYPTO NEWS (24h)
------------------------------------------------------------------------------
  Rank  Source          Title                           Age     Score
------------------------------------------------------------------------------
    1   CoinDesk        Bitcoin Breaks $100K ATH        2h      95.0
    2   The Block       SEC Approves ETH ETF            4h      92.5
    3   Decrypt         Solana DeFi TVL Surges          6h      78.3
------------------------------------------------------------------------------

  Summary: 20 articles shown | Scanned: 50 sources | Matched: 187
==============================================================================
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Network timeout | RSS feed unreachable | Uses cached data; skips unavailable sources |
| Parse error | Malformed RSS | Skips entry; continues with valid articles |
| No results | Filters too strict | Suggest relaxing filters |
| Invalid coin | Unknown symbol | List similar valid symbols |

See `references/errors.md` for comprehensive error handling.

## Examples

Filtering patterns for common news monitoring scenarios:

```bash
# Latest crypto news (defaults)
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py

# Bitcoin news from past 4 hours
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin BTC --period 4h

# DeFi category news
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category defi

# High-relevance news only
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --min-score 70 --top 10

# Multiple coins
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coins BTC,ETH,SOL
```

## Google News RSS (MOST POWERFUL — Use for Specific Topic Search)

The bundled RSS feeds only show the latest 24-48h of articles in each feed. For **searching specific topics** (e.g., "pump.fun token burn"), Google News RSS is far superior — returns 90+ results with full date range:

```python
import feedparser, re

# Search any crypto topic — no API key needed!
query = "pump.fun+token+burn"  # URL-encode spaces as +
url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
feed = feedparser.parse(url)

for entry in feed.entries[:15]:
    source = entry.get('source', {}).get('title', 'Unknown')
    title = entry.get('title', '')
    published = entry.get('published', '')
    link = entry.get('link', '')
    print(f"[{source}] {published}")
    print(f"  {title}")
    print(f"  {link}\n")
```

**Google News RSS patterns:**
- Topic search: `https://news.google.com/rss/search?q=QUERY&hl=en&gl=US&ceid=US:en`
- Top stories: `https://news.google.com/rss?hl=en&gl=US&ceid=US:en`
- By topic: `https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en` (business)

**Advantages over direct RSS feeds:**
- Searches across ALL publishers (not just the 20 in sources.yaml)
- Returns historical results (not just last 24h)
- No rate limiting for reasonable usage (≥60s between requests)
- No API key needed
- Links redirect through Google but source name is in the `<source>` tag

**Combine both approaches:**
1. Google News RSS for **specific topic research** (e.g., "what happened with pump.fun?")
2. Direct RSS feeds for **general market monitoring** (latest headlines across all sources)

## Hermes-Specific Notes

- The `${CLAUDE_SKILL_DIR}` variable does NOT exist in Hermes Agent. Use the actual path: `~/.hermes/skills/trading/aggregating-crypto-news/scripts/`
- Requires `pip install feedparser` (not pre-installed)
- Direct RSS feeds (CoinDesk, Decrypt, etc.) work without authentication
- Some sites (CoinGecko, TheBlock, Google Search) block direct browser access with Cloudflare CAPTCHA — use RSS feeds instead

## Resources

- `references/implementation.md` - CLI options, categories, JSON format, advanced filtering
- `references/errors.md` - Comprehensive error handling
- `references/examples.md` - Detailed usage examples
- `config/sources.yaml` - Full source registry (20+ crypto news RSS feeds)
- `scripts/news_aggregator.py` - Main aggregator script
- CoinDesk RSS: https://www.coindesk.com/arc/outboundfeeds/rss/
- feedparser docs: https://feedparser.readthedocs.io/
- Google News RSS (no auth): https://news.google.com/rss/search?q=QUERY
