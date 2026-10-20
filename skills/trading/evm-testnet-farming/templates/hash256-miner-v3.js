/**
 * hash256.org $HASH Multi-Process Miner v3.0
 * Spawns N independent C processes, each searching a disjoint nonce range.
 * No mutex, no shared memory — pure parallel, ~99% CPU utilization.
 *
 * Requires: miner-solo binary in same directory, ethers@6
 * Usage: PRIVATE_KEY=0x... RPC_URL=https://... WORKERS=64 node miner-v3.js
 */
const { ethers } = require('ethers');
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const CONTRACT_ADDRESS = '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL = process.env.RPC_URL || 'https://ethereum-rpc.publicnode.com';
const NUM_WORKERS = parseInt(process.env.WORKERS || String(os.cpus().length));
const MINER_BIN = path.join(__dirname, 'miner-solo');

const ABI = [
  { type: 'function', stateMutability: 'view', name: 'getChallenge',
    inputs: [{ name: 'miner', type: 'address' }], outputs: [{ type: 'bytes32' }] },
  { type: 'function', stateMutability: 'view', name: 'currentDifficulty',
    inputs: [], outputs: [{ type: 'uint256' }] },
  { type: 'function', stateMutability: 'view', name: 'miningState',
    inputs: [], outputs: [
      { name: 'era', type: 'uint256' }, { name: 'reward', type: 'uint256' },
      { name: 'difficulty', type: 'uint256' }, { name: 'totalMints', type: 'uint256' },
      { name: 'epochBlock', type: 'uint256' }, { name: 'currentBlock', type: 'uint256' },
      { name: 'blocksLeft', type: 'uint256' }
    ]},
  { type: 'function', stateMutability: 'nonpayable', name: 'mine',
    inputs: [{ name: 'nonce', type: 'uint256' }], outputs: [] },
];

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

  console.log(`\n╔══════════════════════════════════════════╗`);
  console.log(`║     $HASH Multi-Process Miner v3.0       ║`);
  console.log(`╚══════════════════════════════════════════╝`);
  console.log(`Wallet  : ${wallet.address}`);
  console.log(`Workers : ${NUM_WORKERS} independent processes`);
  console.log(`Binary  : ${MINER_BIN}\n`);

  let totalMinted = 0;
  let totalEarned = 0n;

  while (true) {
    try {
      const [challenge, difficulty, state] = await Promise.all([
        contract.getChallenge(wallet.address),
        contract.currentDifficulty(),
        contract.miningState(),
      ]);

      const diffHex = '0x' + difficulty.toString(16).padStart(64, '0');
      const reward = ethers.formatEther(state.reward);
      console.log(`\n[${new Date().toISOString()}] New round`);
      console.log(`  Era: ${state.era + 1n} | Reward: ${reward} HASH`);
      console.log(`  Challenge: ${challenge.slice(0, 18)}...`);
      console.log(`  Spawning ${NUM_WORKERS} independent processes...`);

      const startTime = Date.now();

      const nonce = await new Promise((resolve, reject) => {
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

          p.stderr.on('data', (data) => {
            if (i === 0) process.stdout.write(`\r  [0] ${data.toString().trim()}`);
          });

          p.on('error', (err) => { if (!done) reject(err); });
          procs.push(p);
        }
      });

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
      totalEarned += state.reward;

      console.log(`  ✓ MINED! Block ${receipt.blockNumber} | Gas: ${receipt.gasUsed}`);
      console.log(`  Total: ${totalMinted} mints | ${ethers.formatEther(totalEarned)} HASH`);

    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      if (err.message.includes('genesis') || err.message.includes('not open')) {
        console.log('  Mining not open yet, waiting 60s...');
        await new Promise(r => setTimeout(r, 60000));
      } else {
        console.log('  Retrying in 5s...');
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }
}

main().catch(console.error);
