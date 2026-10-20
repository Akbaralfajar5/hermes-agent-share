# Ponyin Trading Intel — Full Knowledge Bank

Source: https://www.ponyin.id/ (scraped directly May 2026, line-by-line)
Author: @ELPonyin on X/Twitter
Language: Indonesian

---

## VOL. 1 — BUNDLE BASICS (9 Lessons)

### 1. Bundle Token — Monopoli yang Tak Terlihat
- Dev beli supply via banyak wallet berbeda di milidetik pertama launch (bundling)
- Dari luar terlihat organik — padahal satu tangan yang menggerakkan
- **Bahaya:** Dev pegang mayoritas supply sejak detik pertama → bisa dump kapanpun
- Patokan "holder di bawah 3%" sudah TIDAK AKURAT di era multi-wallet
  - 1 orang bisa punya 5–20 wallet berbeda, tiap wallet 2% = total 20–40%
  - Token narasi besar: holder 7–10% per wallet sudah wajar, bukan red flag
- Pasar new pair = PvP (Player vs Player) — semua bermain untuk diri sendiri
- **Charon mapping:** `trending_max_bundler_rate` filter + LLM red flag detection

### 2. Global Fees — Detektor Transaksi Palsu
- Setiap transaksi token di Solana kena fee ~0.25% → masuk ke pool LP
- **Formula deteksi:** Volume tinggi + fee sangat kecil = WASH TRADING
- Tiga tipe volume:
  - ✅ Organik: fee sebanding volume, banyak wallet berbeda
  - ⚠️ Wash Trading: volume tinggi, fee kecil, wallet sama saling jual-beli
  - 🚨 Bot Pump: volume meledak dalam detik, fee tidak sebanding (detik pertama launch)
- Cara cek: Trojan → fees paid, atau Birdeye/Solscan → Total Fee vs Total Volume
- **Charon mapping:** `min_gmgn_total_fee_sol` filter (GMGN total_fee field)

### 3. Revoke & Minting — Jebakan yang Kelihatan Aman
- **Revoke Authority (sudah dicabut):** Dev tidak bisa bekukan akun pemegang ✅
  - TAPI: TIDAK mencegah dev dump supply yang sudah mereka pegang
- **Mint Authority (masih aktif):** Dev bisa cetak token baru kapan saja 🚨
  - Supply bisa membengkak → nilai token terdilusi
- **Pola jebakan:** Bundle supply → Revoke authority (terlihat legit) → Tunggu naik → Dump
- Tools: RugCheck.xyz, Token Sniffer, Solscan → Token Extensions → Mint/Freeze Authority
- **Charon mapping:** LLM prompt red flags; tidak ada filter langsung (data tidak tersedia dari GMGN/Jupiter)

### 4. Meme vs Utility — Pilih Sesuai Style Kamu
- Meme coin: digerakkan narasi viral, window profit sempit (menit), high risk/reward
  - Wajib cek: siapa deployer-nya, ada cabal di belakang?
- Utility token: punya produk nyata, window profit lebih panjang (minggu–bulan)
  - Wajib cek: produknya benar-benar exist dan dipakai?
- Rekomendasi Ponyin untuk pemula: mulai dari meme coin dulu (belajar lebih cepat)
- **Charon mapping:** Charon fokus meme coin (Pump.fun) — sesuai rekomendasi ini

### 5. Dex Paid, Ads & Boost — Sinyal atau Sekadar Bayar?
- Ketiganya adalah alat marketing yang bisa dibeli siapapun — termasuk scammer
- **Kunci: KAPAN dipasang**
  - Dex Paid di awal launch = sinyal positif (dev serius)
  - Ads + Boost setelah harga puncak = EXIT LIQUIDITY trap
- Pola berbahaya: Boost + Ads muncul mendadak setelah pump besar = distribusi
- **Charon mapping:** Tidak ada filter langsung; LLM bisa mendeteksi via twitterNarrative

### 6. 3 Konfirmasi Candle — Cara Nyari Dip yang Valid
- Metode masuk bertahap untuk hindari FOMO di dip:
  1. **Dip Pertama** → JANGAN MASUK (hampir selalu ada dip lagi di bawahnya)
  2. **Bounce** → Masuk 10% saja ("mark position")
  3. **Dip Kedua (Konfirmasi)** → Entry penuh (support terbentuk)
- Kalau dip kedua bablas jauh → mundur sepenuhnya (rugi hanya 10% dari rencana)
- Menggeser probabilitas rugi besar dari 90% → ~50/50
- **Charon mapping:** `max_ath_distance_pct` filter (dip_buy strategy); trailing stop untuk exit

### 7. Cabal Play — Ketika Pasar Bergerak Terkoordinasi
- Cabal = kelompok tertutup yang merencanakan launch token secara terkoordinasi
- Tiga tipe:
  - 👥 Cabal Kelompok: Marcel, Lexapro, Cooker, Wynn (Solana ecosystem)
  - 👤 Solo Cabal: Duvel (modal besar, kontrol penuh)
  - ⚔️ Konflik Cabal: dua cabal bertabrakan → volume meledak = peluang
- Case study: $yaranaika — Duvel pump sendirian setelah di-vamp
- Cara manfaatkan: pelajari range push mereka, monitor konflik, track wallet (bukan FOMO ke token)
- Tools: Helius Orb, Solscan, DexScreener, Bun_Scan, Terminal
- RSI/MACD/Bollinger Bands TIDAK BERGUNA di cabal play — yang berlaku: informasi + kecepatan
- **Charon mapping:** `savedWalletExposure` (saved wallets = cabal wallet tracking); `min_saved_wallet_holders`

### 8. Membaca Holder — Yang Terlihat dan Yang Sebenarnya
- "Holder di bawah 5% = distribusi sehat" → NAIF di era multi-wallet
- 1 orang bisa kendalikan 10 wallet berbeda (10 × 2% = 20% total, tidak terlihat)
- Pasar new pair: Cupsey, Cented, Log, Decu beli agresif di detik pertama
- Untuk token narasi besar: holder 7–10% per wallet = wajar, bukan red flag
- Zero-sum mentality: semua orang bermain untuk diri sendiri
- **Charon mapping:** `max_top20_holder_percent` filter; LLM holder analysis

### 9. Market Cap Tier — Beda Level, Beda Lawan, Beda Strategi
| Tier | Range | Pemain | Strategi |
|------|-------|--------|----------|
| New Pair | <$100K | Bot sniper, cabal, whale awal | Narasi, entry cepat, exit lebih cepat |
| Micro Cap | $100K–$5M | Scalper, bot, komunitas kecil | Baca chart, cari reversal, scalp |
| Mid Cap | $5M–$50M | Dolphin, whale, media masuk | Main size besar, entry presisi |
| High Cap | $50M–$200M | Whale besar, CNN, brand | DCA tipis, media goreng = sinyal KELUAR |
| CEX | >$200M | Wintermute, hedge fund, market maker | Posisi kecil, OTC bukan retail |

- Kesalahan umum: pakai strategi yang sama di semua level
- **Charon mapping:** `min_mcap_usd` / `max_mcap_usd` per strategy (sniper: $7K–$200K)

---

## VOL. 2 — ADVANCE (A1–A10 + Bonus)

### A1. Cara Snipe Early Project
- Snipe = beli koin di detik-detik pertama sebelum orang lain sadar
- Butuh 3 hal: informasi (siapa deploy, kapan), alat (bot sniper), kecepatan (milidetik)
- Tahapan: Mapping → Equipment → Snipe → Profit
- Case study Naseem ($trump): masuk 0.05 detik sebelum liquidity add, gas $100K, modal $1M → profit $302M
- Tools (dari paling canggih): Mintech → Flux → Maestro → Trojan → Custom Helius Code
- **Charon mapping:** Charon adalah automated sniper via fee-claim signals (pre-graduation detection)

### A2. Cara Dapat $1000 dari $100
- **Jalur Koneksi ("Mulut Manis"):** Bangun relasi ke cabal/dev → diajak masuk bareng
  - Punya dompet resmi (diketahui cabal) + dompet pribadi (tidak diketahui)
  - Saat jual: gunakan trailing stop, jaga chart tetap sehat
- **Jalur Deployer ("Si Pembuat"):** Buat koin sendiri, kontrol penuh
- Cara jual yang baik: jangan jual saat merah, jangan saat naik cepat → gunakan trailing stop
- **Charon mapping:** Trailing stop = `trailing_enabled: true`, `trailing_percent` setting

### A3. Wallet Ping — 10 Mata Lebih Baik dari 2
- Wallet ping = notifikasi setiap kali wallet yang dipantau bertransaksi
- BUKAN sinyal langsung entry — tetap harus analisis sendiri
- Cara temukan wallet bagus: cek "Top Trader" di koin yang naik, lacak dari 1 wallet ke wallet lain
- Manfaat: risiko rug pull turun dari 90% → 60% → 50%
- **Charon mapping:** `savedWalletExposure` + `/walletadd` command = implementasi wallet ping

### A4. Berapa Modal yang Tepat untuk Trade?
- Jangan trading dengan "uang panas" (hutang, kebutuhan pokok)
- **Strategi Compounding 35% TP:**
  - Setiap profit → ambil 35% → pindah ke dompet baru (tabungan)
  - Saat ada peluang bagus → masuk 70–80% dari total simpanan
  - Target: 50% profit per trade (bukan 10x)
- Simulasi: 0.5 SOL → 5 SOL dalam 5 trade konsisten (50% profit, 80% size)
- Auto Take Profit = senjata melawan keserakahan
- Tanda keserakahan: "sayang kalau jual sekarang", beli lagi koin yang sudah dijual
- **Charon mapping:** `tp_percent` (default 50%), `position_size_sol` (80% of available)

### A5. Transaksi Murah, Speed Tetap Kencang
- Platform fee (Trojan, Flux, Axiom) ~1% per transaksi
- Contoh: 10 trade/hari × 0.5 SOL × 1% = 0.5 SOL/hari = 15 SOL/bulan = 180 SOL/tahun
- Solusi: RUST (tulis kode transaksi langsung ke blockchain, fee = 0) atau RPC langsung (Helius, QuikNode, Triton)
- Mulai belajar setelah simpanan stabil >5 SOL
- **Charon mapping:** Charon pakai Jupiter Ultra (zero platform fee) + direct Helius RPC

### A6. Rent Refund — Tarik Kembali Uang Sewa
- Setiap token account di Solana butuh rent deposit (~0.002 SOL)
- Setelah token dijual, akun kosong tetap ada → rent tidak otomatis kembali
- 50 koin × 0.002 SOL = 0.1 SOL terkunci
- Platform: Refundyoursol.com (bisa nalangin gas kalau SOL nol)
- Hanya berlaku untuk new pair (bukan koin yang sama dibeli berulang)
- **Charon mapping:** Tidak langsung relevan ke bot logic

### A7. Instant Scalping — 4 Filter New Pair
- 4 filter sebelum scalp new pair fresh launch:
  1. **Global Gas Fee** — kalau tinggi, execution lebih lambat dari bot lain → skip
  2. **Holder & Funded Wallet Age** — funded wallet under 1 day = manipulasi 🚨
  3. **Balance Top Holder** — saldo under 0.2 SOL = bukan player besar → skip
  4. **Entry Market Cap** — sudah pump di bawah 3K MC saat deploy = insider sudah keluar → skip
- Rumus: 2+ flag → SKIP; 1 flag → GAS IT (60–70% win rate)
- **Charon mapping:**
  - Filter 1: tidak langsung (gas fee tidak dimonitor Charon)
  - Filter 2: `trending_max_bundler_rate` (bundler = funded wallet baru)
  - Filter 3: `max_top20_holder_percent` (holder balance check via Jupiter)
  - Filter 4: `min_mcap_usd` / `max_mcap_usd` (entry market cap gate)

### ✦ Day Phase Trade — Short Swing 3–7 Hari (Bonus Strat)
- Bukan scalp, bukan hold — main di fase cooldown → sideway
- Fase hidup token: Hype Awal → Parabolic → **Cooldown/Sideway** ← zona ini → Revival/Death
- Kriteria token layak:
  1. FDV di atas $1M (skip micro cap)
  2. Dip 50–70% dari ATH (sweet spot; <40% masih distribution, >80% sudah mati)
  3. Chart sideway minimal 3–5 hari (sellers kehabisan tenaga)
  4. Meme/narrative masih relevan (cek Twitter/X, TG, Discord)
  5. Holder count stabil atau naik tipis (turun cepet = distribution terselubung)
- Eksekusi: beli weekend (volume tipis = harga lebih bagus), jual weekday (Selasa–Kamis)
- Target: 40–70% profit dari average entry
- Size: DCA ke 2–3 wallet berbeda (average entry lebih rata, exit bertahap)
- Jebakan: jangan DCA ke koin holder turun drastis, jangan hold >7 hari kalau tidak bergerak
- **Charon mapping:** `max_ath_distance_pct` (dip_buy strategy); `partial_tp` untuk exit bertahap

### A8. Multi Wallet — Keajaiban yang Bukan Keajaiban
- Multi wallet = beberapa dompet berbeda untuk operasi di pasar
- Manfaat: sebar kepemilikan, pancing bot otomatis, proteksi keamanan, DCA efisien
- Efek: bot melihat distribusi sehat → ikut beli → volume naik → harga naik
- Strategi DCA multi wallet: Wallet 1 beli di MC $10K → dip → pakai Wallet 2 untuk DCA (bukan Wallet 1 lagi)
- Cocok untuk simpanan 5 SOL ke atas
- **Charon mapping:** Tidak langsung (Charon single wallet); tapi konsep ini menjelaskan kenapa `max_top20_holder_percent` bisa misleading

### A9. Unwritten Rules — Jangan Makan Orang Sendiri
- Kalau dikasih early access: JANGAN PERNAH ONE CLIP (jual sekaligus)
- Cara jual yang benar: buat wallet baru → kirim supply yang mau dijual → jual dari sana (chart tetap sehat)
- One clip = chart hancur + reputasi hancur + tidak dapat early access lagi
- Di micro cap: lawan kamu adalah sesama orang Indonesia dengan modal terbatas
- Mid cap/high cap: bisa lebih agresif (lawan sudah orang asing dengan modal besar)
- Jadilah trader yang dihormati, bukan yang ditakuti
- **Charon mapping:** Trailing stop = implementasi "jual bertahap" secara otomatis

### A10. Skema Penipuan — Pig Butchering & Drainer
- **Pig Butchering:** Bangun trust palsu → approach halus → curhat/cerita → saat lengah → kuras harta
  - Tanda: kirim uang duluan, ajak teleponan, share screen
- **Airdrop Drainer:** Token gratis dikirim ke wallet → saat dijual → smart contract backdoor → wallet dikuras
  - Cara hindari: jangan interact dengan koin yang tidak pernah dibeli/garap
- **Bot VIP Drainer:** Iklan Telegram bot trading VIP palsu → minta seed phrase
  - Cara hindari: beli Telegram Premium (hindari fat finger iklan)
- **Charon mapping:** Tidak langsung; tapi Charon tidak pernah minta seed phrase

---

## Konsolidasi: Ponyin Intel → Charon Config

### Strategy Parameter Mapping

| Ponyin Concept | Charon Parameter | Recommended Value |
|----------------|-----------------|-------------------|
| Global fees check | `min_gmgn_total_fee_sol` | ≥10 SOL (sniper) |
| Bundler detection | `trending_max_bundler_rate` | ≤0.3 |
| Holder concentration | `max_top20_holder_percent` | ≤80% |
| Market cap gate | `min_mcap_usd` / `max_mcap_usd` | $7K–$200K (sniper) |
| Dip buy (3 candle) | `max_ath_distance_pct` | -50 to -70 (dip_buy) |
| Trailing stop (jual bertahap) | `trailing_enabled`, `trailing_percent` | true, 15–25% |
| Take profit 50% | `tp_percent` | 50–9999 |
| Stop loss -20% | `sl_percent` | -20 to -30 |
| Saved wallet tracking | `min_saved_wallet_holders` | ≥1 (smart_money) |
| LLM confidence | `llm_min_confidence` | 70–75 |

### LLM Prompt Red Flags (from Ponyin Intel)
Inject these into Charon LLM system prompt:
- Long red candle in first 1–5 minutes = dev dumping bundled supply
- Uniform holder balances across many wallets = bundled (coordinated)
- Volume spike without holder growth = wash trading
- Ads/Boost appearing after pump = distribution signal
- Funded wallets under 1 day old = manipulation setup
- Top holders with <0.2 SOL balance = not real players

### Charon Strategy Recommendations (Ponyin-aligned)

**sniper** (fee-claim overlap, immediate entry):
- `min_fee_claim_sol: 0.5` (fee claim = real volume signal)
- `trending_max_bundler_rate: 0.3`
- `tp_percent: 9999` (trailing stop handles exit)
- `trailing_enabled: true`, `trailing_percent: 20–25`
- `sl_percent: -20`

**dip_buy** (3 candle confirmation):
- `max_ath_distance_pct: -50` (dip 50–70% from ATH)
- `min_holders: 50` (narrative already formed)
- `trending_min_swaps: 20`
- `tp_percent: 50–70`

**smart_money** (cabal/saved wallet tracking):
- `min_saved_wallet_holders: 1`
- `min_holders: 100`
- `llm_min_confidence: 72`
- `partial_tp: true` (exit bertahap = unwritten rules)
