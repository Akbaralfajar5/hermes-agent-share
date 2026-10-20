# 50 Mobile Device Viewports for Anti-Fingerprinting (June 2026)

**Purpose:** Randomized mobile viewports per worker to prevent fingerprint-based detection. Each worker gets a different device profile — viewport, DPR, brand.

**User preference:** "random mobile hp nya yang banyak" (lots of random mobile phones). 50 devices across 8 brands.

```python
MOBILE_VIEWPORTS = [
    # === iPhones (15) ===
    {'name': 'iPhone SE 3',          'width': 375, 'height': 667,  'dpr': 2,    'brand': 'Apple'},
    {'name': 'iPhone 12',            'width': 390, 'height': 844,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 12 Mini',       'width': 360, 'height': 780,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 13',            'width': 390, 'height': 844,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 13 Pro',        'width': 390, 'height': 844,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 13 Pro Max',    'width': 428, 'height': 926,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 14',            'width': 390, 'height': 844,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 14 Plus',       'width': 428, 'height': 926,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 14 Pro',        'width': 393, 'height': 852,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 14 Pro Max',    'width': 430, 'height': 932,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 15',            'width': 393, 'height': 852,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 15 Pro',        'width': 393, 'height': 852,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 15 Pro Max',    'width': 430, 'height': 932,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 16',            'width': 393, 'height': 852,  'dpr': 3,    'brand': 'Apple'},
    {'name': 'iPhone 16 Pro Max',    'width': 430, 'height': 932,  'dpr': 3,    'brand': 'Apple'},
    # === Samsung (10) ===
    {'name': 'Samsung Galaxy S21',   'width': 360, 'height': 800,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy S22',   'width': 360, 'height': 780,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy S23',   'width': 360, 'height': 780,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy S24',   'width': 360, 'height': 780,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy S24+',  'width': 384, 'height': 854,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy S24 U', 'width': 412, 'height': 915,  'dpr': 3,    'brand': 'Samsung'},
    {'name': 'Samsung Galaxy A54',   'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Samsung'},
    {'name': 'Samsung Galaxy A34',   'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Samsung'},
    {'name': 'Samsung Galaxy A15',   'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Samsung'},
    {'name': 'Samsung Galaxy M54',   'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Samsung'},
    # === Xiaomi (12) ===
    {'name': 'Xiaomi Redmi Note 12', 'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Redmi Note 13', 'width': 412, 'height': 915,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Redmi 12',      'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi 13',            'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi 14',            'width': 412, 'height': 915,  'dpr': 3,    'brand': 'Xiaomi'},
    {'name': 'Xiaomi Poco F5',       'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Poco X6',       'width': 412, 'height': 915,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Poco M6',       'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Redmi Note 11', 'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Mi 11 Lite',    'width': 393, 'height': 873,  'dpr': 2.75, 'brand': 'Xiaomi'},
    {'name': 'Xiaomi Redmi 13C',     'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Xiaomi'},
    {'name': 'Xiaomi Redmi A3',      'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Xiaomi'},
    # === Oppo (6) ===
    {'name': 'Oppo Reno 8',          'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    {'name': 'Oppo Reno 10',         'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    {'name': 'Oppo Reno 11',         'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    {'name': 'Oppo A78',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    {'name': 'Oppo A58',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    {'name': 'Oppo Find N3 Flip',    'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Oppo'},
    # === Vivo (6) ===
    {'name': 'Vivo V27',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Vivo'},
    {'name': 'Vivo V29',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Vivo'},
    {'name': 'Vivo Y36',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Vivo'},
    {'name': 'Vivo Y27',             'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Vivo'},
    {'name': 'Vivo Y17s',            'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Vivo'},
    {'name': 'Vivo X100',            'width': 412, 'height': 915,  'dpr': 3,    'brand': 'Vivo'},
    # === Google (3) ===
    {'name': 'Google Pixel 7',       'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Google'},
    {'name': 'Google Pixel 8',       'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Google'},
    {'name': 'Google Pixel 8 Pro',   'width': 412, 'height': 915,  'dpr': 3,    'brand': 'Google'},
    # === Realme (3) ===
    {'name': 'Realme 11 Pro',        'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Realme'},
    {'name': 'Realme C55',           'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Realme'},
    {'name': 'Realme GT5',           'width': 412, 'height': 915,  'dpr': 3,    'brand': 'Realme'},
    # === Infinix (2) ===
    {'name': 'Infinix Hot 40',       'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Infinix'},
    {'name': 'Infinix Note 30',      'width': 412, 'height': 915,  'dpr': 2.625,'brand': 'Infinix'},
]

def pick_random_viewport():
    return random.choice(MOBILE_VIEWPORTS)
```

## Usage in Camoufox

```python
vp = pick_random_viewport()
cf_opts = {
    'window': (vp['width'] + 6, vp['height'] + 40),  # slightly larger than viewport
}
async with AsyncCamoufox(**cf_opts) as browser:
    page = await browser.new_page()
    await page.set_viewport_size({'width': vp['width'], 'height': vp['height']})
```

## Usage in Playwright Chromium

```python
vp = pick_random_viewport()
context = await browser.new_context(
    viewport={'width': vp['width'], 'height': vp['height']},
    device_scale_factor=vp['dpr'],
    is_mobile=True,
    has_touch=True,
)
```
