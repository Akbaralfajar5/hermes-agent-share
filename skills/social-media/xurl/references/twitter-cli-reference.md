# twitter CLI — Cookie-Based X/Twitter CLI Reference

The `twitter` CLI is a Python-based tool that uses cookies (AUTH_TOKEN + CT0) instead of OAuth API. It's the primary tool on this VPS since xurl has no auth configured.

## Setup

Credentials stored at `~/.hermes/x_credentials.env`:
```bash
export TWITTER_AUTH_TOKEN="<auth_token>"
export TWITTER_CT0="<ct0_csrf_token>"
```

Verify:
```bash
source ~/.hermes/x_credentials.env && export TWITTER_AUTH_TOKEN TWITTER_CT0 && twitter whoami
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `post` | Post a tweet | `twitter post "text"` |
| `reply` | Reply to a tweet | `twitter reply <id> "text"` |
| `quote` | Quote tweet | `twitter quote <id> "text"` |
| `delete` | Delete a tweet | `twitter delete <id>` |
| `search` | Search tweets | `twitter search "query" --max 10 --json` |
| `like` | Like a tweet | `twitter like <id>` |
| `retweet` | Retweet | `twitter retweet <id>` |
| `bookmark` | Bookmark a tweet | `twitter bookmark <id>` |
| `follow` | Follow a user | `twitter follow @handle` |
| `followers` | List followers | `twitter followers @handle` |
| `following` | List following | `twitter following @handle` |
| `whoami` | Current user info | `twitter whoami` |
| `show` | View tweet from last results | `twitter show 1` |
| `feed` | Home timeline | `twitter feed` |
| `favorites` | Liked tweets | `twitter favorites` |
| `bookmarks` | Bookmarked tweets | `twitter bookmarks` |
| `dms` | Direct messages | `twitter dms` |

## Flags

- `--json` / `-j`: Output as JSON
- `--max N`: Limit results
- `--compact` / `-c`: (global, before subcommand) Minimal fields, LLM-friendly

## Cronjob Integration

When writing cronjob prompts that use twitter CLI:
1. Always include `source ~/.hermes/x_credentials.env && export TWITTER_AUTH_TOKEN TWITTER_CT0` as first step
2. Use `twitter search "query" --max N --json` for structured output
3. Use `twitter like <id>` for engagement actions
4. Use `twitter post "text"` for content creation

## Pitfalls

- `--compact` / `-c` is a global flag, must come BEFORE the subcommand (not after)
- `trending` command does NOT exist — use `twitter search "trending topic" --max N` instead
- JSON output structure: `{"ok": true, "data": [...]}`
- Cookie expiry: verify with `twitter whoami` — if it fails, cookies need refresh
