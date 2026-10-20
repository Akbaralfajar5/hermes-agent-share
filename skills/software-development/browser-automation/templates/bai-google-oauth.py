#!/usr/bin/env python3
"""
b.ai Automation - CloakBrowser + qsuitee.id + 2Captcha
Login -> Check API keys -> Create if none -> Copy key -> Sign out -> Next
"""
import sys, time, json, re, random, os, requests
from datetime import datetime
from cloakbrowser import launch_context

# ─── CONFIG ───────────────────────────────────────────────────────
TWOCAPTCHA_KEY = os.environ.get("TWOCAPTCHA_KEY", "YOUR_2CAPTCHA_KEY_HERE")
GMAIL_PASS = "yourpassword"
ARGS = [
    "--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
    "--disable-software-rasterizer","--disable-extensions","--disable-component-update"
]

ACCOUNTS = [
    "youremail@here",
]

# ─── HELPERS ──────────────────────────────────────────────────────
def rand_name():
    a=["nova","swift","zen","flux","apex","echo","vibe","core","peak","orbit"]
    n=["dev","hub","net","api","key","sync","flow","link","core","base"]
    return f"{random.choice(a)}-{random.choice(n)}-{random.randint(100,999)}"

def extract_key(text):
    """Extract clean sk-XXXXX key, strip trailing button text"""
    m = re.search(r'(sk-[a-zA-Z0-9]{20,60})', text)
    if m:
        return m.group(1)
    m = re.search(r'(sk-[a-zA-Z0-9]{20,60})[A-Z]', text)
    if m:
        return m.group(1)
    return None

def solve_turnstile(sitekey, page_url):
    """Solve Cloudflare Turnstile via 2Captcha"""
    print("    Solving Turnstile via 2Captcha...")
    try:
        r = requests.post("http://2captcha.com/in.php", data={
            "key": TWOCAPTCHA_KEY,
            "method": "turnstile",
            "sitekey": sitekey,
            "pageurl": page_url,
            "json": 1
        }, timeout=30)
        task_id = r.json().get("request")
        if not task_id or task_id == "ERROR":
            print(f"    2Captcha error: {r.text}")
            return None
        print(f"    Task ID: {task_id}, waiting...")
        for _ in range(60):
            time.sleep(5)
            r = requests.get("http://2captcha.com/res.php", params={
                "key": TWOCAPTCHA_KEY, "action": "get", "id": task_id, "json": 1
            }, timeout=30)
            res = r.json()
            if res.get("status") == 1:
                print("    Turnstile solved!")
                return res.get("request")
            if res.get("request") != "CAPCHA_NOT_READY":
                print(f"    2Captcha fail: {res}")
                return None
        print("    2Captcha timeout")
        return None
    except Exception as e:
        print(f"    2Captcha error: {e}")
        return None

def solve_hcaptcha(sitekey, page_url):
    """Solve hCaptcha via 2Captcha"""
    print("    Solving hCaptcha via 2Captcha...")
    try:
        r = requests.post("http://2captcha.com/in.php", data={
            "key": TWOCAPTCHA_KEY,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": page_url,
            "json": 1
        }, timeout=30)
        task_id = r.json().get("request")
        if not task_id or task_id == "ERROR":
            print(f"    2Captcha error: {r.text}")
            return None
        print(f"    Task ID: {task_id}, waiting...")
        for _ in range(60):
            time.sleep(5)
            r = requests.get("http://2captcha.com/res.php", params={
                "key": TWOCAPTCHA_KEY, "action": "get", "id": task_id, "json": 1
            }, timeout=30)
            res = r.json()
            if res.get("status") == 1:
                print("    hCaptcha solved!")
                return res.get("request")
            if res.get("request") != "CAPCHA_NOT_READY":
                print(f"    2Captcha fail: {res}")
                return None
        print("    2Captcha timeout")
        return None
    except Exception as e:
        print(f"    2Captcha error: {e}")
        return None

def handle_captcha(page):
    """Detect and solve any CAPTCHA on the page"""
    body = page.inner_text("body")

    # Turnstile
    turnstile = page.evaluate('''() => {
        const el = document.querySelector('[data-sitekey]');
        if (el) return el.getAttribute('data-sitekey');
        const scripts = document.querySelectorAll('script[src*="turnstile"]');
        if (scripts.length) {
            const meta = document.querySelector('meta[name="cf-turnstile-site-key"]');
            if (meta) return meta.content;
        }
        return null;
    }''')
    if turnstile:
        token = solve_turnstile(turnstile, page.url)
        if token:
            page.evaluate('''(token) => {
                document.querySelectorAll('[name="cf-turnstile-response"],[name="g-recaptcha-response"]').forEach(el=>{el.value=token});
                const hidden=document.querySelector('input[name="cf-turnstile-response"]');
                if(hidden){hidden.dispatchEvent(new Event('change',{bubbles:true}))}
            }''', token)
            time.sleep(3)
            return True

    # hCaptcha
    hcaptcha_sitekey = page.evaluate('''() => {
        const el = document.querySelector('[data-hcaptcha-sitekey]');
        if (el) return el.getAttribute('data-hcaptcha-sitekey');
        return null;
    }''')
    if hcaptcha_sitekey:
        token = solve_hcaptcha(hcaptcha_sitekey, page.url)
        if token:
            page.evaluate('''(token) => {
                document.querySelectorAll('textarea[name="h-captcha-response"]').forEach(el=>{el.value=token});
            }''', token)
            time.sleep(3)
            return True

    return False

def close_modals(page):
    for _ in range(5):
        c=page.evaluate('''()=>{let c=false;
            document.querySelectorAll('.ant-modal-close,[aria-label="Close"]').forEach(b=>{if(b.offsetParent!==null){b.click();c=true}});
            document.querySelectorAll('button').forEach(b=>{const t=b.textContent.trim();if((t==='Cancel'||t==='Close')&&b.offsetParent!==null){b.click();c=true}});
            return c}''')
        if not c: break
        time.sleep(2)
    time.sleep(2)

def sign_out(page):
    """Sign out and wait for login page"""
    close_modals(page)
    time.sleep(2)

    # Click avatar
    page.evaluate('''()=>{const a=document.querySelector('.ant-avatar');if(a)a.click()}''')
    time.sleep(3)

    # Click Log out
    page.evaluate('''()=>{document.querySelectorAll('*').forEach(el=>{if(el.children.length===0&&el.textContent.trim()==='Log out')el.click()})}''')
    time.sleep(5)

    # If modal "Sign out" button appears
    try:
        page.evaluate('''()=>{document.querySelectorAll('button,a,[role="button"]').forEach(b=>{if(b.textContent.trim().toLowerCase().includes('sign out')&&b.offsetParent!==null)b.click()})}''')
        time.sleep(3)
    except: pass

    # Navigate fresh to chat page
    page.goto('https://chat.b.ai/chat', timeout=30000, wait_until='networkidle')
    time.sleep(5)

    # Wait until "Log in" button appears (max 20s)
    for _ in range(10):
        try:
            body = page.inner_text('body')
            if 'Log in' in body:
                return True
        except: pass
        time.sleep(2)

    # Last resort: hard reload
    page.reload(wait_until='networkidle')
    time.sleep(5)
    return True

def check_existing_keys(page):
    return page.evaluate('''() => {
        const keys=[];
        document.querySelectorAll('*').forEach(el=>{
            const t=el.textContent.trim();
            if(el.children.length===0 && /^sk-[a-zA-Z0-9_*\\.\\\\-]{5,60}$/.test(t)){
                if(!keys.includes(t)) keys.push(t);
            }
        });
        return keys;
    }''')

def google_oauth(page, email):
    """Full Google OAuth flow including Workspace onboarding + 2Captcha"""
    # Navigate fresh
    page.goto('https://chat.b.ai/chat', timeout=60000, wait_until='networkidle')
    time.sleep(5)

    # Wait for "Log in" button
    login_btn = page.locator('button:has-text("Log in")')
    login_btn.wait_for(state='attached', timeout=15000)
    login_btn.click()
    time.sleep(5)

    # Check for captcha before OAuth
    handle_captcha(page)

    # Open Google popup
    with page.expect_popup(timeout=30000) as pi:
        page.click('text=Continue with Google')
    gp = pi.value
    gp.wait_for_load_state('networkidle', timeout=30000)
    time.sleep(3)

    # Email
    ei = gp.locator('input[type="email"]')
    ei.wait_for(state='visible', timeout=15000)
    ei.fill(email)
    gp.locator('#identifierNext').click()
    time.sleep(6)

    # Check "Couldn't find"
    try:
        txt = gp.inner_text('body')
        if "Couldn't find" in txt:
            gp.close(); time.sleep(2)
            return "no_google_account"
    except: pass

    # Password
    try:
        pw = gp.locator('input[name="Passwd"]')
        pw.wait_for(state='visible', timeout=15000)
        pw.fill(GMAIL_PASS)
        gp.locator('#passwordNext').click()
        time.sleep(10)
    except:
        return "password_error"

    # Handle Google pages: Workspace onboarding → OAuth consent → redirect
    popup_alive = True
    for attempt in range(20):
        if not popup_alive:
            break
        try:
            url = gp.url
        except:
            popup_alive = False
            break

        if url.startswith('https://chat.b.ai'):
            break

        # Check for captcha in popup
        try:
            handle_captcha(gp)
        except: pass

        # Click #confirm (I understand) for Workspace onboarding
        try:
            confirm = gp.locator('#confirm')
            if confirm.count() and confirm.is_visible():
                confirm.click()
                time.sleep(8)
                continue
        except: pass

        # Click consent buttons
        clicked = False
        for sel in ['button:has-text("Continue")', 'button:has-text("Allow")',
                    'button:has-text("Accept")', 'button:has-text("I agree")',
                    'button:has-text("Skip")', '#submit_approve_access',
                    'input[type="submit"]']:
            try:
                btn = gp.locator(sel).first
                if btn.count() and btn.is_visible():
                    btn.click()
                    clicked = True
                    time.sleep(8)
                    break
            except: pass

        if not clicked:
            time.sleep(3)

    # Close popup if still alive
    if popup_alive:
        try: gp.close()
        except: pass

    time.sleep(3)

    # Reload main page to pick up auth
    page.reload(wait_until='networkidle')
    time.sleep(8)

    body = page.inner_text('body')
    if 'AO_' in body:
        return "ok"
    return "login_failed"

def process(page, email):
    r = {"email": email, "status": "error", "api_key": None, "time": datetime.now().isoformat()}
    try:
        auth = google_oauth(page, email)
        if auth != "ok":
            r["status"] = auth
            print(f"    Auth failed: {auth}")
            return r
        print("    Logged in")

        # Check captcha on b.ai
        handle_captcha(page)

        # Go to API page
        page.evaluate('''()=>{document.querySelectorAll('span,a,button').forEach(e=>{if(e.textContent.trim()==='API')e.click()})}''')
        time.sleep(8)
        close_modals(page)

        # Check captcha on API page
        handle_captcha(page)

        # Check existing keys
        keys = check_existing_keys(page)
        print(f"    Existing keys: {len(keys)}")
        if keys:
            r["status"] = "already_done"
            r["existing_keys"] = keys
            print("    SKIP")
            sign_out(page)
            return r

        # Inject clipboard hook
        page.evaluate('''() => {
            window.__copied_key = null;
            const orig = navigator.clipboard.writeText;
            navigator.clipboard.writeText = function(text) {
                window.__copied_key = text;
                return orig.call(this, text);
            };
        }''')

        # Create key
        print("    Creating key...")
        page.evaluate('''()=>{document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim().includes('Create API')&&b.offsetParent!==null)b.click()})}''')
        time.sleep(5)

        key_name = rand_name()
        page.evaluate('''(name)=>{
            document.querySelectorAll('input[type="text"]').forEach(i=>{
                if(i.offsetParent!==null&&i.placeholder&&i.placeholder.includes('API')){
                    const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                    s.call(i,name);
                    i.dispatchEvent(new Event('input',{bubbles:true}));
                    i.dispatchEvent(new Event('change',{bubbles:true}));
                }
            });
        }''', key_name)
        time.sleep(2)

        page.evaluate('''()=>{
            document.querySelectorAll('button').forEach(b=>{
                const t=b.textContent.trim().toLowerCase();
                if((t==='create'||t==='submit'||t==='save')&&b.offsetParent!==null)b.click();
            });
            document.querySelectorAll('.ant-btn-primary').forEach(b=>{if(b.offsetParent!==null)b.click()});
        }''')
        time.sleep(8)

        # Check captcha after create
        handle_captcha(page)

        # Try clipboard first (click Copy button)
        page.evaluate('''()=>{
            document.querySelectorAll('button').forEach(b=>{
                const t=b.textContent.trim();
                if(t==='Copy'&&b.offsetParent!==null) b.click();
            });
        }''')
        time.sleep(2)

        api_key = page.evaluate('()=>window.__copied_key')

        # Fallback: extract from modal text (strip "CancelCopy" suffix)
        if not api_key or not api_key.startswith('sk-'):
            modal_text = page.evaluate('''()=>{
                const modals=document.querySelectorAll('.ant-modal-wrap');
                for(const m of modals){
                    const s=getComputedStyle(m);
                    if(s.display==='none'||s.visibility==='hidden')continue;
                    if(m.textContent.includes('Log in'))continue;
                    return m.textContent;
                }
                return '';
            }''')
            api_key = extract_key(modal_text)

        if api_key and api_key.startswith('sk-'):
            r["api_key"] = api_key
            r["status"] = "success"
            r["key_name"] = key_name
            with open('b.ai_api_keys.txt', 'a') as f:
                f.write(f'{email} | {api_key} | {key_name}\n')
            print(f"    API Key: {api_key}")
        else:
            r["status"] = "key_not_found"
            print("    Key not found")

        # Sign out
        sign_out(page)
        print("    Signed out")

    except Exception as e:
        r["status"] = f"error:{str(e)[:100]}"
        print(f"    Error: {e}")
    return r

# ─── MAIN ─────────────────────────────────────────────────────────
def main():
    print(f"=== b.ai Automation (CloakBrowser + 2Captcha) ===")
    print(f"Accounts: {len(ACCOUNTS)}\n")

    results = []
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    ctx = launch_context(
        headless=True, stealth_args=True, humanize=True,
        locale='en-US', timezone='America/Los_Angeles', args=ARGS
    )
    page = ctx.new_page()

    for i, email in enumerate(ACCOUNTS):
        print(f"[{i+1}/{len(ACCOUNTS)}] {email}")
        r = process(page, email)
        results.append(r)

        # Save after each account
        with open(f'b.ai_results_{ts}.json', 'w') as f:
            json.dump(results, f, indent=2)
        try:
            with open('b.ai_api_keys.txt', 'r') as f:
                print(f"    [Total keys saved: {len(f.readlines())}]")
        except: pass

        if i < len(ACCOUNTS) - 1:
            time.sleep(5)

    # Summary
    ok = sum(1 for r in results if r["status"] == "success")
    skip = sum(1 for r in results if r["status"] == "already_done")
    fail = sum(1 for r in results if r["status"] not in ("success", "already_done"))

    print(f"\n{'='*60}")
    print(f"  OK: {ok} | SKIP: {skip} | FAIL: {fail} | TOTAL: {len(results)}")
    print(f"{'='*60}")
    for r in results:
        s = {"success": "✅", "already_done": "⏭️"}.get(r["status"], "❌")
        k = r.get("api_key") or ""
        print(f"  {s} {r['email']}  {k}")

    with open(f'b.ai_results_{ts}.json', 'w') as f:
        json.dump(results, f, indent=2)
    with open(f'b.ai_results_{ts}.csv', 'w') as f:
        f.write("email,status,api_key,timestamp\n")
        for r in results:
            f.write(f"{r['email']},{r['status']},{r.get('api_key','')},{r['time']}\n")
    print(f"\nSaved: b.ai_results_{ts}.json/.csv")

    ctx.close()

if __name__ == '__main__':
    main()
