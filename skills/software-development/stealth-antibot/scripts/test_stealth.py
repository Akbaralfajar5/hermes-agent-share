#!/usr/bin/env python3
"""
Stealth test — launches Chromium with full stealth patches and tests against bot.sannysoft.com.

Usage:
    python3 test_stealth.py              # Full test with all 25 patches
    python3 test_stealth.py --basic      # Test with only 5 basic patches
    python3 test_stealth.py --standard   # Test with 12 standard patches
    python3 test_stealth.py --headless   # Run headless (default: headed for debugging)
"""

import asyncio
import sys
import os

# Stealth patches — paste your STEALTH_JS here or load from file
BASIC_STEALTH = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete Navigator.prototype.webdriver;
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
"""

CHROMIUM_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--no-first-run',
    '--no-default-browser-check',
    '--mute-audio',
    '--disable-webrtc-multiple-routes',
    '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-background-timer-throttling',
    '--disable-ipc-flooding-protection',
]


async def test_stealth(stealth_js: str, headless: bool = True):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=CHROMIUM_ARGS,
            ignore_default_args=['--enable-automation'],
        )

        context = await browser.new_context(
            viewport={'width': 414, 'height': 500},
            user_agent='Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            locale='id-ID',
            timezone_id='Asia/Jakarta',
            is_mobile=True,
            has_touch=True,
        )

        await context.add_init_script(stealth_js)
        page = await context.new_page()

        print("Loading bot.sannysoft.com...")
        await page.goto('https://bot.sannysoft.com/', wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)

        # Get results
        results = await page.evaluate("""() => {
            const rows = document.querySelectorAll('table tr');
            let data = [];
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    const test = cells[0]?.textContent?.trim() || '';
                    const value = cells[1]?.textContent?.trim() || '';
                    const color = cells[1] ? window.getComputedStyle(cells[1]).backgroundColor : '';
                    data.push({test, value, color});
                }
            });
            return data;
        }""")

        print("\n" + "=" * 70)
        print("🛡️ STEALTH TEST RESULTS")
        print("=" * 70)

        passed = 0
        failed = 0

        for r in results:
            if not r['test']:
                continue
            test_name = r['test'][:40]
            value = r['value'][:50]
            # Green background = passed
            is_green = '128' in r['color'] and '192' in r['color']
            is_ok = 'ok' in value.lower()

            if is_green or is_ok:
                icon = '✅'
                passed += 1
            else:
                icon = '❌'
                failed += 1

            print(f"{icon} {test_name:<40} {value}")

        print("=" * 70)
        print(f"📊 PASSED: {passed} | FAILED: {failed}")
        print("=" * 70)

        # Manual checks
        print("\n🔬 KEY PROPERTIES:")
        checks = {
            'navigator.webdriver': '() => navigator.webdriver',
            'navigator.plugins.length': '() => navigator.plugins.length',
            'navigator.platform': '() => navigator.platform',
            'navigator.hardwareConcurrency': '() => navigator.hardwareConcurrency',
            'navigator.deviceMemory': '() => navigator.deviceMemory',
            'navigator.vendor': '() => navigator.vendor',
            'navigator.maxTouchPoints': '() => navigator.maxTouchPoints',
            'screen.width': '() => screen.width',
            'screen.height': '() => screen.height',
            'speechSynthesis.getVoices().length': '() => speechSynthesis.getVoices().length',
        }
        for name, js in checks.items():
            try:
                val = await page.evaluate(js)
                status = '✅' if val not in (None, True, 0, 'undefined') else '⚠️'
                if name == 'navigator.webdriver' and val is None:
                    status = '✅'
                print(f"  {status} {name:<35} = {val}")
            except Exception as e:
                print(f"  ❌ {name:<35} = ERROR: {str(e)[:40]}")

        await browser.close()
        return passed, failed


def main():
    headless = '--headless' in sys.argv
    level = 'full'

    if '--basic' in sys.argv:
        level = 'basic'
        stealth_js = BASIC_STEALTH
        print("Testing: BASIC stealth (5 patches)")
    elif '--standard' in sys.argv:
        level = 'standard'
        # Load standard from SKILL.md or use basic for now
        stealth_js = BASIC_STEALTH
        print("Testing: STANDARD stealth (12 patches)")
        print("⚠️  Paste STANDARD_STEALTH from skill for accurate test")
    else:
        level = 'full'
        # Try to load from deposit.py
        deposit_path = os.path.expanduser('~/deposit_project/deposit.py')
        if os.path.exists(deposit_path):
            import re
            with open(deposit_path) as f:
                content = f.read()
            match = re.search(r'STEALTH_JS = """(.*?)"""', content, re.DOTALL)
            if match:
                stealth_js = match.group(1)
                print(f"Testing: FULL stealth (loaded from {deposit_path})")
            else:
                stealth_js = BASIC_STEALTH
                print("Testing: BASIC stealth (could not extract STEALTH_JS)")
        else:
            stealth_js = BASIC_STEALTH
            print("Testing: BASIC stealth (deposit.py not found)")

    passed, failed = asyncio.run(test_stealth(stealth_js, headless))

    if failed == 0:
        print("\n✅ ALL TESTS PASSED — stealth config is working!")
    else:
        print(f"\n⚠️  {failed} test(s) failed — check output above")


if __name__ == '__main__':
    main()
