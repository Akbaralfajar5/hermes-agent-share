"""
Template: Single-terminal multi-worker for mass account operations.
Pattern: ThreadPoolExecutor + per-thread Playwright instance.

Adapt: replace do_login() and do_claim() with target app logic.
"""
import argparse, json, os, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

ACCOUNTS_FILE = "accounts.txt"
OUTPUT_FILE = "results.txt"
COOKIES_DIR = "cookies"
GMAIL_PASS = "YOUR_PASS"

Path(COOKIES_DIR).mkdir(exist_ok=True)
print_lock = threading.Lock()
output_lock = threading.Lock()

parser = argparse.ArgumentParser()
parser.add_argument('-w', '--workers', type=int, default=5)
parser.add_argument('--phase', choices=['login', 'claim', 'both'], default='both')
args = parser.parse_args()


def log(wid, msg):
    with print_lock:
        print(f"  [W{wid:02d}] {msg}", flush=True)


def write_result(email, status):
    with output_lock:
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"{email}|{status}\n")


def split_list(lst, n):
    k, m = divmod(len(lst), n)
    return [lst[i*k+min(i,m):(i+1)*k+min(i+1,m)] for i in range(n)]


# ─── PHASE 1: LOGIN (headless) ───────────────────────────────────
def login_worker(wid, emails):
    results = {'ok': 0, 'fail': 0}
    with sync_playwright() as p:
        for email in emails:
            if os.path.exists(f"{COOKIES_DIR}/{email}.json"):
                continue
            status = do_login(p, email)
            if status == "ok":
                log(wid, f"✅ {email}")
                results['ok'] += 1
            else:
                log(wid, f"❌ {email} — {status}")
                results['fail'] += 1
                write_result(email, f"login_{status}")
    return results


def do_login(p, email):
    """ADAPT THIS: Login to target app, save cookies."""
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={'width': 1280, 'height': 720})
    page = context.new_page()
    try:
        # ... your login logic ...
        # On success:
        cookies = context.cookies()
        with open(f"{COOKIES_DIR}/{email}.json", 'w') as f:
            json.dump({'cookies': cookies}, f)
        return "ok"
    except Exception as e:
        return f"error:{str(e)[:50]}"
    finally:
        browser.close()


# ─── PHASE 2: CLAIM (non-headless for Turnstile) ─────────────────
def claim_worker(wid, emails):
    results = {'claimed': 0, 'fail': 0}
    with sync_playwright() as p:
        for email in emails:
            status = do_claim(p, email)
            if status == "claimed":
                log(wid, f"✅ {email}")
                results['claimed'] += 1
                write_result(email, "claimed")
            else:
                log(wid, f"❌ {email} — {status}")
                results['fail'] += 1
                write_result(email, status)
    return results


def do_claim(p, email):
    """ADAPT THIS: Load cookies, do Turnstile-gated action."""
    cookie_file = f"{COOKIES_DIR}/{email}.json"
    if not os.path.exists(cookie_file):
        return "no_cookies"
    with open(cookie_file) as f:
        data = json.load(f)

    browser = p.chromium.launch(headless=False, args=["--no-sandbox"])
    context = browser.new_context(viewport={'width': 1280, 'height': 720})
    context.add_cookies(data['cookies'])
    page = context.new_page()
    try:
        # ... your claim logic ...
        # Wait for Turnstile: poll btn.disabled until False
        return "claimed"
    except Exception as e:
        return f"error:{str(e)[:50]}"
    finally:
        browser.close()


# ─── MAIN ────────────────────────────────────────────────────────
def main():
    with open(ACCOUNTS_FILE) as f:
        accounts = [l.strip() for l in f if l.strip() and '@' in l]

    done = set()
    try:
        with open(OUTPUT_FILE) as f:
            for line in f:
                if '|' in line:
                    parts = line.strip().split('|')
                    if parts[1] in ('claimed', 'already_claimed'):
                        done.add(parts[0])
    except FileNotFoundError:
        pass

    remaining = [a for a in accounts if a not in done]
    n = min(args.workers, len(remaining))
    chunks = split_list(remaining, n)

    if args.phase in ('login', 'both'):
        print(f"Phase 1: Login ({n} workers)")
        with ThreadPoolExecutor(max_workers=n) as pool:
            futures = [pool.submit(login_worker, i+1, c) for i, c in enumerate(chunks)]
            for f in as_completed(futures):
                f.result()

    if args.phase in ('claim', 'both'):
        claimable = [e for e in remaining if os.path.exists(f"{COOKIES_DIR}/{e}.json")]
        n2 = min(n, len(claimable))
        chunks2 = split_list(claimable, n2)
        print(f"Phase 2: Claim ({n2} workers)")
        with ThreadPoolExecutor(max_workers=n2) as pool:
            futures = [pool.submit(claim_worker, i+1, c) for i, c in enumerate(chunks2)]
            for f in as_completed(futures):
                f.result()


if __name__ == '__main__':
    main()
