#!/usr/bin/env python3
"""
Template: Multi-Worker Google OAuth Login
- Single terminal, N parallel workers
- Browser stays open after login (manual post-login action)
- Batch processing with ENTER prompt between batches

Customize:
- GMAIL_PASS: account password
- ACCOUNTS_FILE: one email per line
- TARGET_URL: the app to login to
- num_workers: parallel browser count (5-10 safe)
"""
import sys, time, os, argparse, threading
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(line_buffering=True)

# ─── CONFIG (customize these) ────────────────────────────────────
GMAIL_PASS = "your_password"
ACCOUNTS_FILE = "accounts.txt"
OUTPUT_FILE = "results.txt"
TARGET_URL = "https://target-app.com"
# ──────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument('-w', '--workers', type=int, default=5)
args = parser.parse_args()

print_lock = threading.Lock()
output_lock = threading.Lock()
open_browsers = []


def log(msg):
    with print_lock:
        print(msg, flush=True)


def write_result(email, status):
    with output_lock:
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"{email}|{status}\n")


def login_one(email, idx, total):
    """Login 1 account. Browser stays open on success."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--no-sandbox",
              "--disable-blink-features=AutomationControlled",
              "--disable-features=IsolateOrigins,site-per-process"]
    )
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        locale='en-US', timezone_id='America/Los_Angeles'
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
    """)
    page = context.new_page()

    def fail(reason):
        try: browser.close()
        except: pass
        try: pw.stop()
        except: pass
        log(f"[{idx}/{total}] ❌ {email} — {reason}")
        write_result(email, f"login_{reason}")

    try:
        page.goto(TARGET_URL, timeout=60000, wait_until='load')
        time.sleep(3)

        # === CUSTOMIZE: Click login button ===
        page.evaluate('''()=>{
            document.querySelectorAll('button').forEach(b=>{
                if(b.textContent.trim()==='Log in') b.click()
            })
        }''')
        time.sleep(3)

        # === Google popup ===
        try:
            with page.expect_popup(timeout=15000) as pi:
                page.click('text=Continue with Google')
            gp = pi.value
        except:
            fail("popup_failed"); return

        try: gp.wait_for_load_state('load', timeout=30000)
        except: pass
        time.sleep(2)

        # Email
        try:
            ei = gp.locator('input[type="email"]')
            ei.wait_for(state='visible', timeout=15000)
            ei.fill(email)
            gp.locator('#identifierNext').click()
            time.sleep(4)
        except:
            try: gp.close()
            except: pass
            fail("email_error"); return

        # Password
        try:
            pw_input = gp.locator('input[name="Passwd"]')
            pw_input.wait_for(state='visible', timeout=15000)
            pw_input.fill(GMAIL_PASS)
            gp.locator('#passwordNext').click()
            time.sleep(6)
        except:
            try: gp.close()
            except: pass
            fail("password_error"); return

        # Consent
        for _ in range(5):
            try:
                body = gp.inner_text('body')
                if 'Continue' in body or 'Allow' in body:
                    for sel in ['button:has-text("Continue")', 'button:has-text("Allow")', '#submit_approve_access']:
                        btn = gp.locator(sel).first
                        if btn.count() and btn.is_visible():
                            btn.click()
                            time.sleep(4)
                            break
                    break
            except: break
            time.sleep(2)

        # Wait popup close
        for _ in range(20):
            try: _ = gp.url
            except: break
            time.sleep(1)
        try: gp.close()
        except: pass
        time.sleep(2)

        page.reload(wait_until='load')
        time.sleep(5)

        # === CUSTOMIZE: Verify login success ===
        session = page.evaluate('''async()=>{
            try { const r = await fetch('/api/auth/session',{credentials:'include'}); return await r.json(); }
            catch(e) { return null; }
        }''')

        if not session or not session.get('user'):
            fail("login_failed"); return

        # SUCCESS — keep browser open
        open_browsers.append((browser, pw))
        log(f"[{idx}/{total}] ✅ {email} — logged in")
        write_result(email, "logged_in")

    except Exception as e:
        fail(f"error:{str(e)[:50]}")


def main():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ {ACCOUNTS_FILE} not found!"); return

    with open(ACCOUNTS_FILE) as f:
        accounts = [l.strip() for l in f if l.strip() and '@' in l]

    # Filter already done
    done = set()
    try:
        with open(OUTPUT_FILE) as f:
            for line in f:
                if '|' in line:
                    done.add(line.strip().split('|')[0])
    except FileNotFoundError: pass

    remaining = [a for a in accounts if a not in done]
    num_workers = min(args.workers, len(remaining))

    print(f"Total: {len(accounts)} | Done: {len(done)} | Remaining: {len(remaining)} | Workers: {num_workers}")

    if not remaining:
        print("✅ All done!"); return

    # Process in batches
    for i in range(0, len(remaining), num_workers):
        batch = remaining[i:i+num_workers]
        threads = []
        for j, email in enumerate(batch):
            t = threading.Thread(target=login_one, args=(email, i+j+1, len(remaining)))
            threads.append(t)
            t.start()
            time.sleep(0.5)

        for t in threads:
            t.join()

        print(f"\n  Batch done — {len(open_browsers)} browsers open")
        if i + num_workers < len(remaining):
            input("  ⏸️  ENTER for next batch...")

    print(f"\n  ALL DONE! {len(open_browsers)} browsers open. Ctrl+C to close all.")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        for browser, pw_inst in open_browsers:
            try: browser.close()
            except: pass
            try: pw_inst.stop()
            except: pass


if __name__ == '__main__':
    main()
