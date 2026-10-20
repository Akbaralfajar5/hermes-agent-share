# Reverse API Engineer Workflow

Tool for capturing browser traffic and generating Python API clients from protected websites.

## Installation

```bash
# Recommended
uv tool install reverse-api-engineer

# Alternative
pip install reverse-api-engineer

# Required: install browser
playwright install chromium
```

## Configuration

Settings stored in `~/.reverse-api/config.json`:
```json
{
  "agent_provider": "auto",
  "claude_code_model": "claude-sonnet-4-6",
  "output_language": "python",
  "real_time_sync": true
}
```

## Modes

### Manual Mode (Best for Protected Sites)
1. `reverse-api-engineer` → enter task description
2. Browser opens with stealth mode
3. Navigate and interact manually (login, browse, trigger API calls)
4. Close browser when done
5. AI analyzes HAR → generates Python client

### Agent Mode (Autonomous)
- Uses Playwright MCP for browser automation
- AI agent navigates and interacts automatically
- Best for sites without heavy bot detection
- Switch mode with Shift+Tab in CLI

### Engineer Mode
Re-process existing HAR captures:
```bash
reverse-api-engineer engineer <run_id>
```

## Output Structure

```
./scripts/{task_name}/
├── api_client.py      # Main API client
├── models.py          # Pydantic models (if applicable)
├── README.md          # Usage documentation
└── requirements.txt   # Dependencies
```

## Use Cases for Protected APIs

- Akamai blocks direct API calls (signature detection)
- Manual mode: login via app-like flow, browse episodes
- Captures: RSA signatures, version headers, package-name headers
- Generated client includes all auth headers

### Cloudflare-Protected Sites
- JS challenge resolved by real browser
- Captures cf_clearance cookie and required headers
- Generated client can replay authenticated requests

## Pitfalls

1. **Time-based signatures expire** — generated code may need refresh logic
2. **Session cookies rotate** — may need periodic re-capture
3. **Rate limiting** — captured patterns may hit limits at scale
4. **Mobile-only APIs** — use mobile user-agent in browser settings

## Integration with Camoufox/CloakBrowser

For extra stealth, launch reverse-api-engineer with custom browser:
```python
# Not directly supported, but HAR can be captured separately
# Then use engineer mode to process the HAR
```


Target: `https://sapi.streaming-servicedb.com/drama-box/ap001/`

Blocked by Akamai when called directly (even with residential proxy).

Workflow:
3. Close browser
4. AI extracts:
   - RSA signature generation pattern
   - Required headers: `User-Agent: okhttp/4.9.3`, `version: 470`, `vn: 4.7.0`
   - Cookie handling
5. Generated client bypasses Akamai because it replicates exact browser behavior

## Links

- Repo: https://github.com/kalil0321/reverse-api-engineer
- Examples: `/tmp/reverse-api-engineer/examples/` (Apple, Uber, Ashby, AutoScout24)
