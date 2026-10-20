# Downloading from File-Sharing Sites (Anti-Bot Protected)

Sites like sfile.co/mobi, uptobox, etc. block direct `curl`/`wget` downloads with anti-bot JS. Browser `fetch()` also fails (CORS/redirects).

## Pattern: Python requests.Session with Cookie Collection

```python
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Step 1: Visit the file page to collect cookies
r1 = session.get('https://sfile.co/FILE_ID')

# Step 2: Download with session cookies intact
r2 = session.get(DOWNLOAD_URL, stream=True, allow_redirects=True)

if 'pdf' in r2.headers.get('Content-Type', '').lower() or \
   'application/octet-stream' in r2.headers.get('Content-Type', '').lower():
    with open('/path/to/save.pdf', 'wb') as f:
        for chunk in r2.iter_content(8192):
            f.write(chunk)
```

## Finding the Download URL

1. Navigate browser to the file page
2. Click through the wait/countdown timer ("Please wait 5s...")
3. Once "Download File" link appears, extract via JS console:
   ```js
   document.querySelector('a[href*="download"]')?.href
   ```
4. Use that URL in the Python script above

## Pitfalls

- **Direct curl returns HTML**, not the file — always use Python `requests.Session()` to preserve cookies
- **Cookie dict conflict**: sfile.co sets duplicate cookie names — don't use `dict(session.cookies)`, just track count
- **Browser fetch() fails** with "Failed to fetch" — CORS or redirect blocks it
- **Content-Type check**: some sites return `application/octet-stream` instead of `application/pdf`
- **File size check**: if result is < 100KB and file type is HTML, the download URL may have expired — re-extract from browser

## Tested Sites

- **sfile.co / sfile.mobi**: Works with this pattern (tested June 2025)
