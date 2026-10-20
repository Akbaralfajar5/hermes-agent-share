const { ethers } = require('ethers');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const os = require('os');

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const CONTRACT_ADDRESS = '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL = process.env.RPC_URL || 'https://ethereum-rpc.publicnode.com';
const NUM_WORKERS = parseInt(process.env.WORKERS || String(os.cpus().length));

if (!PRIVATE_KEY) {
  console.error('ERROR: Set PRIVATE_KEY env var');
  process.exit(1);
}

const ABI = [
  { type: 'function', stateMutability: 'view', name: 'getChallenge', inputs: [{ name: 'miner', type: 'address' }], outputs: [{ type: 'bytes32' }] },
  { type: 'function', stateMutability: 'view', name: 'currentDifficulty', inputs: [], outputs: [{ type: 'uint256' }] },
  { type: 'function', stateMutability: 'view', name: 'miningState', inputs: [], outputs: [
    { name: 'era', type: 'uint256' }, { name: 'reward', type: 'uint256' },
    { name: 'difficulty', type: 'uint256' }, { name: 'totalMints', type: 'uint256' },
    { name: 'epochBlock', type: 'uint256' }, { name: 'currentBlock', type: 'uint256' },
    { name: 'blocksLeft', type: 'uint256' }
  ]},
  { type: 'function', stateMutability: 'nonpayable', name: 'mine', inputs: [{ name: 'nonce', type: 'uint256' }], outputs: [] },
  { type: 'function', stateMutability: 'view', name: 'genesisComplete', inputs: [], outputs: [{ type: 'bool' }] },
];

// ─── WORKER THREAD: keccak256 brute-force ────────────────────────────────────
if (!isMainThread) {
  const { challenge, difficulty, noncePrefix } = workerData;
  const challengeBytes = Buffer.from(challenge.slice(2), 'hex');
  const diffBig = BigInt(difficulty);

  let hashes = 0;
  let nonce = BigInt('0x' + noncePrefix.slice(2).padStart(64, '0'));
  const start = Date.now();

  function toBytes32(n) {
    return Buffer.from(n.toString(16).padStart(64, '0'), 'hex');
  }

  while (true) {
    const nonceBytes = toBytes32(nonce);
    const input = Buffer.concat([challengeBytes, nonceBytes]);
    const hash = ethers.keccak256(input);
    const hashBig = BigInt(hash);

    hashes++;
    if (hashBig < diffBig) {
      parentPort.postMessage({ type: 'found', nonce: '0x' + nonce.toString(16).padStart(64, '0'), hash, hashes });
      break;
    }

    nonce++;

    if (hashes % 50000 === 0) {
      const elapsed = (Date.now() - start) / 1000;
      const hashrate = Math.floor(hashes / elapsed);
      parentPort.postMessage({ type: 'progress', hashes, hashrate, elapsed });
    }
  }
  process.exit(0);
}

// ─── MAIN THREAD ─────────────────────────────────────────────────────────────
async function main() {
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

  console.log(`\n╔══════════════════════════════════════════╗`);
  console.log(`║         $HASH CPU MINER v1.0             ║`);
  console.log(`╚══════════════════════════════════════════╝`);
  console.log(`Wallet  : ${wallet.address}`);
  console.log(`RPC     : ${RPC_URL}`);
  console.log(`Workers : ${NUM_WORKERS}`);
  console.log(`Contract: ${CONTRACT_ADDRESS}\n`);

  // Check genesis
  const genesisOk = await contract.genesisComplete();
  if (!genesisOk) {
    console.log('Mining not open yet — genesis not complete. Waiting...');
    await new Promise(r => setTimeout(r, 60000));
  }

  let totalMinted = 0;
  let totalEarned = 0n;

  while (true) {
    try {
      const [challenge, difficulty, state] = await Promise.all([
        contract.getChallenge(wallet.address),
        contract.currentDifficulty(),
        contract.miningState(),
      ]);

      const reward = ethers.formatEther(state.reward);
      console.log(`\n[${new Date().toISOString()}] Starting new round`);
      console.log(`  Era: ${state.era + 1n} | Reward: ${reward} HASH | Difficulty: 0x${difficulty.toString(16).slice(0, 10)}...`);
      console.log(`  Challenge: ${challenge.slice(0, 18)}...`);
      console.log(`  Spawning ${NUM_WORKERS} workers...`);

      const nonceRange = BigInt('0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff') / BigInt(NUM_WORKERS);

      const found = await new Promise((resolve, reject) => {
        const workers = [];
        let done = false;
        let totalHashes = 0;
        const startTime = Date.now();

        for (let i = 0; i < NUM_WORKERS; i++) {
          const nonceStart = nonceRange * BigInt(i);
          const noncePrefix = '0x' + nonceStart.toString(16).padStart(64, '0');

          const w = new Worker(__filename, {
            workerData: { challenge, difficulty: difficulty.toString(), noncePrefix }
          });

          w.on('message', (msg) => {
            if (msg.type === 'found' && !done) {
              done = true;
              workers.forEach(ww => ww.terminate());
              resolve({ nonce: msg.nonce, hashes: totalHashes + msg.hashes });
            } else if (msg.type === 'progress') {
              totalHashes += 50000;
              const elapsed = (Date.now() - startTime) / 1000;
              const hashrate = Math.floor(totalHashes / elapsed);
              process.stdout.write(`\r  Searching... ${(totalHashes / 1e6).toFixed(1)}M hashes | ${(hashrate / 1000).toFixed(0)} kH/s | ${elapsed.toFixed(0)}s`);
            }
          });

          w.on('error', reject);
          workers.push(w);
        }
      });

      console.log(`\n  ✓ Nonce found! ${found.hashes.toLocaleString()} hashes tried`);
      console.log(`  Submitting tx...`);

      let gasLimit = 300000n;
      try {
        const est = await contract.mine.estimateGas(BigInt(found.nonce));
        gasLimit = est * 3n / 2n;
        if (gasLimit < 200000n) gasLimit = 200000n;
        if (gasLimit > 400000n) gasLimit = 400000n;
      } catch (e) {
        console.log(`  Gas estimation failed, using fallback: ${gasLimit}`);
      }

      const tx = await contract.mine(BigInt(found.nonce), { gasLimit });
      console.log(`  TX: ${tx.hash}`);
      const receipt = await tx.wait();
      totalMinted++;
      totalEarned += state.reward;

      console.log(`  ✓ MINED! Block ${receipt.blockNumber} | Gas: ${receipt.gasUsed}`);
      console.log(`  Total: ${totalMinted} mints | ${ethers.formatEther(totalEarned)} HASH earned`);

    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      if (err.message.includes('genesis') || err.message.includes('not open')) {
        console.log('  Mining not open. Waiting 60s...');
        await new Promise(r => setTimeout(r, 60000));
      } else {
        console.log('  Retrying in 5s...');
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }
}

main().catch(console.error);
