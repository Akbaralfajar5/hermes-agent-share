/**
 * $HASH GPU Miner — Node.js wrapper (WORKING, May 2026)
 * hash256.org | Contract: 0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc
 *
 * Usage:
 *   PRIVATE_KEY=0x... RPC_URL=https://... NUM_GPUS=4 node miner.js
 *
 * Requires: hash-miner-v4 binary (compiled from hash_miner_v4.cu)
 */

const { ethers } = require('ethers');
const { spawn } = require('child_process');
const path = require('path');
const crypto = require('crypto');

const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL     = process.env.RPC_URL || 'https://ethereum.publicnode.com';
const NUM_GPUS    = parseInt(process.env.NUM_GPUS || '1');
const MINER_BIN   = path.join(__dirname, 'hash-miner-v4');

const CONTRACT_ADDRESS = '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc';
const ABI = [
  { type:'function', stateMutability:'view',      name:'getChallenge',      inputs:[{name:'miner',type:'address'}], outputs:[{type:'bytes32'}] },
  { type:'function', stateMutability:'view',      name:'currentDifficulty', inputs:[], outputs:[{type:'uint256'}] },
  { type:'function', stateMutability:'view',      name:'miningState',       inputs:[], outputs:[
    {name:'era',type:'uint256'},{name:'reward',type:'uint256'},{name:'difficulty',type:'uint256'},
    {name:'minted',type:'uint256'},{name:'remaining',type:'uint256'},
    {name:'epoch',type:'uint256'},{name:'epochBlocksLeft',type:'uint256'}
  ]},
  { type:'function', stateMutability:'nonpayable', name:'mine', inputs:[{name:'nonce',type:'uint256'}], outputs:[] },
];

if (!PRIVATE_KEY) { console.error('Set PRIVATE_KEY env variable'); process.exit(1); }

async function main() {
  const wallet = new ethers.Wallet(PRIVATE_KEY);
  console.log(`Wallet: ${wallet.address} | GPUs: ${NUM_GPUS} | RPC: ${RPC_URL.slice(0,40)}...`);

  let totalMinted = 0, totalEarned = 0n, lastChallenge = '';

  while (true) {
    try {
      const provider = new ethers.JsonRpcProvider(RPC_URL);
      const w = new ethers.Wallet(PRIVATE_KEY, provider);
      const c = new ethers.Contract(CONTRACT_ADDRESS, ABI, w);

      const [challenge, difficulty, state] = await Promise.all([
        c.getChallenge(wallet.address), c.currentDifficulty(), c.miningState(),
      ]);
      const diffHex = '0x' + difficulty.toString(16).padStart(64, '0');

      if (challenge === lastChallenge && totalMinted > 0) {
        process.stdout.write(`\r  Waiting for new epoch...   `);
        await new Promise(r => setTimeout(r, 5000));
        continue;
      }
      lastChallenge = challenge;

      console.log(`\n[${new Date().toISOString()}] New round`);
      console.log(`  Era: ${state.era+1n} | Reward: ${ethers.formatEther(state.reward)} HASH`);
      console.log(`  Minted: ${ethers.formatEther(state.minted)} | Epoch blocks left: ${state.epochBlocksLeft}`);
      console.log(`  Challenge: ${challenge.slice(0,18)}... | Difficulty: ${diffHex.slice(0,18)}...`);

      const startTime = Date.now();
      // Full 256-bit random nonce offsets — CRITICAL, do not use 64-bit
      const nonceOffsets = Array.from({ length: NUM_GPUS }, () => {
        const r = crypto.randomBytes(32);
        r[0] &= 0x7F; // keep MSB clear to avoid overflow issues
        return '0x' + r.toString('hex');
      });

      const nonce = await new Promise((resolve, reject) => {
        const procs = []; let done = false;
        for (let g = 0; g < NUM_GPUS; g++) {
          const p = spawn(MINER_BIN, [challenge, diffHex, String(g), nonceOffsets[g]]);
          p.stdout.on('data', data => {
            const s = data.toString().trim();
            if (s.includes('FOUND') && !done) {
              done = true;
              procs.forEach(pp => { try { pp.kill('SIGTERM'); } catch(e){} });
              const m = s.match(/nonce=(0x[0-9a-fA-F]+)/);
              if (m) { console.log(`\n  ✓ GPU${g} found in ${((Date.now()-startTime)/1000).toFixed(1)}s`); resolve(m[1]); }
              else reject(new Error('Parse error: '+s));
            }
          });
          p.stderr.on('data', data => {
            const s = data.toString().trim();
            if (s.includes('MH/s')) process.stdout.write(`\r  ${s}                    `);
          });
          p.on('error', err => { if (!done) reject(err); });
          procs.push(p);
        }
        setTimeout(() => {
          if (!done) { done=true; procs.forEach(pp=>{try{pp.kill();}catch(e){}}); reject(new Error('TIMEOUT')); }
        }, 480000);
      });

      console.log(`\n  Submitting tx...`);
      const submitProvider = new ethers.JsonRpcProvider(RPC_URL);
      const submitWallet   = new ethers.Wallet(PRIVATE_KEY, submitProvider);
      const submitContract = new ethers.Contract(CONTRACT_ADDRESS, ABI, submitWallet);

      // Verify challenge still valid before submitting
      const currentChallenge = await submitContract.getChallenge(wallet.address);
      if (currentChallenge !== challenge) {
        console.log(`  ⚠ Challenge changed! Skipping.`); lastChallenge = ''; continue;
      }

      const feeData = await submitProvider.getFeeData();
      let gasLimit = 150000n;
      try {
        const est = await submitContract.mine.estimateGas(BigInt(nonce));
        gasLimit = est * 13n / 10n;
      } catch(e) { console.log(`  Gas est failed, using fallback`); }

      const tx = await submitContract.mine(BigInt(nonce), {
        gasLimit,
        maxFeePerGas:         feeData.maxFeePerGas * 2n,
        maxPriorityFeePerGas: feeData.maxPriorityFeePerGas * 3n,
      });
      console.log(`  TX: ${tx.hash}`);
      const receipt = await tx.wait();

      if (receipt.status === 1) {
        totalMinted++; totalEarned += state.reward;
        console.log(`  ✓ MINED! Block ${receipt.blockNumber} | Gas: ${receipt.gasUsed}`);
        console.log(`  Total: ${totalMinted} mints | ${ethers.formatEther(totalEarned)} HASH earned`);
        lastChallenge = '';
      } else {
        console.log(`  ✗ TX reverted!`); lastChallenge = '';
        await new Promise(r => setTimeout(r, 2000));
      }
    } catch(err) {
      console.error(`\n  ✗ Error: ${err.message?.slice(0,120)}`);
      lastChallenge = '';
      await new Promise(r => setTimeout(r, 3000));
    }
  }
}

main().catch(console.error);
