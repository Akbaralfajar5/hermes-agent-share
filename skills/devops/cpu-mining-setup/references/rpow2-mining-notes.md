# rpow2 Mining Notes

Session-specific notes for rpow2 (Proof of Work v2) CPU mining setup and operations.

## Cookie Format

rpow2 uses JWT-based session cookies:

```
rpow_session=eyJlbWFpbCI6ImFrYmFyYWxwYWphcjVAZ21haWwuY29tIiwiZXhwIjoxNzgwODQzNjU4fQ.GShkyCeG_9TMhkFL5uLua5iPDmWm_xlWNhTpup3trtU
```

**Structure:**
- Cookie name: `rpow_session`
- Value: JWT token (base64-encoded JSON + signature)
- Decoded payload example:
  ```json
  {
    "email": "user@example.com",
    "exp": 1780843658  // Unix timestamp (June 4, 2026)
  }
  ```

**Expiration:**
- Typical validity: ~3 months
- Check expiration: Decode JWT payload and check `exp` field
- Update before expiration to avoid mining downtime

**Obtaining Cookie:**
1. Login to https://api.rpow2.com in browser
2. Open DevTools (F12)
3. Application tab > Cookies > api.rpow2.com
4. Copy value of `rpow_session` cookie

## Miner Repository

**Official Rust miner:**
- Repo: https://github.com/rizkypujir/miner
- Language: Rust
- Build time: 2-5 minutes on Threadripper PRO
- Binary location: `target/release/rpow2-miner` (note: binary name is `rpow2-miner`, not `miner`)

**Build dependencies:**
```bash
# Required for OpenSSL linking
apt-get install -y pkg-config libssl-dev
```

**Command-line usage:**
```bash
# Miner reads from accounts.txt in working directory
echo "rpow_session=..." > accounts.txt
./rpow2-miner --threads 6
```

**Arguments:**
- `--threads`: Number of parallel workers (default: all cores)
- Cookie is read from `accounts.txt` file (one cookie per line, supports multi-account)

## API Behavior

**Endpoint:** https://api.rpow2.com

**Known issues:**
- **Frequent timeouts** — API often returns timeout errors (normal behavior)
- **Retry logic required** — Miner must auto-retry on timeout
- **Rate limiting** — Unknown limits, but aggressive mining may trigger throttling

**Network requirements:**
- Stable connection (API calls every few seconds)
- Low latency preferred (US-based API, Bulgaria VPS may have 100-200ms latency)
- Bandwidth: Minimal (<1 GB/day typical)

## Mining Performance

**Challenge window:** 5 minutes (300 seconds)

**Performance by CPU:**
- **Intel Xeon E5-4669 v4** (Broadwell 2016, 2.2 GHz base, 2.9 GHz boost):
  - Mining speed: 3-6 seconds per block
  - Blocks per challenge: ~50-100
  - Verdict: Too slow ❌

- **AMD Threadripper PRO 5995WX** (Zen 3, 2.7 GHz base, 4.5 GHz boost):
  - Mining speed: 1-3 seconds per block
  - Blocks per challenge: ~100-300
  - Verdict: Good ✅

- **AMD Threadripper PRO 7985WX** (Zen 4, 3.2 GHz base, 5.1 GHz boost):\n  - Mining speed: 0.06-0.24 seconds per block (verified May 2026 on QuickPod)\n  - Blocks per challenge: ~1250-5000\n  - Verdict: Best ✅✅ (10-30x faster than Xeon E5-4669 v4)

**Key factors:**
1. **Single-core clock speed** (most important)
2. **IPC (architecture generation)** (Zen 4 > Zen 3 > Zen 2 > Broadwell)
3. **Thread count** (6 threads optimal for parallel workers)

## Optimal Configuration

**Thread count:**
- **6 threads** = optimal for 6-vCPU instances (one worker per thread)
- **4 threads** = good for 4-vCPU instances
- **More threads ≠ better** — diminishing returns beyond physical core count

**Auto-restart:**
- **24-hour rotation** — prevents memory leaks, refreshes connection
- **10-second delay on crash** — avoids rapid restart loops
- **Random jitter (0-60s)** — prevents synchronized restarts across multiple instances

**Logging:**
- Log to file (`mining.log`) for persistence
- Rotate logs manually if file grows too large (`> mining.log`)
- Monitor success rate: `grep "Success" mining.log | wc -l`

## Troubleshooting

### High timeout rate

**Symptoms:**
- Logs show frequent "timeout" or "connection refused" errors
- Success rate < 10%

**Causes:**
- API instability (common)
- Network latency (Bulgaria → US)
- Rate limiting (too many requests)

**Solutions:**
- Wait and retry (API instability usually temporary)
- Test latency: `ping api.rpow2.com`
- Reduce thread count (less aggressive API usage)
- Consider US-based VPS (lower latency)

### Low mining speed

**Symptoms:**
- Mining speed > 3 seconds per block
- Blocks per challenge < 100

**Causes:**
- CPU throttling (thermal limits, power limits)
- Noisy neighbors (shared VPS host)
- Old CPU architecture (Broadwell, Zen 2)

**Solutions:**
- Check actual clock speeds: `watch -n1 "grep MHz /proc/cpuinfo"`
- Monitor CPU temperature (if available): `sensors`
- Upgrade to faster CPU (Threadripper PRO 7985WX recommended)

### Cookie expired

**Symptoms:**
- Miner fails with "unauthorized" or "invalid session" error
- Logs show authentication failures

**Solutions:**
- Decode JWT to check expiration: `echo "eyJ..." | base64 -d`
- Obtain new cookie from browser
- Update `cookie.txt` and restart mining

## Migration Notes

**From Python miner to Rust miner:**
- Rust miner is **5-10x faster** than Python miner
- Python miner too slow for 5-minute challenge window (2 cores)
- Rust miner handles 6+ threads efficiently

**From old VPS to new VPS:**
1. Backup cookie: `scp old-vps:~/rpow2-mining/cookie.txt ./cookie.txt.bak`
2. Run setup on new VPS
3. Restore cookie: `scp ./cookie.txt.bak new-vps:~/rpow2-mining/cookie.txt`
4. Start mining on new VPS
5. Stop mining on old VPS

## Monitoring

**Key metrics:**
- **CPU usage**: Should be ~100% per mining thread
- **Memory usage**: Should be < 500 MB
- **Success rate**: `grep "Success" mining.log | wc -l` vs `grep "timeout" mining.log | wc -l`
- **Blocks per hour**: `grep "block" mining.log | grep "$(date +%Y-%m-%d\ %H)" | wc -l`

**Daily checks:**
- Verify mining is running: `screen -list | grep rpow2`
- Check recent logs: `tail -50 mining.log`
- Monitor CPU usage: `top -bn1 | grep miner`

**Watchdog (optional):**
```bash
# Add to crontab: check every 5 minutes
*/5 * * * * screen -list | grep -q rpow2 || (cd ~/rpow2-mining && ./start.sh)
```

## Cost Analysis (May 2026)

**VPS costs:**
- Threadripper PRO 5995WX (6 threads): $0.138/hr = $99/month
- Threadripper PRO 7985WX (6 threads): $0.141/hr = $101/month

**Performance gain:**
- 5995WX: 2x faster than Xeon E5-4669 v4
- 7985WX: 3x faster than Xeon E5-4669 v4

**ROI depends on:**
- rpow2 token value
- Blocks mined per challenge
- Competition (difficulty)
- API uptime

## See Also

- `vps-provider-comparison` skill — Finding optimal VPS for CPU mining
- `templates/rpow2-mining-setup.sh` — Automated setup script
