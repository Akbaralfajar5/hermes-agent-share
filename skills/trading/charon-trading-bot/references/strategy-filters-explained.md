# Charon Strategy Filter Explanation

Penjelasan lengkap setiap filter di Charon strategy untuk onboarding user.

## Entry Filters

### 1. MARKET_CAP_MIN (Minimum Market Cap)

Market cap = total nilai token beredar (harga × supply).

| Value | Efek |
|-------|------|
| < 5K | Token baru banget, high risk rug pull |
| 5K-10K | Early entry, masih risky |
| 10K-25K | Sweet spot untuk sniper |
| > 50K | Sudah miss early entry |

**Fungsi:** Filter token yang terlalu kecil/belum ada traction.

### 2. MARKET_CAP_MAX (Maximum Market Cap)

| Value | Efek |
|-------|------|
| < 100K | Banyak token bagus kefilter |
| 100K-500K | Good range untuk meme coins |
| 500K-1M | Mid-cap, lebih stabil |
| > 1M | Entry sudah telat, upside terbatas |

**Fungsi:** Hindari beli token yang sudah pump tinggi.

### 3. ATH_DISTANCE (Jarak dari All-Time High)

Seberapa jauh harga sekarang dari harga tertinggi.

| Value | Artinya |
|-------|---------|
| 0% | Boleh beli walau di ATH |
| -5% | Harus turun minimal 5% dari ATH |
| -15% | Harus turun minimal 15% (beli saat dip) |
| -40% | Cari deep dip (Dip Buy strategy) |

**Fungsi:** Hindari beli di puncak, cari entry saat pullback.

### 4. MIN_HOLDERS (Minimum Holders)

Jumlah wallet yang hold token.

| Value | Artinya |
|-------|---------|
| 0 | Tidak ada minimum |
| 50-100 | Ada traction awal |
| 500-1000 | Solid holder base |
| > 1000 | Established token |

**Fungsi:** Filter token yang belum ada interest.

### 5. MAX_TOP20_HOLDER_PERCENT (Max % Top 20 Holders)

Persentase supply yang dipegang 20 holder terbesar.

| Value | Artinya |
|-------|---------|
| > 80% | Sangat concentrated, high dump risk |
| 50-80% | Moderate concentration |
| < 50% | Distribusi sehat |

**Fungsi:** Hindari token yang dikuasai sedikit whale.

## Trending Filters

### 6. TRENDING_MIN_VOLUME_USD (Min Volume)

Minimum trading volume dalam USD.

| Value | Artinya |
|-------|---------|
| 0 | Tidak ada minimum |
| 1K-5K | Ada aktivitas trading |
| > 10K | High activity |

**Fungsi:** Filter token yang tidak ada volume.

### 7. TRENDING_MIN_SWAPS (Min Swaps)

Minimum jumlah transaksi swap.

| Value | Artinya |
|-------|---------|
| 0 | Tidak ada minimum |
| 50-100 | Moderate activity |
| > 200 | High activity |

**Fungsi:** Pastikan ada real trading activity.

### 8. TRENDING_MAX_RUG_RATIO (Max Rug Ratio)

Persentase indikator rug pull.

| Value | Artinya |
|-------|---------|
| < 20% | Very safe |
| 20-30% | Acceptable |
| > 50% | High rug risk |

**Fungsi:** Filter token dengan indikasi rug pull.

### 9. TRENDING_MAX_BUNDLER_RATE (Max Bundler Rate)

Persentase wallet yang beli via bundler (biasanya insider/dev).

| Value | Artinya |
|-------|---------|
| < 30% | Organic buying |
| 30-50% | Some insider activity |
| 50-70% | High insider accumulation |
| > 70% | Mostly insider, coordinated dump risk |

**Fungsi:** Hindari token dengan banyak insider.

## Fee Requirements

### 10. REQUIRE_FEE_CLAIM

Apakah dev harus sudah claim fee.

| Value | Artinya |
|-------|---------|
| true | Dev sudah claim = committed |
| false | Tidak wajib |

### 11. MIN_FEE_CLAIM_SOL

Minimum fee yang sudah di-claim dev.

| Value | Artinya |
|-------|---------|
| 0 | Tidak ada minimum |
| 0.5-2 SOL | Dev sudah dapat profit |
| > 5 SOL | Dev sangat committed |

### 12. MIN_GMGN_TOTAL_FEE_SOL

Minimum total trading fee dari GMGN data.

**Fungsi:** Indikator trading activity dan liquidity.

## Position & Exit

### 13. POSITION_SIZE_SOL

SOL per trade.

| Value | Risk Level |
|-------|------------|
| 0.01-0.03 | Very conservative |
| 0.05 | Conservative |
| 0.1 | Moderate |
| > 0.2 | Aggressive |

### 14. MAX_OPEN_POSITIONS

Maksimal posisi terbuka bersamaan.

| Value | Efek |
|-------|------|
| 1-3 | Fokus, less diversified |
| 5-10 | Balanced |
| > 10 | Spread thin, more opportunities |

### 15. TP_PERCENT (Take Profit)

Target profit untuk exit.

| Value | Style |
|-------|-------|
| 25-30% | Quick scalp |
| 50-75% | Moderate |
| 100%+ | Let winners run |

### 16. SL_PERCENT (Stop Loss)

Cut loss threshold (negative number).

| Value | Style |
|-------|-------|
| -10% to -15% | Tight, quick exit |
| -20% to -25% | Moderate |
| -30% to -40% | Wide, more room |

### 17. TRAILING_ENABLED & TRAILING_PERCENT

Trailing stop dari high water mark.

| Trailing % | Efek |
|------------|------|
| 10-15% | Tight, lock profit early |
| 20-25% | Moderate |
| 30-35% | Wide, let it run |

### 18. PARTIAL_TP

Partial take profit settings:
- `partial_tp`: true/false
- `partial_tp_at_percent`: trigger di +X%
- `partial_tp_sell_percent`: jual X% posisi

**Example:** Partial TP at +100%, sell 50% → Amankan modal, sisanya free ride.

## LLM Settings

### 19. USE_LLM

Enable/disable LLM analysis untuk strategy ini.

### 20. LLM_MIN_CONFIDENCE

Minimum confidence dari LLM untuk eksekusi BUY.

| Value | Strictness |
|-------|------------|
| 50% | Loose, more trades |
| 60-70% | Moderate |
| 80%+ | Very strict, fewer trades |

## Default Strategies Comparison

| Strategy | MCap | ATH Dist | Holders | Bundler | TP | SL | LLM |
|----------|------|----------|---------|---------|----|----|-----|
| Sniper | 7K-200K | 0% | 0 | 50% | 50% | -25% | 50% |
| Dip Buy | 25K-500K | -40% | 0 | 50% | 30% | -20% | 60% |
| Smart Money | 10K-1M | 0% | 1000 | 30% | 100% | -25% | 70% |
| Degen | 5K-100K | 0% | 0 | 70% | 30% | -15% | Off |

## Adjusting via Telegram

```
/stratset <strategy> <key> <value>

Examples:
/stratset sniper max_mcap_usd 500000
/stratset smart_money min_holders 500
/stratset degen sl_percent -20
```
