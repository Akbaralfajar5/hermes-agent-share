# GitHub as Database for Static Site CMS

## Why GitHub over JSONBlob

| Factor | JSONBlob | GitHub |
|--------|----------|--------|
| Retention | Anonymous: 1 day, Free: 3 days | Permanent |
| Auth | None (anyone can read/write) | Token-based |
| Version history | None | Full git history |
| User control | None | User owns the repo |
| CORS | Broken for PUT/POST | N/A (use API proxy) |
| Cost | Free tier limited | Free unlimited (public repos) |

**Verdict:** JSONBlob is only suitable for throwaway demos. For anything the user cares about, use GitHub.

## Architecture

```
Admin Panel → PUT /api/data/[key] → Vercel API Route → GitHub Contents API → repo JSON file
Visitor      → GET /api/data/[key] → Vercel API Route → GitHub Contents API → repo JSON file
```

All requests go through a Next.js API route (server-side) to:
1. Avoid CORS issues
2. Keep the GitHub token secret (env var, never exposed to browser)

## Setup Steps

### 1. Get GitHub Personal Access Token
User goes to: `https://github.com/settings/tokens`
- Generate new token (classic)
- Scope: `repo` only
- Expiration: No expiration (for convenience)
- Token format: `ghp_...`

### 2. Create Data Repo
```bash
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"myapp-data","description":"Website data storage","private":false,"auto_init":true}'
```

### 3. Create JSON Data Files
For each data domain, create a file via GitHub Contents API:
```bash
# Base64 encode the JSON content
CONTENT=$(echo '{"key":"value"}' | base64)

curl -s -X PUT https://api.github.com/repos/OWNER/REPO/contents/products.json \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"init: products\",\"content\":\"$CONTENT\"}"
```

Typical files: `products.json`, `contacts.json`, `settings.json`, `password.json`

### 4. API Proxy Route

```typescript
// src/app/api/data/[key]/route.ts
import { NextRequest, NextResponse } from "next/server";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const REPO_OWNER = "username";
const REPO_NAME = "data-repo";

const FILE_MAP: Record<string, string> = {
  products: "products.json",
  contacts: "contacts.json",
  siteSettings: "settings.json",
  password: "password.json",
};

function githubUrl(file: string): string {
  return `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${file}`;
}

// GET: fetch file content
export async function GET(
  _req: NextRequest,
  { params }: { params: { key: string } }
) {
  const file = FILE_MAP[params.key];
  if (!file) return NextResponse.json({ error: "Invalid key" }, { status: 400 });

  const res = await fetch(githubUrl(file), {
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
    },
    cache: "no-store",
  });

  const ghData = await res.json();
  const content = Buffer.from(ghData.content, "base64").toString("utf-8");
  return NextResponse.json(JSON.parse(content), {
    headers: {
      "Cache-Control": "public, s-maxage=10, stale-while-revalidate=30",
      "X-GitHub-SHA": ghData.sha,
    },
  });
}

// PUT: update file (requires current SHA)
export async function PUT(
  req: NextRequest,
  { params }: { params: { key: string } }
) {
  const file = FILE_MAP[params.key];
  if (!file) return NextResponse.json({ error: "Invalid key" }, { status: 400 });

  const body = await req.json();

  // Get current SHA (required by GitHub API for updates)
  const getRes = await fetch(githubUrl(file), {
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
    },
    cache: "no-store",
  });
  const current = await getRes.json();

  // Update with new content
  const content = Buffer.from(JSON.stringify(body, null, 2)).toString("base64");
  const putRes = await fetch(githubUrl(file), {
    method: "PUT",
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: `update: ${file} via admin panel`,
      content,
      sha: current.sha, // CRITICAL: must include current SHA
    }),
  });

  return putRes.ok
    ? NextResponse.json({ success: true })
    : NextResponse.json({ error: "Failed" }, { status: putRes.status });
}
```

### 5. Add Token to Vercel Environment
```bash
echo "$TOKEN" | npx vercel env add GITHUB_TOKEN production --token=$VERCEL_TOKEN
```

### 6. Client-Side Helper (jsonblob.ts or github.ts)
```typescript
export async function fetchBlob<T>(key: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`/api/data/${key}`, { cache: "no-store" });
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    // Fallback to localStorage
    const stored = localStorage.getItem(`myapp_${key}`);
    return stored ? JSON.parse(stored) : fallback;
  }
}

export async function updateBlob<T>(key: string, data: T): Promise<boolean> {
  try {
    const res = await fetch(`/api/data/${key}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (res.ok) localStorage.setItem(`myapp_${key}`, JSON.stringify(data));
    return res.ok;
  } catch { return false; }
}
```

## Key Pitfalls

1. **SHA is required for updates** — GitHub Contents API requires the current file SHA in every PUT. Always GET first to obtain it.
2. **Token must be server-side only** — use `process.env.GITHUB_TOKEN` in API routes, never expose to browser.
3. **Base64 encoding** — GitHub stores file content as base64. Decode on read, encode on write.
4. **Rate limits** — GitHub API: 5000 req/hour with token. Fine for admin panels, not for high-traffic reads. Add `Cache-Control` headers.
5. **Vercel env vars need redeploy** — after `vercel env add`, must redeploy for the var to take effect.
6. **Public repo = readable by anyone** — the JSON data files are public. Password hashes should never be stored in plain text in production (acceptable for school projects).

## Migration from JSONBlob

If already using JSONBlob and migrating to GitHub:
1. Create GitHub repo + files with same data
2. Update API route to point to GitHub instead of JSONBlob
3. Keep the same `/api/data/[key]` URL pattern — client code doesn't change
4. Add `GITHUB_TOKEN` env var to Vercel
5. Redeploy
