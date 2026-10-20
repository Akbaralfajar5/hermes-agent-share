/**
 * Arc Testnet — Faucet Automation (No Captcha!)
 * Claims 20 USDC from faucet.circle.com for all wallets
 *
 * Usage:
 *   node faucet.js           — claim for all wallets
 *   node faucet.js 0 99      — claim for wallets index 0-99
 *   node faucet.js --eurc    — claim EURC instead of USDC
 *   node faucet.js --both    — claim both USDC and EURC
 *
 * Requires: wallets.json (array of {index, address, privateKey})
 * Produces: faucet-log.json (cooldown tracking)
 */

const axios = require('axios');
const fs = require('fs');

const WALLETS_FILE = 'wallets.json';
const LOG_FILE = 'faucet-log.json';

// Arc faucet API (no captcha)
const FAUCET_API = 'https://faucet.circle.com/api/faucet';
const FAUCET_HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://faucet.circle.com',
    'Referer': 'https://faucet.circle.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
};

const TOKENS = {
    USDC: { token: 'USDC', network: 'arc' },
    EURC: { token: 'EURC', network: 'arc' },
};

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function claimFaucet(address, token = 'USDC') {
    try {
        const payload = {
            address,
            token: TOKENS[token].token,
            network: TOKENS[token].network,
        };

        const resp = await axios.post(FAUCET_API, payload, {
            headers: FAUCET_HEADERS,
            timeout: 15000,
        });

        if (resp.data?.txHash || resp.data?.success || resp.status === 200) {
            const txHash = resp.data?.txHash || 'pending';
            console.log(`  ✅ ${token} claimed → ${address.slice(0,10)}... | tx: ${txHash.slice(0,20)}...`);
            return { success: true, txHash, token };
        } else {
            console.log(`  ⚠️  ${token} unexpected response: ${JSON.stringify(resp.data).slice(0,100)}`);
            return { success: false, error: JSON.stringify(resp.data) };
        }
    } catch (err) {
        const msg = err.response?.data?.message || err.response?.data?.error || err.message;
        if (msg?.includes('cooldown') || msg?.includes('already') || msg?.includes('wait')) {
            console.log(`  ⏳ ${token} cooldown: ${address.slice(0,10)}...`);
            return { success: false, cooldown: true };
        }
        console.log(`  ❌ ${token} error: ${msg?.slice(0,80)}`);
        return { success: false, error: msg };
    }
}

async function main() {
    const args = process.argv.slice(2);
    const claimBoth = args.includes('--both');
    const claimEURC = args.includes('--eurc');
    const tokens = claimBoth ? ['USDC', 'EURC'] : claimEURC ? ['EURC'] : ['USDC'];

    const numArgs = args.filter(a => !a.startsWith('--')).map(Number);

    if (!fs.existsSync(WALLETS_FILE)) {
        console.error('❌ wallets.json not found. Run: node generate-wallets.js 1000');
        process.exit(1);
    }

    const wallets = JSON.parse(fs.readFileSync(WALLETS_FILE, 'utf8'));
    const startIdx = numArgs[0] ?? 0;
    const endIdx = numArgs[1] ?? wallets.length - 1;
    const batch = wallets.slice(startIdx, endIdx + 1);

    console.log(`\n💧 Arc Faucet Claimer`);
    console.log(`   Wallets: #${startIdx + 1} → #${endIdx + 1} (${batch.length} total)`);
    console.log(`   Tokens: ${tokens.join(', ')}`);
    console.log(`   Faucet: 20 USDC per claim, 2h cooldown\n`);

    const log = fs.existsSync(LOG_FILE) ? JSON.parse(fs.readFileSync(LOG_FILE, 'utf8')) : {};

    let claimed = 0, skipped = 0, failed = 0;

    for (let i = 0; i < batch.length; i++) {
        const w = batch[i];
        console.log(`\n[${i + 1}/${batch.length}] Wallet #${w.index}: ${w.address}`);

        for (const token of tokens) {
            const logKey = `${w.address}_${token}`;
            const lastClaim = log[logKey]?.timestamp;
            if (lastClaim) {
                const elapsed = Date.now() - new Date(lastClaim).getTime();
                const cooldownMs = 2.1 * 60 * 60 * 1000; // 2h 6min buffer
                if (elapsed < cooldownMs) {
                    const remaining = Math.ceil((cooldownMs - elapsed) / 60000);
                    console.log(`  ⏳ ${token} cooldown: ${remaining}min remaining`);
                    skipped++;
                    continue;
                }
            }

            const result = await claimFaucet(w.address, token);

            if (result.success) {
                claimed++;
                log[logKey] = { timestamp: new Date().toISOString(), txHash: result.txHash };
            } else if (result.cooldown) {
                skipped++;
                log[logKey] = { timestamp: new Date().toISOString(), cooldown: true };
            } else {
                failed++;
            }

            fs.writeFileSync(LOG_FILE, JSON.stringify(log, null, 2));

            if (tokens.length > 1) await sleep(3000 + Math.random() * 2000);
        }

        if (i < batch.length - 1) {
            await sleep(4000 + Math.random() * 3000);
        }
    }

    console.log(`\n${'═'.repeat(50)}`);
    console.log(`💧 Faucet Summary:`);
    console.log(`   ✅ Claimed: ${claimed}`);
    console.log(`   ⏳ Skipped (cooldown): ${skipped}`);
    console.log(`   ❌ Failed: ${failed}`);
    console.log(`${'═'.repeat(50)}\n`);
}

main().catch(console.error);
