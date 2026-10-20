---
name: internet-reach
description: >
  Unified internet research & platform access — read, search, and extract
  from 13+ platforms via one skill. Combines Agent-Reach (Bilibili, Reddit,
  XiaoHongShu, V2EX, Xueqiu, Xiaoyuzhou, LinkedIn, Exa search) with
  existing tools (Twitter/X via xurl, YouTube via yt-dlp/transcript-api,
  GitHub via gh, RSS via feedparser, web via Jina Reader).
  
  Use when: user shares any URL, mentions any platform, asks to research
  anything online, or wants to find/search/read from the internet.
metadata:
  hermes:
    tags: [internet, research, social-media, search, multi-platform]
---

# Internet Reach — Unified Platform Access

Single skill for ALL internet research. 13 platforms, zero API fees.

## Platform Routing Table

| Platform | Tool | Status |
|---|---|---|
| 🌐 Web pages | Jina Reader (`curl r.jina.ai/URL`) | ✅ Zero-config |
| 📺 YouTube | yt-dlp + youtube-transcript-api | ✅ Zero-config |
| 📦 GitHub | gh CLI | ✅ Zero-config |
| 📡 RSS/Atom | feedparser (Python) | ✅ Zero-config |
| 📺 Bilibili (B站) | bili-cli or B站 search API | ✅ Zero-config (basic) |
| 💻 V2EX | V2EX API | ✅ Zero-config |
| 🔍 Semantic Search | Exa (via mcporter) | ✅ Zero-config |
| 🐦 Twitter/X | twitter-cli (cookie) or xurl (OAuth2) | ⚙️ Needs cookie/token |
| 📖 Reddit | rdt-cli + cookie | ⚙️ Needs cookie |
| 📕 小红书 | xiaohongshu-mcp or OpenCLI | ⚙️ Needs login |
| 💼 LinkedIn | linkedin-mcp or Jina Reader | ⚙️ Needs login |
| 📈 雪球 (Xueqiu) | xueqiu-mcp | ⚙️ Needs config |
| 🎙️ 小宇宙播客 | Whisper transcription | ⚙️ Needs Groq key |

## Health Check

```bash
agent-reach doctor --json
```

Run this FIRST to see which backends are active for each platform.

---

## Quick Commands by Platform

### 🌐 Web Pages (Jina Reader)
```bash
# Read any URL → clean markdown
curl -s "https://r.jina.ai/URL_HERE"

# With metadata
curl -sH "X-Return-Format: markdown" "https://r.jina.ai/URL_HERE"
```

### 📺 YouTube
```bash
# Get video info
yt-dlp --dump-json "URL"

# Download subtitles only
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"

# Search videos
yt-dlp --dump-json "ytsearch5:query"

# Transcript via Python (lightweight)
python3 -c "
from youtube_transcript_api import YouTubeTranscriptApi
for seg in YouTubeTranscriptApi.get_transcript('VIDEO_ID', languages=['en','id'])[:20]:
    print(f'{seg[\"start\"]:.0f}s: {seg[\"text\"]}')"
```

### 🐦 Twitter/X

**Option A: twitter-cli (cookie-based, no dev account needed)**
```bash
# Install
pip install twitter-cli

# Auth: export cookies from Cookie-Editor Chrome extension
# Set env vars: TWITTER_AUTH_TOKEN + TWITTER_CT0

# Feed
twitter feed -n 20

# Read tweet
twitter tweet URL_OR_ID

# User timeline
twitter user-posts @username -n 20

# Search (may be unstable, Twitter changes GraphQL endpoints)
twitter search "query" -n 10
```

**Option B: xurl CLI (official API, needs X Developer Portal OAuth2)**
```bash
# Search
xurl search recent "query" --max-results 10

# Read single tweet
xurl tweet TWEET_ID

# Post (write operation)
xurl post "tweet text"
```

**twitter-cli search unstable → retry chain:**
1. Direct retry
2. `pipx upgrade twitter-cli` then retry
3. Fallback to `twitter feed` or `twitter user-posts @somebody`

### 📺 Bilibili (B站)
```bash
# Search
curl -s "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=QUERY" | python3 -m json.tool

# Video info via bili-cli
bili-cli info BVID

# Subtitles via bili-cli
bili-cli subtitle BVID
```

### 📖 Reddit
```bash
# Read subreddit
rdt-cli subreddit SUBREDDIT_NAME --limit 10

# Read post + comments
rdt-cli post POST_URL

# Search
rdt-cli search "query" --subreddit SUBREDDIT
```

### 📕 小红书 (XiaoHongShu)
```bash
# Search (MCP)
mcporter call 'xiaohongshu.search_notes(query: "query")'

# Read note
mcporter call 'xiaohongshu.get_note(url: "NOTE_URL")'

# Comments
mcporter call 'xiaohongshu.get_comments(note_id: "ID")'
```

### 💻 V2EX
```bash
# Hot topics
curl -s "https://www.v2ex.com/api/topics/hot.json"

# Topic detail
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID"

# Node topics
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=NODE"
```

### 📈 雪球 (Xueqiu)
```bash
# Stock quote
mcporter call 'xueqiu.get_stock_quote(symbol: "SH600519")'

# Search stocks
mcporter call 'xueqiu.search(query: "茅台")'

# Hot posts
mcporter call 'xueqiu.get_hot_posts()'
```

### 📡 RSS/Atom Feeds
```bash
# Read feed
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:10]:
    print(f'{e.title} — {e.link}')"
```

### 🎙️ Podcasts (小宇宙)
```bash
# Transcribe podcast audio
agent-reach transcribe "PODCAST_URL"
```

### 💼 LinkedIn
```bash
# Profile
mcporter call 'linkedin-scraper.get_person_profile(linkedin_url: "URL")'

# Search jobs
mcporter call 'linkedin-scraper.search_jobs(keyword: "engineer", limit: 10)'

# Fallback: Jina Reader
curl -s "https://r.jina.ai/https://linkedin.com/in/username"
```

### 🔍 Semantic Search (Exa)
```bash
# Web search
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'

# Code search
mcporter call 'exa.get_code_context_exa(query: "code question", tokensNum: 3000)'
```

### 📦 GitHub (gh CLI)
```bash
# Search repos
gh search repos "query" --sort stars --limit 10

# View repo
gh repo view owner/repo

# Search code
gh search code "query" --language python

# Issues/PRs
gh issue list -R owner/repo
gh pr list -R owner/repo
```

---

## Research Workflow (Multi-Platform)

For broad research tasks, combine platforms:

1. **Web search** → Exa for general results
2. **Social discussion** → Twitter + Reddit for opinions
3. **Chinese content** → 小红书 + Bilibili for CN perspective
4. **Technical** → GitHub + V2EX for dev discussion
5. **Video** → YouTube + Bilibili for tutorials
6. **Finance** → 雪球 for stock/finance discussion

Collect in parallel, then synthesize.

---

## File Sharing Site Downloads

For downloading files from anti-bot protected sites (sfile.co, uptobox, etc.), see `references/file-sharing-downloads.md`. Key pattern: Python `requests.Session()` with cookie collection — direct curl/browser fetch() both fail.

---

## Pitfalls

- **GitHub `gh auth login`**: PAT must have `read:org` scope or login fails silently. Generate new token at github.com/settings/tokens with `repo` + `workflow` + `read:org`.
- **Twitter auth choice**: If user has no X Developer Portal access, use `twitter-cli` with Cookie-Editor export (TWITTER_AUTH_TOKEN + TWITTER_CT0), NOT xurl (needs OAuth2 app credentials).
- **Agent-Reach is NOT a wrapper** — after install, use upstream tools directly (xurl, yt-dlp, gh, mcporter, etc.)
- **Cookie-based platforms** (Twitter, Reddit, 小红书): export via Cookie-Editor Chrome extension, not QR scan
- **yt-dlp subtitles**: auto-generated subs may have duplicates, needs post-processing
- **Reddit**: no zero-config path (anonymous API blocked), needs cookie
- **Bilibili basic**: search API works without auth, but subtitles need bili-cli
- **mcporter**: MCP tools need mcporter running — check with `mcporter status`
- **Run `agent-reach doctor --json`** before multi-platform tasks to verify backends
- **Update check**: `agent-reach check-update` after big tasks

## Agent-Reach Install/Update

```bash
# Install
source ~/.agent-reach-venv/bin/activate
agent-reach install --env=auto

# Update
source ~/.agent-reach-venv/bin/activate
pip install --upgrade https://github.com/Panniantong/agent-reach/archive/main.zip
```

Venv path: `~/.agent-reach-venv/`
Config: `~/.agent-reach/`
