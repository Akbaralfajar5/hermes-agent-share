/**
 * Multi-Process PoW Miner Orchestrator (Node.js)
 * Spawns N independent miner-solo processes, submits winning nonce via ethers.js
 *
 * Usage:
 *   PRIVATE_KEY=0x... RPC_URL=https://... WORKERS=64 node miner-orchestrator.js
 *
 * Requires:
 *   - ./miner-solo binary (compiled from cpu-pow-miner-solo.c)
 *   - npm install ethers@6
 *
 * Customize:
 *   - CONTRACT_ADDRESS, ABI, challenge/difficulty fetch logic
 *   - Gas estimation logic
 */
const { ethers } = require('ethers');
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '0x...';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL = process.env.RPC_URL || 'https://ethereum-rpc.publicnode.com';
const NUM_WORKERS = parseInt(process.env.WORKERS || String(os.cpus().length));
const MINER_BIN = path.join(__dirname, 'miner-solo');

// Customize ABI for your contract
const ABI = [
  { type: 'function', stateMutability: 'view', name: 'getChallenge',
    inputs: [{ name: 'miner', type: 'address' }], outputs: [{ type: 'bytes32' }] },
  { type: 'function', stateMutability: 'view', name: 'currentDifficulty',
    inputs: [], outputs: [{ type: 'uint256' }] },
  { type: 'function', stateMutability: 'nonpayable', name: 'mine',
    inputs: [{ name: 'nonce', type: 'uint256' }], outputs: [] },
];

async function mineRound(contract, wallet, challenge, diffHex) {
  const startTime = Date.now();
  console.log(`  Spawning ${NUM_WORKERS} independent processes...`);

  return new Promise((resolve, reject) => {
    const procs = [];
    let done = false;

    for (let i = 0; i < NUM_WORKERS; i++) {
      const nonceStart = `0x${BigInt(i).toString(16)}`;
      const nonceStep = `0x${BigInt(NUM_WORKERS).toString(16)}`;

      const p = spawn(MINER_BIN, [challenge, diffHex, nonceStart, nonceStep]);

      p.stdout.on('data', (data) => {
        const s = data.toString().trim();
        if (s.includes('FOUND') && !done) {
          done = true;
          procs.forEach(pp => { try { pp.kill('SIGTERM'); } catch(e){} });
          const match = s.match(/nonce=(0x[0-9a-fA-F]+)/);
          if (match) {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            console.log(`\n  ✓ Found! ${elapsed}s | ${s}`);
            resolve(match[1]);
          } else {
            reject(new Error('Parse error: ' + s));
          }
        }
      });

      // Show progress from worker 0 only
      p.stderr.on('data', (data) => {
        if (i === 0) process.stdout.write(`\r  [W0] ${data.toString().trim()}`);
      });

      p.on('error', (err) => { if (!done) reject(err); });
      procs.push(p);
    }
  });
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

  console.log(`\nWallet  : ${wallet.address}`);
  console.log(`Workers : ${NUM_WORKERS} independent processes\n`);

  let totalMinted = 0;

  while (true) {
    try {
      const [challenge, difficulty] = await Promise.all([
        contract.getChallenge(wallet.address),
        contract.currentDifficulty(),
      ]);

      const diffHex = '0x' + difficulty.toString(16).padStart(64, '0');
      console.log(`\n[${new Date().toISOString()}] New round`);
      console.log(`  Challenge: ${challenge.slice(0, 18)}...`);
      console.log(`  Difficulty: ${diffHex.slice(0, 18)}...`);

      const nonce = await mineRound(contract, wallet, challenge, diffHex);

      console.log(`\n  Submitting tx...`);
      let gasLimit = 300000n;
      try {
        const est = await contract.mine.estimateGas(BigInt(nonce));
        gasLimit = est * 3n / 2n;
        if (gasLimit < 200000n) gasLimit = 200000n;
        if (gasLimit > 400000n) gasLimit = 400000n;
      } catch (e) {
        console.log(`  Gas est failed, using fallback`);
      }

      const tx = await contract.mine(BigInt(nonce), { gasLimit });
      console.log(`  TX: ${tx.hash}`);
      const receipt = await tx.wait();
      totalMinted++;
      console.log(`  ✓ MINED! Block ${receipt.blockNumber} | Total: ${totalMinted}`);

    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}

main().catch(console.error);
