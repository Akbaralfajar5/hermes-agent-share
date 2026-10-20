#!/usr/bin/env python3
"""
b.ai Mass API Key Generator - Google OAuth via CloakBrowser
Pattern: login → claim 500K credits → create API key → sign out → next
Resume-safe: skips accounts already in output file
"""
import sys, time, re, random, os, json
from datetime import datetime
from cloakbrowser import launch_context

sys.stdout.reconfigure(line_buffering=True)

# ─── CONFIG ───────────────────────────────────────────────────────
GMAIL_PASS = os.environ.get("GMAIL_PASS", "yourpassword")
ACCOUNTS_FILE = os.environ.get("ACCOUNTS_FILE", "accounts.txt")
OUTPUT_FILE = "bai_apikeys.txt"
MAX_KEYS_PER_ACCOUNT = 1

ARGS = [
    "--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
    "--disable-software-rasterizer","--disable-extensions","--disable-component-update"
]

# ─── HELPERS ──────────────────────────────────────────────────────
def rand_name():
    a=["nova","swift","zen","flux","apex","echo","vibe","core","peak","orbit"]
    n=["dev","hub","net","api","key","sync","flow","link","core","base"]
    return f"{random.choice(a)}-{random.choice(n)}-{random.randint(100,999)}"

def extract_key(text):
    m = re.search(r'(sk-[a-zA-Z0-9]{20,60})', text)
    return m.group(1) if m else None

def close_modals(page):
    for _ in range(3):
        c = page.evaluate('''()=>{let c=false;
            document.querySelectorAll('.ant-modal-close,[aria-label="Close"]').forEach(b=>{if(b.offsetParent!==null){b.click();c=true}});
            return c}''')
        if not c: break
        time.sleep(1)

def sign_out(page):
    close_modals(page)
    time.sleep(1)
    page.evaluate('''()=>{const a=document.querySelector('.ant-avatar');if(a)a.click()}''')
    time.sleep(2)
    page.evaluate('''()=>{document.querySelectorAll('*').forEach(el=>{if(el.children.length===0&&el.textContent.trim()==='Log out')el.click()})}''')
    time.sleep(4)
    try:
        page.evaluate('''()=>{document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim().toLowerCase().includes('sign out')&&b.offsetParent!==null)b.click()})}''')
        time.sleep(2)
    except: pass
    page.goto('https://chat.b.ai/chat', timeout=30000, wait_until='load')
    time.sleep(5)
    for _ in range(15):
        try:
            if 'Log in' in page.inner_text('body'): return True
        except: pass
        time.sleep(1)
    page.reload(wait_until='load')
    time.sleep(5)
    return True

def claim_credits(page):
    """Claim 500K free credits (no wallet needed — gift for new users)."""
    print(f"  Claiming credits...", end=" ")
    try:
        page.goto('https://chat.b.ai/chat', timeout=30000, wait_until='load')
        time.sleep(4)
        page.evaluate('''()=>{
            document.querySelectorAll('button, span, a, div[role="button"]').forEach(el=>{
                var t = el.textContent.trim();
                if (t.includes("Claim") || t.includes("500K") || t.includes("500,000") || t.includes("Free Credits") || t.includes("Gift")) {
                    if (el.offsetParent !== null) el.click();
                }
            });
        }''')
        time.sleep(4)
        page.evaluate('''()=>{
            document.querySelectorAll('*').forEach(el=>{
                var t = el.textContent.trim();
                if ((t.includes("Top-up") || t.includes("Bonus") || t.includes("Deposit Match")) && el.offsetParent !== null) {
                    el.click();
                }
            });
        }''')
        time.sleep(2)
        print("✅")
    except Exception as e:
        print(f"⚠️ {e}")

def google_oauth(page, email):
    """Google OAuth login with 3-attempt retry + storage clearing."""
    for attempt in range(3):
        page.goto('https://chat.b.ai/chat', timeout=60000, wait_until='load')
        time.sleep(5)
        page.evaluate('''()=>{document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim()==='Log in')b.click()})}''')
        time.sleep(4)
        try:
            with page.expect_popup(timeout=15000) as pi:
                page.click('text=Continue with Google')
            gp = pi.value
            break
        except Exception as e:
            print(f"  ⚠️ Google popup attempt {attempt+1}/3: {e}")
            if attempt < 2:
                page.evaluate('()=>{localStorage.clear();sessionStorage.clear();document.cookie.split(";").forEach(c=>{document.cookie=c.replace(/^ +/,"").replace(/=.*/,"=;expires="+new Date().toUTCString()+";path=/")})}')
                page.reload(wait_until='load')
                time.sleep(5)
                continue
            else:
                return "google_popup_failed"
    
    try: gp.wait_for_load_state('load', timeout=30000)
    except: pass
    time.sleep(3)
    
    ei = gp.locator('input[type="email"]')
    ei.wait_for(state='visible', timeout=15000)
    ei.fill(email)
    gp.locator('#identifierNext').click()
    time.sleep(5)
    
    try:
        txt = gp.inner_text('body')
        if "Couldn't find" in txt:
            gp.close()
            return "no_google_account"
    except: pass
    
    try:
        pw = gp.locator('input[name="Passwd"]')
        pw.wait_for(state='visible', timeout=15000)
        pw.fill(GMAIL_PASS)
        gp.locator('#passwordNext').click()
        time.sleep(8)
    except:
        gp.close()
        return "password_error"
    
    for _ in range(12):
        try: url = gp.url
        except: break
        if url.startswith('https://chat.b.ai'): break
        if 'gsi/transform' in url:
            time.sleep(1)
            continue
        try:
            for sel in ['button:has-text("Continue")','button:has-text("Allow")',
                        'button:has-text("Accept")','button:has-text("I agree")',
                        '#confirm','#submit_approve_access']:
                btn = gp.locator(sel).first
                if btn.count() and btn.is_visible():
                    btn.click()
                    time.sleep(4)
                    break
        except: pass
        time.sleep(1)
    
    try: gp.close()
    except: pass
    time.sleep(3)
    page.reload(wait_until='load')
    time.sleep(6)
    
    body = page.inner_text('body')
    if 'AO_' in body or 'Claim Free Credits' in body or 'New Chat' in body:
        if 'Log in' not in body.split('API')[0] if 'API' in body else True:
            return "ok"
    return "login_failed"

def create_api_key(page):
    """Create one API key → return key string or None."""
    page.evaluate('''()=>{
        window.__key = null;
        var orig = navigator.clipboard.writeText;
        navigator.clipboard.writeText = function(t) { window.__key = t; return orig.call(this, t); };
    }''')
    page.evaluate('''()=>{document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim()==='Create API key'&&b.offsetParent!==null)b.click()})}''')
    time.sleep(3)
    key_name = rand_name()
    page.evaluate('''(name)=>{
        var input = document.querySelector('.ant-modal input[type="text"]');
        if (input) {
            var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            s.call(input, name);
            input.dispatchEvent(new Event('input',{bubbles:true}));
            input.dispatchEvent(new Event('change',{bubbles:true}));
        }
    }''', key_name)
    time.sleep(1)
    page.evaluate('''()=>{
        var modal = document.querySelector('.ant-modal-content');
        if (modal) {
            modal.querySelectorAll('button').forEach(b=>{
                if(b.textContent.trim()==='Create API key') b.click();
            });
        }
    }''')
    time.sleep(5)
    api_key = page.evaluate('()=>window.__key')
    if not api_key or not api_key.startswith('sk-'):
        body = page.inner_text('body')
        matches = re.findall(r'sk-([a-zA-Z0-9]{30,60})', body)
        if matches: api_key = 'sk-' + matches[-1]
    if not api_key or not api_key.startswith('sk-'):
        modal_text = page.evaluate('''()=>{
            var m = document.querySelector('.ant-modal-content');
            return m ? m.textContent : '';
        }''')
        api_key = extract_key(modal_text)
    return api_key

def process_account(page, email):
    result = {"email": email, "status": "error", "keys": [], "time": datetime.now().isoformat()}
    try:
        print(f"  Login...")
        auth = google_oauth(page, email)
        if auth != "ok":
            result["status"] = auth
            print(f"  ❌ Auth failed: {auth}")
            return result
        print(f"  ✅ Logged in")
        claim_credits(page)
        try:
            page.goto('https://chat.b.ai/key', timeout=30000, wait_until='load')
        except:
            page.reload(wait_until='load')
        time.sleep(4)
        close_modals(page)
        body = page.inner_text('body')
        existing = len(re.findall(r'sk-[a-zA-Z0-9*]+', body))
        for i in range(existing, MAX_KEYS_PER_ACCOUNT):
            print(f"  Creating key {i+1}/{MAX_KEYS_PER_ACCOUNT}...")
            api_key = create_api_key(page)
            if api_key and api_key.startswith('sk-'):
                result["keys"].append(api_key)
                print(f"  ✅ {api_key}")
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(f"{email}|{api_key}\n")
                close_modals(page)
                time.sleep(2)
            else:
                print(f"  ⚠️ Key creation failed")
                break
        if result["keys"]: result["status"] = "success"
        print(f"  Signing out...")
        sign_out(page)
        print(f"  ✅ Signed out")
    except Exception as e:
        result["status"] = f"error:{str(e)[:80]}"
        print(f"  ❌ Error: {e}")
    return result

# ─── MAIN ─────────────────────────────────────────────────────────
def main():
    # Resume-safe: skip already-processed accounts
    done = set()
    try:
        with open(OUTPUT_FILE) as f:
            for line in f:
                if '|' in line:
                    done.add(line.strip().split('|')[0])
    except FileNotFoundError: pass
    
    with open(ACCOUNTS_FILE) as f:
        accounts = [l.strip() for l in f if l.strip() and '@' in l and l.strip() not in done]
    
    if done: print(f"Skipping {len(done)} already-processed\n")
    print(f"=== b.ai Mass API Key Generator ===")
    print(f"Accounts: {len(accounts)}")
    print(f"Max keys/account: {MAX_KEYS_PER_ACCOUNT}\n")
    
    ctx = launch_context(
        headless=True, stealth_args=True, humanize=False,
        locale='en-US', timezone='America/Los_Angeles', args=ARGS
    )
    page = ctx.new_page()
    results, fail_streak = [], 0
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for i, email in enumerate(accounts):
        # Normal mode: recycle every 5 accounts or after 2 consecutive failures
        # AGGRESSIVE MODE: uncomment `if i > 0:` below and comment out the 5/2 check
        if i > 0 and (i % 5 == 0 or fail_streak >= 2):
            print(f"  🔄 Recycling browser (streak={fail_streak})")
            try: ctx.close()
            except: pass
            ctx = launch_context(
                headless=True, stealth_args=True, humanize=False,
                locale='en-US', timezone='America/Los_Angeles', args=ARGS
            )
            page = ctx.new_page()
            fail_streak = 0
        
        print(f"\n[{i+1}/{len(accounts)}] {email}")
        r = process_account(page, email)
        results.append(r)
        fail_streak = 0 if r["status"] == "success" else fail_streak + 1
        
        with open(f'bai_results_{ts}.json', 'w') as f:
            json.dump(results, f, indent=2)
    
    ok = sum(1 for r in results if r["status"] == "success")
    total_keys = sum(len(r["keys"]) for r in results)
    print(f"\n{'='*50}")
    print(f"  ✅ OK: {ok} | ❌ FAIL: {len(results)-ok}")
    print(f"  🔑 Total keys: {total_keys}")
    print(f"  📁 Saved: {OUTPUT_FILE}")
    print(f"{'='*50}")
    ctx.close()

if __name__ == '__main__':
    main()
