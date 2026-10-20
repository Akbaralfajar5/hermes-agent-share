# QuickPod Threadripper PRO 7985WX Setup Notes

Session: May 9, 2026

## VPS Specs

**Provider:** QuickPod.io
**CPU:** AMD Ryzen Threadripper PRO 7985WX (Zen 4, 64-core)
**Config:** 6 vCPU threads allocated
**RAM:** 18 GB
**Storage:** 30 GB
**Network:** 568 Mbps up / 601 Mbps down
**Location:** Sofia, Bulgaria
**Cost:** $0.1409/hr (~$101/month, 30-day max rental)
**OS:** Ubuntu 22.04.5 LTS (Jammy) in Docker container

## SSH Access

QuickPod uses UUID-based usernames:
```bash
ssh -p <PORT> <UUID>@<IP>
# Example: ssh -p 41001 b67793f2-36e3-4bbe-8b58-fe899db0759c@84.242.173.26
```

**Passwordless SSH:** QuickPod instances support key-based auth by default. No password prompt = working.

## Performance

**Mining Speed (rpow2):**
- Fastest block: 0.02s
- Average: 0.06-0.47s per block
- Blocks per minute: ~20 blocks
- Blocks per hour: ~1,223 blocks
- Daily earnings: ~0.448 rpow2 (after May 2026 reward nerf)

**Comparison to older hardware:**
- Intel Xeon E5-4669 v4 (2.2 GHz base, 2.9 GHz boost, Broadwell 2016): 3-6s/block
- Threadripper PRO 7985WX (3.2 GHz base, 5.1 GHz boost, Zen 4 2022): 0.06-0.47s/block
- **Performance gain: 10-30x faster**

## Build Time

Rust miner compilation on Threadripper PRO 7985WX:
- **19.58 seconds** (release build)
- Much faster than typical VPS (2-5 minutes)

## Container Environment

QuickPod runs Ubuntu in Docker containers:
- Hostname: random hex (e.g., `3e4faa34dc8e`)
- Kernel: Host kernel (5.15.0-176-generic)
- No systemd (use screen/tmux for background processes)
- Limited CPU threads (6 out of 64 physical cores)

## CPU Detection

```bash
$ lscpu | grep -E 'Model name|CPU\(s\)|Thread|Architecture'
Architecture:                            x86_64
CPU(s):                                  32
On-line CPU(s) list:                     0-31
Model name:                              AMD Ryzen Threadripper PRO 7985WX 64-Cores
Thread(s) per core:                      1
NUMA node0 CPU(s):                       0-31
```

**Note:** Shows 32 CPUs but only 6 are allocated to the container. Use `nproc` (returns 6) not `lscpu` for thread count.

## rpow2 Reward Economics (May 2026)

**Reward per block:** 0.000015258 rpow2

**Before nerf (pre-May 2026):**
- ~1 rpow2 per 5 minutes
- ~288 rpow2/day
- ~8,640 rpow2/month

**After nerf (May 2026):**
- ~0.001555 rpow2 per 5 minutes
- ~0.448 rpow2/day
- ~13.44 rpow2/month
- **99.84% reduction** (643x decrease)

**Break-even analysis:**
- Monthly cost: $101
- Monthly earnings: 13.44 rpow2
- Break-even price: $7.51 per rpow2
- Profitable if rpow2 > $7.51

**Historical context:** User reported "kemarin sebelum nerf, reward sampe 1 rpow per 5 mint" — massive reward reduction likely due to network growth or tokenomics adjustment.

## Multi-Account Mining

**Thread distribution:**
- 1 account: 6 threads/account, ~20 blocks/min total
- 2 accounts: 3 threads/account, ~10 blocks/min each, ~20 blocks/min total
- 6 accounts: 1 thread/account, ~3.33 blocks/min each, ~20 blocks/min total

**Conclusion:** Multi-account on single VPS provides NO benefit for rpow2 (no referral program, no per-account limits). Total output remains constant regardless of account count.

**Better strategy:** Use full thread allocation for single account to maximize per-block speed.

## QuickPod-Specific Notes

**Template selection:** Ubuntu 22.04 Jammy (codename visible in template list)

**No password in dashboard:** SSH credentials available via "Connect" button in QuickPod console, not visible in main pod view.

**VPS destruction:** User reported destroying VPS mid-session. QuickPod allows instant termination. Check if pro-rated refunds available for unused days.

## Balance Check API

```bash
curl -s -H "Cookie: rpow_session=<JWT_TOKEN>" https://api.rpow2.com/me
```

**Response format:**
```json
{
  "email": "user@example.com",
  "balance_base_units": "171002136120",
  "minted_base_units": "171002136120",
  "sent_base_units": "0",
  "received_base_units": "0",
  "wrap_allowed": false,
  "solana_wallet": null,
  "srpow_supply_owned_base_units": "0"
}
```

**Conversion:** 1 rpow2 = 1 billion base units (1,000,000,000)
- 171,002,136,120 base units = 171.002 rpow2

**Cookie extraction:** rpow2 cookies are JWT tokens. Decode to extract email:
```bash
echo '<BASE64_PAYLOAD>' | base64 -d
# Returns: {"email":"user@example.com","exp":1780862126}
```

## Lessons Learned

1. **Always install OpenSSL dev packages first** — saves 5+ minutes of failed build + retry cycle
2. **Check actual binary name** — rizkypujir/miner builds as `rpow2-miner` not `miner`
3. **Use accounts.txt not --cookie flag** — miner expects file-based config
4. **Reward nerfs happen** — 99.84% reduction observed, always check current economics before committing to long-term rental
5. **QuickPod pricing competitive** — $0.14/hr for Threadripper PRO 7985WX is excellent value for single-core performance
6. **Container CPU limits** — `lscpu` shows host CPU, use `nproc` for actual allocated threads
