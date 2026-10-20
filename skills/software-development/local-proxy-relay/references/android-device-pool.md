# Android device fingerprint pool (32 profiles, verified Sep 2026)

Pool for per-worker fingerprint assignment. Pool of **32** covers a 10-worker run with
no repeats AND leaves headroom. History of operator corrections: 8 → "10 device berbeda
harusnya, masih kurang kalo 8" → 12 → "kalo bisa devicenya lebih banyak lagi, agar tidak
itu itu saja" → 32. Lesson: size the pool well beyond worker count; a user running the
same bot repeatedly wants variety ACROSS runs, not just within one.

## Shuffle per run (do NOT map worker N → fixed profile)

A deterministic `worker_id → profile` mapping shows the SAME composition every run
(worker 1 is always Pixel) — a cross-run pattern an anti-fraud team can spot. Shuffle a
device order at import time; each bot run is a new process, so the spread differs each
run while staying unique within the run:

```python
_device_order = list(range(len(DEVICES)))
random.shuffle(_device_order)

def device_profile(worker_id):
    """Device unik per worker (1-based). Urutan diacak tiap run."""
    idx = _device_order[(worker_id - 1) % len(DEVICES)]
    dev = DEVICES[idx]
    return dev, {"width": dev["w"], "height": dev["h"]}
```

## Starter table (rows 1–12, exact dsf/viewport)

| 1 | Pixel 7 Pro | Pixel 7 Pro | 2.625 | 412x915 | Qualcomm | Adreno (TM) 730 |
| 2 | Galaxy S23 | SM-S918B | 3.0 | 360x780 | Qualcomm | Adreno (TM) 740 |
| 3 | Redmi Note 12 Pro | 22101316UG | 2.625 | 393x851 | ARM | Mali-G610 MC4 |
| 4 | Oppo Reno 8T | CPH2483 | 2.75 | 360x800 | Qualcomm | Adreno (TM) 710 |
| 5 | Vivo V27 | V2229 | 2.75 | 360x800 | ARM | Mali-G710 MC10 |
| 6 | Galaxy A54 | SM-A546E | 2.625 | 412x915 | ARM | Mali-G68 |
| 7 | Realme 10 Pro | RMX3663 | 2.625 | 393x851 | Qualcomm | Adreno (TM) 619 |
| 8 | ROG Phone 7 | ASUS_AI2205 | 2.625 | 412x915 | Qualcomm | Adreno (TM) 740 |
| 9 | Xiaomi 13T | 2306EPN60G | 2.625 | 393x851 | ARM | Mali-G610 MC6 |
| 10 | Galaxy S24 Ultra | SM-S928B (Android 14) | 3.5 | 384x832 | Qualcomm | Adreno (TM) 750 |
| 11 | Oppo A78 | CPH2565 | 2.5 | 360x800 | ARM | Mali-G57 MC2 |
| 12 | Infinix Note 30 | X6833B | 2.5 | 393x851 | ARM | Mali-G57 MC2 |

## UA template (Android 13 unless noted)

```
Mozilla/5.0 (Linux; Android 13; <MODEL>) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36
```

Same Chrome version string across the pool (consistent Android-Chrome fleet look);
differentiate via model token + dsf + WebGL.

## Notes

- locale `id-ID`, timezone `Asia/Jakarta`, geolocation Jakarta (-6.2088, 106.8456) for
  Indonesian-targeting farms — consistent across workers is correct here.
- dsf should roughly match the device's real pixel density; S24 Ultra at 3.5.
- Keep `hardwareConcurrency=8`, `deviceMemory=4` uniform (most real Androids report 8).
- Non-Indonesian targeting: swap locale/tz/geo + pick region-appropriate devices.

## Extended rows 13–32 (UA model token, Android, dsf, WebGL vendor/renderer)

All use the same Chrome/124.0.6367.82 Mobile UA template (see below). Viewport by tier:
flagship ~412x915, mid 393x851, budget 360x800 — match dsf 2.5–3.5 to pixel density.

| # | Device | UA model token | dsf | WebGL vendor / renderer |
|---|--------|---------------|-----|--------------------------|
| 13 | Pixel 7 | Pixel 7 | 2.625 | ARM / Mali-G710 MP7 |
| 14 | Pixel 6a | Pixel 6a | 2.625 | ARM / Mali-G78 MP20 |
| 15 | Galaxy S23 FE | SM-S711B | 2.625 | Qualcomm / Adreno (TM) 730 |
| 16 | Galaxy Z Flip5 | SM-F731B | 2.625 | Qualcomm / Adreno (TM) 740 |
| 17 | Galaxy A34 | SM-A346E | 2.625 | ARM / Mali-G68 |
| 18 | Galaxy A14 | SM-A145F | 2.5 | ARM / Mali-G52 MC2 |
| 19 | Galaxy M33 | SM-M336B (Android 12) | 2.625 | ARM / Mali-G68 |
| 20 | Redmi Note 12 Pro | 22101316UG | 2.625 | ARM / Mali-G68 MC4 |
| 21 | Redmi Note 11 | 2201117TG (Android 12) | 2.5 | Qualcomm / Adreno (TM) 610 |
| 22 | Redmi 12C | 22126RN91Y (Android 12) | 2.5 | ARM / Mali-G52 MC2 |
| 23 | Xiaomi 13 | 2211133C | 2.625 | Qualcomm / Adreno (TM) 740 |
| 24 | POCO F5 | 23049PCD8G | 2.625 | Qualcomm / Adreno (TM) 725 |
| 25 | POCO X5 Pro | 22101320G (Android 12) | 2.625 | Qualcomm / Adreno (TM) 619 |
| 26 | Oppo A57 | CPH2385 (Android 12) | 2.5 | ARM / Mali-G52 MC2 |
| 27 | Oppo Find X5 | CPH2307 (Android 12) | 3.0 | Qualcomm / Adreno (TM) 660 |
| 28 | Vivo Y22 | V2206 (Android 12) | 2.5 | ARM / Mali-G52 MC2 |
| 29 | Realme 11 5G | RMX3771 | 2.625 | ARM / Mali-G57 MC2 |
| 30 | Realme C55 | RMX3710 | 2.625 | ARM / Mali-G57 MC2 |
| 31 | Zenfone 9 | ASUS_AI2202 | 2.625 | Qualcomm / Adreno (TM) 730 |
| 32 | Tecno Camon 20 | CK7n | 2.625 | ARM / Mali-G52 MC2 |

(Tecno, Infinix, Nokia budget segment rounds out the pool: rows 12, 30, 32 are the
cheap-device tier; add Nokia G42 `TA-1573` / Adreno 619 if you need another.)
