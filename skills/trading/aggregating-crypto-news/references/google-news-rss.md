# Google News RSS API Reference (from google-news skill)

## Base URL
```
https://news.google.com/rss
```

## Query Parameters
| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `hl` | Yes | Interface language | `en-US`, `id` |
| `gl` | Yes | Country (ISO 3166-1) | `US`, `ID` |
| `ceid` | Yes | Compound locale `{gl}:{lang}` | `US:en`, `ID:id` |

## Feed Types

### Top Stories
```
https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en
```

### Topic Feeds
```
https://news.google.com/rss/topics/{TOPIC_ID}?hl={hl}&gl={gl}&ceid={gl}:{lang}
```
Topic IDs (English, US): World, Business, Technology, Entertainment, Sports, Science, Health

### Keyword Search
```
https://news.google.com/rss/search?q={query}&hl={hl}&gl={gl}&ceid={gl}:{lang}
```

## Search Modifiers
| Modifier | Example |
|----------|---------|
| `+` or space | `q=artificial+intelligence` |
| `OR` | `q=Tesla+OR+SpaceX` |
| `-` (exclude) | `q=Apple+-fruit` |
| `"..."` (exact) | `q=%22climate+change%22` |
| `when:7d` | `q=Bitcoin+when:7d` |
| `when:1h` | `q=breaking+news+when:1h` |
| `after:YYYY-MM-DD` | `q=Olympics+after:2024-07-01` |
| `site:` | `q=AI+site:reuters.com` |

## Rate Limits
- Polling interval: ≥ 60 seconds between requests
- Concurrent: < 10 connections
- Use descriptive User-Agent

## Python Usage
```python
import feedparser
feed = feedparser.parse("https://news.google.com/rss/search?q=crypto+market&hl=en&gl=US&ceid=US:en")
for entry in feed.entries[:10]:
    source = entry.get('source', {}).get('title', 'Unknown')
    print(f"[{source}] {entry.title}")
```

## Resolving Redirect URLs
```python
import requests
response = requests.head("https://news.google.com/rss/articles/CBMi...", allow_redirects=True, timeout=10)
print(response.url)  # final publisher URL
```
