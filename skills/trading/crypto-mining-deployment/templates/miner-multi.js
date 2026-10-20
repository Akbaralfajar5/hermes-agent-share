// $HASH CPU Multi-Thread Miner
// Usage: NUM_THREADS=$(nproc) PRIVATE_KEY=0x... RPC_URL=https://... node miner-multi.js
// Spawns N worker threads, each brute-forces keccak256 independently.
// First thread to find valid nonce broadcasts via Flashbots + MEV Blocker.
// Source: built on top of https://github.com/mrfunntastiic/hash256-cli

require("dotenv").config();

const { ethers } = require("ethers");
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");
const os = require("os");

const RPC_URL = process.env.RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc";
const NUM_THREADS = parseInt(process.env.NUM_THREADS || os.cpus().length);

const ABI = [
  "function getChallenge(address miner) view returns (bytes32)",
  "function miningState() view returns (uint256 era,uint256 reward,uint256 difficulty,uint256 minted,uint256 remaining,uint256 epoch,uint256 epochBlocksLeft_)",
  "function mine(uint256 nonce)"
];

// ── Worker thread: brute-force keccak256 ────────────────────────────────────
if (!isMainThread) {
  const { challenge, difficulty, startNonce, threadId } = workerData;
  const { keccak256, toBeHex, zeroPadValue } = require("ethers");

  const diff = BigInt(difficulty);
  let nonce = BigInt(startNonce);
  let count = 0n;

  while (true) {
    // keccak256(abi.encodePacked(challenge, nonce))
    const nonceHex = zeroPadValue(toBeHex(nonce), 32);
    const hash = keccak256(challenge + nonceHex.slice(2));
    const hashNum = BigInt(hash);

    if (hashNum < diff) {
      parentPort.postMessage({ found: true, nonce: nonce.toString() });
      break;
    }

    nonce++;
    count++;

    // Report hashrate every 50k hashes
    if (count % 50000n === 0n) {
      parentPort.postMessage({ found: false, count: Number(count), threadId });
    }
  }
  return;
}

// ── Main thread ──────────────────────────────────────────────────────────────
async function main() {
  if (!RPC_URL || !PRIVATE_KEY) {
    console.error("Set RPC_URL dan PRIVATE_KEY di .env");
    process.exit(1);
  }

  const provider = new ethers.JsonRpcProvider(RPC_URL, 1, { staticNetwork: true });
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

  console.log(`\n╔══════════════════════════════════════════╗`);
  console.log(`║   $HASH CPU Miner — Multi-thread         ║`);
  console.log(`╚══════════════════════════════════════════╝`);
  console.log(`Wallet  : ${wallet.address}`);
  console.log(`Threads : ${NUM_THREADS}`);
  console.log(`RPC     : ${RPC_URL.slice(0, 40)}...`);

  let totalMinted = 0;

  while (true) {
    try {
      const state = await contract.miningState();
      // Use currentDifficulty() directly — miningState() display can be misleading
      const diffRaw = await provider.call({ to: CONTRACT_ADDRESS, data: "0x5c062d6c" });
      const difficulty = BigInt(diffRaw).toString();
      const challenge = await contract.getChallenge(wallet.address);

      console.log(`\n[${new Date().toISOString()}] New round`);
      console.log(`  Era: ${state.era} | Reward: ${ethers.formatUnits(state.reward, 18)} HASH`);
      console.log(`  Difficulty: 0x${BigInt(difficulty).toString(16).slice(0,16)}...`);
      console.log(`  Challenge: ${challenge.slice(0,18)}...`);
      console.log(`  Epoch blocks left: ${state.epochBlocksLeft_}`);
      console.log(`  Spawning ${NUM_THREADS} CPU threads...`);

      // Spawn workers, each starts at a different nonce range
      const nonceRange = BigInt("0xFFFFFFFFFFFFFFFF") / BigInt(NUM_THREADS);
      let found = false;
      let foundNonce = null;
      let hashCounts = new Array(NUM_THREADS).fill(0);
      let startTime = Date.now();

      await new Promise((resolve, reject) => {
        const workers = [];

        for (let i = 0; i < NUM_THREADS; i++) {
          const startNonce = (nonceRange * BigInt(i) + BigInt(Math.floor(Math.random() * 1e12))).toString();
          const w = new Worker(__filename, {
            workerData: { challenge, difficulty, startNonce, threadId: i }
          });

          w.on("message", (msg) => {
            if (msg.found && !found) {
              found = true;
              foundNonce = msg.nonce;
              workers.forEach(ww => { try { ww.terminate(); } catch(e){} });
              resolve();
            } else if (!msg.found && msg.count) {
              hashCounts[msg.threadId] = msg.count;
              const total = hashCounts.reduce((a, b) => a + b, 0);
              const elapsed = (Date.now() - startTime) / 1000;
              const mhs = (total / elapsed / 1e6).toFixed(2);
              process.stdout.write(`\r  [CPU] ${mhs} MH/s | ${(total/1e6).toFixed(1)}M hashes | ${NUM_THREADS} threads   `);
            }
          });

          w.on("error", reject);
          workers.push(w);
        }
      });

      console.log(`\n  Found nonce: ${foundNonce}`);
      console.log(`  Submitting tx (Flashbots + MEVBlocker)...`);

      // Sign and broadcast privately
      const iface = new ethers.Interface(ABI);
      const txData = iface.encodeFunctionData("mine", [BigInt(foundNonce)]);
      const feeData = await provider.getFeeData();
      const nonceTx = await provider.getTransactionCount(wallet.address, "pending");
      let gasLimit = 150000n;
      try {
        gasLimit = await contract.mine.estimateGas(BigInt(foundNonce)) * 13n / 10n;
      } catch(e) {}

      const rawTx = await wallet.signTransaction({
        to: CONTRACT_ADDRESS,
        data: txData,
        gasLimit,
        maxFeePerGas: feeData.maxFeePerGas + ethers.parseUnits("10", "gwei"),
        maxPriorityFeePerGas: ethers.parseUnits("10", "gwei"),
        nonce: nonceTx,
        chainId: 1,
        type: 2,
      });

      // Broadcast to Flashbots + MEVBlocker (skip public mempool)
      const privateRPCs = [
        "https://rpc.flashbots.net/fast",
        "https://rpc.mevblocker.io",
      ];
      const results = await Promise.allSettled(
        privateRPCs.map(async (rpc) => {
          const p = new ethers.JsonRpcProvider(rpc, 1, { staticNetwork: true });
          const hash = await p.send("eth_sendRawTransaction", [rawTx]);
          console.log(`  → ${rpc.includes("flashbots") ? "Flashbots" : "MEVBlocker"}: ${hash}`);
          return hash;
        })
      );

      const txHash = results.find(r => r.status === "fulfilled")?.value;
      if (!txHash) throw new Error("All broadcasts failed");

      // Wait for receipt via dRPC
      let receipt = null;
      for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, 3000));
        receipt = await provider.getTransactionReceipt(txHash);
        if (receipt) break;
      }

      if (receipt?.status === 1) {
        totalMinted++;
        console.log(`  ✓ MINED! Block ${receipt.blockNumber} | Total: ${totalMinted} mints`);
      } else {
        console.log(`  ✗ TX reverted or timeout`);
      }

    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message?.slice(0, 120)}`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}

main().catch(err => {
  console.error(err.message || err);
  process.exit(1);
});
