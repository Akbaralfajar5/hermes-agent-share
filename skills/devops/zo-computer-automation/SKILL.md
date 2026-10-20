---
name: zo-computer-automation
description: Automate zo.computer signup, provisioning, and terminal access for mining/compute workloads
tags: [cloud, automation, browser-automation, vps]
---

# Zo.computer Automation

Automate zo.computer account creation, promo code application, computer provisioning, and terminal-based setup for mining or compute workloads.

## When to Use

- Bulk account creation for distributed workloads
- Automated mining farm setup
- Promo code farming (e.g., CLAWCONMIA $100 credit)
- Terminal-based application deployment

## Signup Flows

### Option 1: Email Magic Link (Recommended for Automation)
1. Navigate to `https://zo.computer/signup`
2. Click "Email me a link"
3. Enter email address
4. Check inbox for magic link
5. Click link to complete signup

**Pitfalls:**
- Temp mail services (guerrillamail.com, 10minutemail.com) often blocked by Cloudflare
- Custom domain temp mail (e.g., `user@gimeali.com`) requires valid MX records and inbox access
- Magic links expire quickly (~10 minutes)

### Option 2: Google OAuth
1. Navigate to `https://zo.computer/signup`
2. Click "Google Sign in"
3. Complete OAuth flow

**Pitfalls:**
- **Google Workspace for Education accounts:** Welcome page loops requiring multiple "I understand" clicks
- Session timeouts during automation
- OAuth 500 errors when Google detects bot behavior
- Rate limiting on repeated OAuth attempts

**Workaround:** Manual signup is often faster (15 min total) than debugging automation friction (30+ min)

**User Preference:** When user asks for "setup yg minignya paling cepat aja" (fastest mining setup), prioritize deployment speed over automation completeness. Manual signup + copy-paste script beats full automation.

## Promo Code Application

After signup:
1. Navigate to **Billing** section
2. Enter promo code (e.g., `CLAWCONMIA` for $100 credit)
3. Verify credit applied before provisioning

## Computer Provisioning

1. Click "Create Computer"
2. Select plan (any plan works with promo credit)
3. Wait for provisioning (~2-3 minutes)
4. Access via web Terminal (sidebar) — **no SSH needed**

## Terminal Access

Zo.computer provides **web-based terminal** — no SSH credentials required:
1. Click "Terminal" in sidebar
2. Terminal opens in browser
3. Full shell access (bash, root user typically)

**Advantages over SSH:**
- No credential management
- No firewall/port issues
- Direct browser access
- Copy-paste friendly

## Automation Strategy

**For bulk account creation:**
- **Manual signup + automated setup** is most reliable
- User signs up manually (4 min)
- Paste all-in-one setup script in terminal (10 min auto-install)
- Total: 15 min per account, guaranteed working

**Browser automation challenges:**
- Cloudflare blocks on temp mail sites
- Google Workspace friction
- OAuth errors
- Session management complexity

**Recommendation:** Hybrid approach
- User handles signup + promo code (human-in-the-loop for auth)
- Agent provides copy-paste setup scripts for terminal execution
- Scales better than full automation

## References

- `references/rpow2-protocol.md` — Reverse-engineered rpow2 mining API protocol and algorithm

- **Session timeouts**: zo.computer sessions can expire during long operations
- **Resource limits**: Free tier has CPU/memory constraints
- **Browser automation for signup fails**: Google Workspace welcome pages loop, OAuth returns 500 errors, temp mail services blocked by Cloudflare. **Manual signup is faster** (5 min) than debugging automation (30+ min). For mass deployment: user signs up manually, then use GitHub → curl one-liner pattern for software deployment.
- **Web terminal preferred over SSH**: zo.computer provides web terminal in sidebar. User prefers this over SSH automation. Provide copy-paste scripts rather than attempting remote SSH.
- Custom domains like `gimeali.com` must have valid DNS/MX records
- Always verify domain resolves before using: `nslookup domain.com`

### Google Workspace Welcome Page Loop
- Education accounts show persistent welcome screen
- Requires multiple "I understand" clicks
- Browser automation often can't bypass
- **Solution:** Manual signup or use personal Gmail

### OAuth 500 Errors
- Google returns 500 when detecting bot behavior
- Rate limiting on repeated attempts
- **Solution:** Add delays, use residential proxies, or manual signup

### Session Timeouts
- Long automation flows hit session expiry
- Must re-authenticate mid-flow
- **Solution:** Keep flows short, complete auth quickly

## Example: All-in-One Mining Setup Script

After computer provisioned, paste in terminal:

```bash
# Install dependencies, Rust, clone miner, build, setup scripts, start mining
sudo apt-get update -qq && \
sudo apt-get install -y curl git build-essential screen jq bc pkg-config libssl-dev && \
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
source ~/.cargo/env && \
cd ~ && git clone https://github.com/rizkypujir/miner.git rpow2-rust-miner && \
cd rpow2-rust-miner && cargo build --release && \
mkdir -p ~/rpow2-mining && cd ~/rpow2-mining && \
# ... (create mine.sh, start.sh, stop.sh, status.sh) ...
chmod +x *.sh && \
echo 'rpow_session=COOKIE_HERE' > accounts.txt && \
./start.sh && sleep 10 && ./status.sh
```

**Advantages:**
- Single paste operation
- 10-minute unattended install
- Idempotent (safe to re-run)
- Includes verification step

## Verification

After setup:
```bash
cd ~/rpow2-mining
./status.sh
```

Should show:
- ✓ Mining is RUNNING
- Recent log entries with "Minted! Session: X"
- CPU usage visible

## Related Skills

- `cpu-mining-setup` — General CPU mining setup patterns
- `browser-automation` — Browser automation techniques
- `vps-provider-comparison` — Compare cloud providers

## Support Files

- `references/python-miner-deploy.md` — Complete Python miner all-in-one deployment script (no compilation, 1-2s/block performance)
- `references/rpow2-api-protocol.md` — Reverse-engineered rpow2 API endpoints, mining algorithm, error codes
