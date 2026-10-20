const { ethers } = require('ethers');
const { spawn } = require('child_process');
const path = require('path');

const CONTRACT_ADDRESS = '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL = process.env.RPC_URL || 'https://ethereum-rpc.publicnode.com';
const NUM_WORKERS = parseInt(process.env.WORKERS || '64');
const MINER_BIN = path.join(__dirname, 'hash-miner-native');

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
];

async function main() {
  if (!PRIVATE_KEY) { console.error('Set PRIVATE_KEY env var'); process.exit(1); }
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);

  console.log(`\n╔══════════════════════════════════════════╗`);
  console.log(`║     $HASH Native C Miner v2.0            ║`);
  console.log(`╚══════════════════════════════════════════╝`);
  console.log(`Wallet  : ${wallet.address}`);
  console.log(`Workers : ${NUM_WORKERS}`);
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
      console.log(`  Mining with ${NUM_WORKERS} native C workers...`);

      const nonce = await new Promise((resolve, reject) => {
        const proc = spawn(MINER_BIN, [challenge, diffHex, String(NUM_WORKERS)]);
        let output = '';
        proc.stdout.on('data', (data) => {
          const s = data.toString();
          output += s;
          if (s.includes('MH searched')) process.stdout.write('\r' + s.trim());
          if (s.includes('Hashrate')) console.log('\n' + s.trim());
        });
        proc.stderr.on('data', (data) => console.error('miner err:', data.toString()));
        proc.on('close', () => {
          const match = output.match(/RESULT_NONCE=(0x[0-9a-fA-F]+)/);
          if (match) resolve(match[1]);
          else reject(new Error('No nonce found: ' + output.slice(-200)));
        });
        proc.on('error', reject);
      });

      console.log(`\n  ✓ Nonce found: ${nonce}`);
      console.log(`  Submitting tx...`);

      let gasLimit = 300000n;
      try {
        const est = await contract.mine.estimateGas(BigInt(nonce));
        gasLimit = est * 3n / 2n;
        if (gasLimit < 200000n) gasLimit = 200000n;
        if (gasLimit > 400000n) gasLimit = 400000n;
      } catch (e) { console.log(`  Gas est failed, using fallback ${gasLimit}`); }

      const tx = await contract.mine(BigInt(nonce), { gasLimit });
      console.log(`  TX: ${tx.hash}`);
      const receipt = await tx.wait();
      totalMinted++;
      totalEarned += state.reward;
      console.log(`  ✓ MINED! Block ${receipt.blockNumber}`);
      console.log(`  Total: ${totalMinted} mints | ${ethers.formatEther(totalEarned)} HASH earned`);

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
