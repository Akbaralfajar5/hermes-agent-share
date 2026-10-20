#!/usr/bin/env python3
"""
b.ai Credit Claimer — Multi-Worker Edition
===========================================
Claim 500K free credits in parallel. Supports resume, headless, configurable concurrency.

⚠️  NOTE: The claim button opens the Welcome Gift modal, but Cloudflare Turnstile
    blocks the actual credit grant with a "Verifying..." spinner. The balance stays
    at 0 unless a captcha solver (2Captcha/CapSolver/Anti-Captcha) is integrated.
    This script captures the click but the claim may not go through without a solver.
    See browser-automation SKILL.md → "b.ai Credit Claiming" section for details.

Usage:
    python bai-claim-credits.py --workers 5
    python bai-claim-credits.py --workers 10 --headless --resume

Requirements:
    pip install playwright cloakbrowser
    python -m playwright install chromium

Environment:
    GMAIL_PASS — shared password for all GSuite accounts (default: qwertyui)
"""

import sys, time, os, json, threading, queue, argparse, datetime

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

GMAIL_PASS = os.environ.get("GMAIL_PASS", "qwertyui")
APIKEYS_FILE = "bai_apikeys.txt"
OUTPUT_FILE = "bai_claims_multi.txt"
LOCK = threading.Lock()

BROWSER_ARGS = [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
    "--disable-software-rasterizer", "--disable-extensions",
    "--disable-component-update",
]


def google_oauth(page, email):
    """Login via Google OAuth — return True if logged in"""
    for attempt in range(3):
        try:
            page.goto("https://chat.b.ai/chat", timeout=60000, wait_until="load")
            time.sleep(5)

            # Click "Log in"
            page.evaluate(
                """()=>{document.querySelectorAll('button').forEach(b=>{
                    if(b.textContent.trim()==='Log in')b.click()
                })}"""
            )
            time.sleep(4)

            # Open Google popup
            with page.expect_popup(timeout=15000) as pi:
                page.click("text=Continue with Google")
            gp = pi.value
            break
        except Exception as e:
            print(f"  ⚠️ Google popup attempt {attempt+1}/3: {e}")
            if attempt < 2:
                page.evaluate(
                    """()=>{localStorage.clear();sessionStorage.clear();
                    document.cookie.split(";").forEach(c=>{
                        document.cookie=c.replace(/^ +/,"").replace(/=.*/,
                            "=;expires="+new Date().toUTCString()+";path=/")
                    })}"""
                )
                page.reload(wait_until="load")
                time.sleep(5)
                continue
            else:
                return False

    try:
        gp.wait_for_load_state("load", timeout=30000)
    except:
        pass
    time.sleep(3)

    # Enter email
    try:
        gp.fill('input[type="email"]', email)
        gp.locator("#identifierNext").click()
        time.sleep(5)
    except:
        try:
            gp.close()
        except:
            pass
        return False

    # Enter password
    try:
        gp.fill('input[type="password"]', GMAIL_PASS)
        gp.locator("#passwordNext").click()
        time.sleep(8)
    except:
        try:
            gp.close()
        except:
            pass
        return False

    # Handle post-login prompts (Continue, Allow, Accept, etc.)
    for _ in range(15):
        try:
            url = gp.url
        except:
            break
        if url.startswith("https://chat.b.ai"):
            break
        if "gsi/transform" in url:
            time.sleep(1)
            continue
        try:
            for sel in [
                'button:has-text("Continue")',
                'button:has-text("Allow")',
                'button:has-text("Accept")',
                'button:has-text("I agree")',
                "#confirm",
            ]:
                btn = gp.locator(sel).first
                if btn.count() and btn.is_visible():
                    btn.click()
                    time.sleep(4)
                    break
        except:
            pass
        time.sleep(1)

    try:
        gp.close()
    except:
        pass
    time.sleep(3)

    # Reload main page and verify login
    page.reload(wait_until="load")
    time.sleep(6)

    body = page.inner_text("body")
    if "AO_" in body or "New Chat" in body:
        return True
    return False


def claim_credits(page, email):
    """Claim 500K free credits — no wallet needed, but Turnstile blocks the grant"""
    page.goto("https://chat.b.ai/chat", timeout=30000, wait_until="load")
    time.sleep(4)

    # Method 1: Click "Claim Free Credits" or "500K" button
    page.evaluate(
        """()=>{
            document.querySelectorAll('button, span, a, div[role="button"]').forEach(el=>{
                var t = el.textContent.trim();
                if (t.includes("Claim") || t.includes("500K") || 
                    t.includes("500,000") || t.includes("Free Credits") || 
                    t.includes("Gift")) {
                    if (el.offsetParent !== null) el.click();
                }
            });
        }"""
    )
    time.sleep(4)

    # Method 2: Click top-up/bonus banner
    page.evaluate(
        """()=>{
            document.querySelectorAll('*').forEach(el=>{
                var t = el.textContent.trim();
                if ((t.includes("Top-up") || t.includes("Bonus") || 
                     t.includes("Deposit Match")) && el.offsetParent !== null) {
                    el.click();
                }
            });
        }"""
    )
    time.sleep(2)

    # Check for Turnstile spinner (signals the claim was BLOCKED, not granted)
    verifying_spinner = page.evaluate(
        """() => {
            const modals = document.querySelectorAll('[class*=\"modal\"], [role=\"dialog\"]');
            for (const m of modals) {
                if (m.textContent.includes('Verifying') || m.textContent.includes('v1fy1ng')) {
                    return m.textContent.substring(0, 200);
                }
            }
            return null;
        }"""
    )
    if verifying_spinner:
        print(f"  ⚠️ Turnstile spinning — claim blocked")
        return "needs_captcha"

    # Verify via Usage page (real balance check, not modal detection)
    try:
        page.goto("https://chat.b.ai/usage", timeout=15000, wait_until="load")
        time.sleep(3)
        body = page.inner_text("body")
        if "500" in body and ("credit" in body.lower() or "balance" in body.lower()):
            return True
        # Also check if balance shows 0 (not claimed)
        zero_balance = page.evaluate(
            """() => {
                const els = document.querySelectorAll('[class*=\"balance\"], [class*=\"credit\"]');
                for (const el of els) {
                    const t = el.textContent.trim();
                    if (t.includes('0') || t === '0') return 'zero';
                    if (t.includes('500')) return 'has_credits';
                }
                return null;
            }"""
        )
        if zero_balance == 'zero':
            return False
        if zero_balance == 'has_credits':
            return True
    except:
        pass

    return None  # Unknown state


def sign_out(page):
    """Sign out from b.ai"""
    try:
        page.evaluate(
            """()=>{const a=document.querySelector('.ant-avatar');if(a)a.click()}"""
        )
        time.sleep(2)
        page.evaluate(
            """()=>{document.querySelectorAll('*').forEach(el=>{
                if(el.children.length===0&&el.textContent.trim()==='Log out')el.click()
            })}"""
        )
        time.sleep(4)
        page.evaluate(
            """()=>{document.querySelectorAll('button').forEach(b=>{
                if(b.textContent.trim().toLowerCase().includes('sign out')&&
                   b.offsetParent!==null)b.click()
            })}"""
        )
        time.sleep(2)
    except:
        pass
    page.goto("https://chat.b.ai/chat", timeout=30000, wait_until="load")
    time.sleep(3)


def save_result(results):
    """Thread-safe save to output file — re-write entire file from list"""
    with LOCK:
        with open(OUTPUT_FILE, "w") as f:
            for r in results:
                status = (
                    "claimed" if r["claimed"] is True
                    else "unknown" if r["claimed"] is None
                    else "failed"
                )
                f.write(f"{r['email']}|{status}\n")


def worker(worker_id, q, results_ref):
    """Worker thread — process accounts from queue"""
    from cloakbrowser import launch_context

    while True:
        try:
            email, key = q.get_nowait()
        except queue.Empty:
            break

        result = {"email": email, "claimed": False}

        try:
            ctx = launch_context(
                headless=HEADLESS,
                stealth_args=True,
                humanize=False,
                locale="en-US",
                timezone="America/Los_Angeles",
                args=BROWSER_ARGS,
            )
            page = ctx.new_page()

            # Login
            if not google_oauth(page, email):
                result["claimed"] = False
            else:
                # Claim
                claim_result = claim_credits(page, email)
                result["claimed"] = claim_result

            sign_out(page)
            ctx.close()
        except Exception as e:
            result["claimed"] = False

        # Thread-safe save + progress
        with LOCK:
            results_ref.append(result)
            save_result(results_ref)
            claimed = sum(1 for r in results_ref if r["claimed"] is True)
            unknown = sum(1 for r in results_ref if r["claimed"] is None)
            failed = sum(1 for r in results_ref if r["claimed"] is False)
            print(f"[W{worker_id}] {email}: {result['claimed']} | "
                  f"Progress: {claimed}✅ {unknown}⚠️ {failed}❌ "
                  f"({len(results_ref)}/{len(accounts_total)})",
                  flush=True)

        q.task_done()
        time.sleep(2)  # Cooldown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="b.ai Credit Claimer — Multi-Worker")
    parser.add_argument("--workers", type=int, default=3,
                        help="Number of parallel workers (default: 3)")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browsers headlessly")
    parser.add_argument("--visible", action="store_false", dest="headless",
                        help="Show browser windows")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already processed accounts")
    parser.add_argument("--file", default=APIKEYS_FILE,
                        help=f"API keys file (default: {APIKEYS_FILE})")
    args = parser.parse_args()
    HEADLESS = args.headless

    # Load accounts
    accounts = []
    with open(args.file) as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                email, key = line.split("|", 1)
                accounts.append((email, key))

    # Resume: skip already processed
    if args.resume:
        done = set()
        try:
            with open(OUTPUT_FILE) as f:
                for line in f:
                    if "|" in line:
                        done.add(line.strip().split("|")[0])
        except FileNotFoundError:
            pass
        if done:
            accounts = [(e, k) for e, k in accounts if e not in done]
            print(f"Resume mode: skipping {len(done)} already processed")

    if not accounts:
        print("No accounts to process!")
        sys.exit(0)

    accounts_total = accounts  # For progress display in workers
    q = queue.Queue()
    for acc in accounts:
        q.put(acc)

    results = []
    threads = []

    print(f"b.ai Credit Claimer — {args.workers} workers")
    print(f"Accounts: {len(accounts)} | Headless: {HEADLESS} | Resume: {args.resume}")
    print()

    for wid in range(1, args.workers + 1):
        t = threading.Thread(target=worker, args=(wid, q, results), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(2)  # Stagger startup

    for t in threads:
        t.join()

    # Final summary
    claimed = sum(1 for r in results if r["claimed"] is True)
    unknown = sum(1 for r in results if r["claimed"] is None)
    failed = sum(1 for r in results if r["claimed"] is False)

    print()
    print("═" * 50)
    print(f"  ✅ Claimed: {claimed}")
    print(f"  ⚠️ Unknown (may already have): {unknown}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📄 Results saved to: {OUTPUT_FILE}")
    print("═" * 50)

    save_result(results)
