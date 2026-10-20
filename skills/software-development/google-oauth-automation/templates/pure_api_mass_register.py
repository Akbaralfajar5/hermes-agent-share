#!/usr/bin/env python3
"""
Template: Pure API Mass Registration via Google OAuth + Firebase
Adapt per target app — change FIREBASE_API_KEY, CLIENT_ID, REDIRECT_URI,
and the create_and_activate() function for app-specific endpoints.

RUN:
    python3 mass_register.py -w 5
    python3 mass_register.py -w 3 --dry-run
"""
import sys, json, re, os, time, argparse, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

sys.stdout.reconfigure(line_buffering=True)

# ─── ADAPT THESE PER TARGET APP ──────────────────────────────────
FIREBASE_API_KEY = "AIzaSy..."
CLIENT_ID = "XXXXXXXXX.apps.googleusercontent.com"
REDIRECT_URI = "https://PROJECT.firebaseapp.com/__/auth/handler"
COOKIES_DIR = "cookies"
ACCOUNTS_FILE = "accounts.txt"
OUTPUT_FILE = "results.txt"
# ──────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument('-w', '--workers', type=int, default=5)
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()

print_lock = threading.Lock()
output_lock = threading.Lock()


def log(msg):
    with print_lock:
        print(msg, flush=True)


def write_result(email, status):
    with output_lock:
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"{email}|{status}\n")


def load_google_cookies(cookie_file):
    """Load Google cookies from JSON file. Returns (requests.Session, pw_cookies, count)."""
    with open(cookie_file) as f:
        data = json.load(f)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    })

    pw_cookies = []
    count = 0
    for c in data.get('cookies', []):
        domain = c.get('domain', '')
        if 'google.com' in domain or 'google.co' in domain:
            session.cookies.set(c['name'], c['value'], domain=domain)
            pw_cookies.append({
                'name': c['name'], 'value': c['value'],
                'domain': domain, 'path': c.get('path', '/'),
                **({'expires': c['expires']} if c.get('expires') else {}),
                **({'httpOnly': True} if c.get('httpOnly') else {}),
                **({'secure': True} if c.get('secure') else {}),
            })
            count += 1

    return session, pw_cookies, count


def get_oauth_silent(session, email):
    """Silent OAuth (prompt=none). Works if user previously consented."""
    try:
        r = session.get("https://accounts.google.com/o/oauth2/auth", params={
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "id_token token",
            "scope": "openid email profile",
            "nonce": f"n_{int(time.time())}",
            "prompt": "none",
            "login_hint": email,
        }, allow_redirects=False, timeout=15)

        loc = r.headers.get('Location', '')
        if 'id_token=' in loc:
            return (
                re.search(r'id_token=([^&]+)', loc).group(1),
                re.search(r'access_token=([^&]+)', loc).group(1)
            )
    except:
        pass
    return None


def get_oauth_consent(pw_cookies, email):
    """Headless Playwright consent click. ~3s per account."""
    from playwright.sync_api import sync_playwright

    pw = None
    browser = None
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
        context = browser.new_context()
        context.add_cookies(pw_cookies)
        page = context.new_page()

        oauth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
            f"&response_type=id_token%20token&scope=openid%20email%20profile"
            f"&nonce=n_{int(time.time())}&login_hint={email}"
        )
        page.goto(oauth_url, wait_until='networkidle', timeout=30000)
        time.sleep(1)

        # Already redirected?
        if 'id_token=' in page.url:
            m = re.search(r'id_token=([^&]+)', page.url)
            a = re.search(r'access_token=([^&]+)', page.url)
            return m.group(1), a.group(1) if a else None

        # Click consent
        for sel in ['button:has-text("Allow")', 'button:has-text("Continue")',
                    '#submit_approve_access', 'button:has-text("Lanjutkan")']:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    page.wait_for_url("**/auth/handler*", timeout=15000)
                    break
            except:
                continue

        if 'id_token=' in page.url:
            m = re.search(r'id_token=([^&]+)', page.url)
            a = re.search(r'access_token=([^&]+)', page.url)
            return m.group(1), a.group(1) if a else None
        return None
    except:
        return None
    finally:
        try:
            if browser: browser.close()
        except: pass
        try:
            if pw: pw.stop()
        except: pass


def get_firebase_token(id_token, access_token):
    """Exchange Google OAuth for Firebase auth."""
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody": f"id_token={id_token}&access_token={access_token}&providerId=google.com",
            "requestUri": "https://app.target.com",  # ADAPT
            "returnIdpCredential": True,
            "returnSecureToken": True
        }, timeout=15)
    fb = r.json()
    if 'idToken' in fb:
        return fb['idToken'], fb.get('localId', ''), fb.get('email', '')
    return None, None, None


def create_and_activate(firebase_token, email, uid):
    """
    ADAPT THIS: App-specific registration + activation.
    Returns status string starting with 'done' on success.
    """
    api = requests.Session()
    api.cookies.set("token", firebase_token, domain="app.target.com")  # ADAPT domain
    headers = {
        "Authorization": f"Bearer {firebase_token}",
        "Content-Type": "application/json",
        "Origin": "https://app.target.com",  # ADAPT
    }

    # Example: create workspace
    r = api.post("https://app.target.com/api/start/create-workspace", headers=headers, json={
        "workspaceName": email.split('@')[0] + "-ws",
        "timezone": "America/New_York",
        "creatorEmail": email,
        "creatorUid": uid
    }, timeout=20)

    if r.status_code != 200:
        return f"workspace_{r.status_code}"

    network_id = r.json().get('networkId', '')
    if not network_id:
        return "no_network_id"

    # Example: activate free trial
    r = api.post("https://app.target.com/api/start/free-trial", headers=headers, json={
        "networkId": network_id, "quantity": 1
    }, timeout=20)

    if r.status_code == 200:
        return f"done|{network_id}"
    return f"trial_{r.status_code}"


def process_account(email, idx, total):
    """Full flow for one account."""
    cookie_file = Path(COOKIES_DIR) / f"{email}.json"
    if not cookie_file.exists():
        write_result(email, "no_cookies")
        return

    try:
        session, pw_cookies, count = load_google_cookies(cookie_file)
    except:
        write_result(email, "cookie_error")
        return

    if count < 5:
        write_result(email, "insufficient_cookies")
        return

    # OAuth: silent first, consent fallback
    result = get_oauth_silent(session, email)
    method = "silent"
    if not result:
        result = get_oauth_consent(pw_cookies, email)
        method = "consent"

    if not result:
        log(f"[{idx}/{total}] ❌ {email} — OAuth failed")
        write_result(email, "oauth_failed")
        return

    id_token, access_token = result

    # Firebase
    firebase_token, uid, _ = get_firebase_token(id_token, access_token)
    if not firebase_token:
        log(f"[{idx}/{total}] ❌ {email} — Firebase failed")
        write_result(email, "firebase_failed")
        return

    if args.dry_run:
        log(f"[{idx}/{total}] ✅ {email} — auth OK ({method}) [dry-run]")
        write_result(email, f"dry_run_ok|{method}")
        return

    # App-specific registration
    status = create_and_activate(firebase_token, email, uid)
    if status.startswith("done"):
        log(f"[{idx}/{total}] ✅ {email} — {status.split('|')[0]} ({method})")
    else:
        log(f"[{idx}/{total}] ❌ {email} — {status}")
    write_result(email, status)


def main():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ {ACCOUNTS_FILE} not found!")
        return

    with open(ACCOUNTS_FILE) as f:
        accounts = [l.strip() for l in f if l.strip() and '@' in l]

    done = set()
    try:
        with open(OUTPUT_FILE) as f:
            for line in f:
                if '|' in line and line.strip().split('|')[1].startswith('done'):
                    done.add(line.strip().split('|')[0])
    except FileNotFoundError:
        pass

    remaining = [a for a in accounts if a not in done]
    has_cookies = [a for a in remaining if Path(COOKIES_DIR, f"{a}.json").exists()]

    print(f"{'='*55}")
    print(f"  Mass Registration (Pure API + Headless Consent)")
    print(f"{'='*55}")
    print(f"  Total: {len(accounts)} | Done: {len(done)} | Remaining: {len(remaining)}")
    print(f"  With cookies: {len(has_cookies)} | Workers: {args.workers}")
    print(f"{'='*55}\n")

    if not has_cookies:
        print("❌ No accounts with cookies!")
        return

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_account, e, i+1, len(has_cookies))
                   for i, e in enumerate(has_cookies)]
        for f in as_completed(futures):
            try: f.result()
            except Exception as e: log(f"⚠️ Thread error: {e}")

    # Summary
    done_n = sum(1 for l in open(OUTPUT_FILE) if '|done' in l)
    fail_n = sum(1 for l in open(OUTPUT_FILE) if '|' in l and '|done' not in l and '|dry_run' not in l)
    print(f"\n{'='*55}")
    print(f"  ✅ Success: {done_n} | ❌ Failed: {fail_n}")
    print(f"{'='*55}")


if __name__ == '__main__':
    main()
