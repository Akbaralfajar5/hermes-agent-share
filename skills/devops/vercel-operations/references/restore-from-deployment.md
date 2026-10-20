# Restore Source from a Deployed Vercel App

Use this when the user wants to edit a `*.vercel.app` project whose source is not in `~`. Verified working for `seminar-deck` (single-file HTML, 2 MB).

## Step 1 — Find the project

```bash
export VERCEL_TOKEN="vcp_..."  # from memory
curl -s "https://api.vercel.com/v9/projects?limit=100" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | \
python3 -c "
import json, sys
d = json.load(sys.stdin)
for p in d.get('projects', []):
    if 'seminar' in p['name'].lower():
        latest = (p.get('latestDeployments') or [{}])[0]
        print(p['name'], '|', p.get('id'), '|', latest.get('url',''))
"
```

## Step 2 — Get the production deployment id

```bash
PROJECT_ID="prj_xxxxx"
curl -s "https://api.vercel.com/v6/deployments?projectId=${PROJECT_ID}&limit=3&target=production" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | \
python3 -c "
import json, sys
d = json.load(sys.stdin)
for x in d.get('deployments', []):
    print(x['uid'], x.get('url',''), x.get('createdAt',''))
"
```

Pick the most recent `dpl_xxx`.

## Step 3 — Walk the file tree

```bash
DPL="dpl_xxxxx"
curl -s "https://api.vercel.com/v6/deployments/${DPL}/files" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | python3 -m json.tool
```

Response is a recursive tree of `{name, type, mode, uid?, children?}`. Files have `uid`; directories have `children`. The `src/` prefix is part of Vercel's source-file storage — when you reconstruct, you usually want files at the root unless the original layout truly had `src/`.

## Step 4 — Download & base64-decode each file

This is the trap: `data` is base64 even when `encoding` is null.

```python
import json, base64, os, requests

TOKEN = os.environ["VERCEL_TOKEN"]
DPL = "dpl_xxxxx"
OUT = os.path.expanduser("~/seminar-deck")
os.makedirs(OUT, exist_ok=True)

def fetch(uid, dest_path):
    r = requests.get(
        f"https://api.vercel.com/v7/deployments/{DPL}/files/{uid}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    payload = r.json()
    raw = base64.b64decode(payload["data"])
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(raw)
    print("wrote", dest_path, len(raw), "bytes")

def walk(node, prefix=""):
    if node.get("type") == "directory":
        for child in node.get("children", []):
            # Strip the leading 'src/' that Vercel adds for source-file storage
            sub = child["name"] if prefix == "" and node.get("name") == "src" else os.path.join(prefix, child["name"])
            walk(child, sub if node.get("name") == "src" else os.path.join(prefix, node.get("name", "")))
    elif node.get("uid"):
        fetch(node["uid"], os.path.join(OUT, prefix or node["name"]))

tree = requests.get(
    f"https://api.vercel.com/v6/deployments/{DPL}/files",
    headers={"Authorization": f"Bearer {TOKEN}"},
).json()

for top in tree:
    walk(top)
```

For single-file projects (like `seminar-deck`), the tree was simply:

```json
[{"name":"src","type":"directory","children":[{"name":"index.html","uid":"...","type":"file"}]}]
```

So just one fetch is needed:

```bash
curl -s "https://api.vercel.com/v7/deployments/${DPL}/files/${UID}" \
  -H "Authorization: Bearer $VERCEL_TOKEN" > /tmp/file_resp.json

python3 -c "
import json, base64
d = json.load(open('/tmp/file_resp.json'))
open('$HOME/<project>/index.html','wb').write(base64.b64decode(d['data']))
"
```

## Step 5 — Edit, then redeploy

After restore, drop `vercel.json` (use `templates/static-vercel.json`) and run:

```bash
cd ~/<project>
timeout 240 vercel deploy --prod --yes --token "$VERCEL_TOKEN"
```

If the dir is fresh, the CLI will prompt to link — `--yes` accepts the existing matching project automatically.

## Pitfalls observed in this restore

- Response had `"encoding": null` but data was still base64. Probe-decode the first 200 chars to confirm: if all chars are `[A-Za-z0-9+/=]`, it's base64.
- The `src/` directory in the file tree is Vercel's internal source-file convention, not user-authored layout. For static single-file projects you usually want `index.html` at the project root, not `src/index.html`.
- Production aliases with `ssoProtection` enabled still serve the public alias (`<name>.vercel.app`) without auth, but the deploy-hash URL requires login. Verify against the alias.
