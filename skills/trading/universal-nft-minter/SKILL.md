---
name: universal-nft-minter
description: "Universal NFT minter — auto-detect mint function, price, and gas from any URL or contract address. Supports OpenSea, Manifold, Zora, Seadrop, and direct contracts. Mass mint with multiple wallets."
version: 1.0.0
author: Hermes (adapted from SUPERAGENT v3 m13)
license: MIT
metadata:
  hermes:
    tags: [nft, mint, opensea, manifold, zora, seadrop, on-chain, web3, ethers]
---

# Universal NFT Minter

Load when: mint, NFT, opensea, manifold, zora, seadrop, mint nft, mint contract, claim NFT, mint url.

One command → mint anywhere. Auto-detect mint function, price, gas. No manual ABI needed.

## Accepted Input Shapes

- OpenSea URL: `https://opensea.io/collection/<slug>` or `https://opensea.io/assets/<chain>/<contract>/<id>`
- Direct contract: `0xABC... on base` or just `0xABC...` (default mainnet)
- Manifold claim link: `https://app.manifold.xyz/c/<id>`
- Zora link: `https://zora.co/collect/<chain>:<contract>/<token>`
- Raw: `mint <contract> <amount> on <chain>`

Default amount = 1. Default chain = ethereum.

---

## Architecture

```
parse input → resolve(contract, chain, mintFn, price, args)
            → auto gas (estimate + buffer)
            → simulate (eth_call)
            → send tx
            → wait receipt
            → report
```

Never ask user for: gas, function name, ABI. Detect everything.

---

## Step 1 — Parse input

```js
function parseTarget(input) {
  const s = input.trim();

  // OpenSea assets URL
  let m = s.match(/opensea\.io\/assets\/([\w-]+)\/(0x[a-fA-F0-9]{40})(?:\/(\d+))?/);
  if (m) return { source: 'opensea', chain: chainSlug(m[1]), contract: m[2], tokenId: m[3] };

  // OpenSea collection URL → needs slug → contract lookup
  m = s.match(/opensea\.io\/collection\/([\w-]+)/);
  if (m) return { source: 'opensea_slug', slug: m[1] };

  // Manifold
  m = s.match(/manifold\.xyz\/c\/(\w+)/);
  if (m) return { source: 'manifold', claimId: m[1] };

  // Zora
  m = s.match(/zora\.co\/collect\/(\w+):(0x[a-fA-F0-9]{40})(?:\/(\d+))?/);
  if (m) return { source: 'zora', chain: chainSlug(m[1]), contract: m[2], tokenId: m[3] };

  // "mint 0xABC on base 5"
  m = s.match(/(0x[a-fA-F0-9]{40})(?:\s+on\s+(\w+))?(?:\s+x?(\d+))?/i);
  if (m) return { source: 'direct', contract: m[1], chain: m[2] || 'ethereum', amount: Number(m[3] || 1) };

  throw new Error('cannot parse mint target');
}

function chainSlug(s) {
  const map = {
    ethereum: 'ethereum', eth: 'ethereum', mainnet: 'ethereum',
    base: 'base', matic: 'polygon', polygon: 'polygon',
    arbitrum: 'arbitrum', arb: 'arbitrum',
    optimism: 'optimism', op: 'optimism',
    zora: 'zora-network',
  };
  return map[s.toLowerCase()] || s;
}
```

---

## Step 2 — Detect mint function

Try signatures in order. First one that exists wins.

```js
const MINT_SIGNATURES = [
  { sig: 'mint(uint256)',                    args: ['amount'] },
  { sig: 'mint(address,uint256)',            args: ['to', 'amount'] },
  { sig: 'publicMint(uint256)',              args: ['amount'] },
  { sig: 'mintPublic(uint256)',              args: ['amount'] },
  { sig: 'mint()',                           args: [] },
  { sig: 'claim(uint256)',                   args: ['amount'] },
  { sig: 'mintPublic(address,address,address,uint256)', args: ['nftContract','feeRecipient','minterIfNotPayer','quantity'], protocol: 'seadrop' },
  { sig: 'mintWithRewards(address,uint256,uint256,bytes,address)', args: ['minter','tokenId','quantity','minterArgs','mintReferral'], protocol: 'zora' },
  { sig: 'mint(address,uint256,uint256,bytes)', args: ['to','id','amount','data'] },
];

async function detectMintFunction(contract, signer) {
  for (const fn of MINT_SIGNATURES) {
    const iface = new ethers.Interface([`function ${fn.sig} payable`]);
    const data = iface.encodeFunctionData(fn.sig.split('(')[0], synthArgs(fn, signer.address));
    try {
      await signer.provider.call({ to: contract, from: signer.address, data, value: 0 });
      return fn;
    } catch (e) {
      if (e.data && e.data !== '0x') return fn;  // function exists but needs payment
      continue;
    }
  }
  throw new Error('no recognized mint function');
}
```

---

## Step 3 — Detect price

```js
const PRICE_READERS = [
  'function mintPrice() view returns (uint256)',
  'function price() view returns (uint256)',
  'function cost() view returns (uint256)',
  'function PRICE() view returns (uint256)',
  'function publicSalePrice() view returns (uint256)',
];

async function detectPrice(contract, provider, amount = 1) {
  for (const sig of PRICE_READERS) {
    try {
      const c = new ethers.Contract(contract, [sig], provider);
      const fnName = sig.match(/function (\w+)/)[1];
      const p = await c[fnName]();
      return p * BigInt(amount);
    } catch { continue; }
  }
  return 0n;  // free mint or seadrop
}
```

---

## Step 4 — Auto gas

```js
async function autoGas(provider, txRequest) {
  const feeData = await provider.getFeeData();
  let gasLimit;
  try {
    gasLimit = await provider.estimateGas(txRequest);
    gasLimit = gasLimit * 120n / 100n;  // +20% buffer
  } catch (e) {
    throw new Error(`gas estimate failed (likely revert): ${e.shortMessage || e.message}`);
  }

  const priorityFee = feeData.maxPriorityFeePerGas
    ? feeData.maxPriorityFeePerGas * 110n / 100n
    : ethers.parseUnits('1.5', 'gwei');

  const baseFee = feeData.gasPrice ?? feeData.maxFeePerGas;
  const maxFee = (baseFee * 2n) + priorityFee;

  return { gasLimit, maxPriorityFeePerGas: priorityFee, maxFeePerGas: maxFee };
}
```

---

## Step 5 — One-shot CLI

```js
// mint.js
import { ethers } from 'ethers';
import 'dotenv/config';

const RPCS = {
  ethereum: process.env.RPC_ETH || 'https://eth.llamarpc.com',
  base: process.env.RPC_BASE || 'https://mainnet.base.org',
  polygon: process.env.RPC_POLYGON || 'https://polygon-rpc.com',
  arbitrum: process.env.RPC_ARB || 'https://arb1.arbitrum.io/rpc',
  optimism: process.env.RPC_OP || 'https://mainnet.optimism.io',
  'zora-network': process.env.RPC_ZORA || 'https://rpc.zora.energy',
};

async function main() {
  const input = process.argv.slice(2).join(' ');
  if (!input) { console.error('usage: node mint.js <url|contract> [chain] [amount]'); process.exit(1); }

  const target = parseTarget(input);
  if (target.source === 'opensea_slug') {
    const r = await fetch(`https://api.opensea.io/api/v2/collections/${target.slug}`,
      { headers: { 'x-api-key': process.env.OPENSEA_KEY } });
    const j = await r.json();
    target.contract = j.contracts[0].address;
    target.chain = j.contracts[0].chain;
  }

  const provider = new ethers.JsonRpcProvider(RPCS[target.chain]);
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
  const result = await mintOne(target, wallet);

  console.log(`\n[${result.status.toUpperCase()}] ${target.contract} on ${target.chain}`);
  console.log(`hash:    ${result.hash}`);
  console.log(`gasUsed: ${result.gasUsed}`);
  console.log(`view:    ${result.explorer}`);
}

main().catch(e => { console.error(`[FAIL] ${e.message}`); process.exit(1); });
```

---

## Mass mint with N wallets (combo with batch-parallel-execution)

```js
import pLimit from 'p-limit';

const wallets = JSON.parse(fs.readFileSync('wallets.json'))
  .map(w => new ethers.Wallet(w.pk));

const target = parseTarget(process.argv[2]);
const limit = pLimit(5);

const tasks = wallets.map(w => limit(async () => {
  try { return await mintOne(target, w); }
  catch (e) { return { wallet: w.address, error: e.message }; }
}));

const results = await Promise.allSettled(tasks);
const ok = results.filter(r => r.value?.status === 'success').length;
console.log(`[DONE] ${ok}/${wallets.length} minted`);
fs.writeFileSync(`mint-${Date.now()}.json`, JSON.stringify(results, null, 2));
```

---

## Special Protocols

### OpenSea Seadrop

```js
const SEADROP = '0x00005EA00Ac477B1030CE78506496e8C2dE24bf5';
const abi = ['function mintPublic(address nftContract, address feeRecipient, address minterIfNotPayer, uint256 quantity) payable'];
const seadrop = new ethers.Contract(SEADROP, abi, signer);

// Get fee recipient from drop config
const cfgAbi = ['function getPublicDrop(address) view returns (tuple(uint80 mintPrice, uint48 startTime, uint48 endTime, uint16 maxTotalMintableByWallet, uint16 feeBps, bool restrictFeeRecipients))'];
const cfg = new ethers.Contract(SEADROP, cfgAbi, provider);
const drop = await cfg.getPublicDrop(nftContract);
const price = drop.mintPrice * BigInt(quantity);

const feeRecipientAbi = ['function getAllowedFeeRecipients(address) view returns (address[])'];
const fr = new ethers.Contract(SEADROP, feeRecipientAbi, provider);
const allowed = await fr.getAllowedFeeRecipients(nftContract);
await seadrop.mintPublic(nftContract, allowed[0], ethers.ZeroAddress, quantity, { value: price });
```

### Manifold Claims

```js
const MANIFOLD = '0x44e94034afce2dd3cd5eb62528f239686fc8f162';
const abi = ['function mint(address creatorContractAddress, uint256 instanceId, uint32 mintIndex, bytes32[] merkleProof, address mintFor) payable'];
// instanceId from URL → API call
const url = `https://apps.api.manifoldxyz.dev/public/instance/data?id=${claimId}`;
const meta = await (await fetch(url)).json();
// extract creatorContractAddress, publicData.instanceId, cost
```

### Zora 1155

```js
const ZORA_MINTER = '0x777777722D078c97c6ad07d9f36801e653E356Ae';
const abi = ['function mintWithRewards(address minter, uint256 tokenId, uint256 quantity, bytes minterArguments, address mintReferral) payable'];
const minterArgs = ethers.AbiCoder.defaultAbiCoder().encode(['address'], [signer.address]);
const mintFee = ethers.parseEther('0.000111');  // Zora protocol fee per mint
await contract.mintWithRewards(ZORA_MINTER, tokenId, quantity, minterArgs, ethers.ZeroAddress, { value: mintFee * BigInt(quantity) });
```

---

## Output Format

```
[TARGET] 0xABC... on base × 3
[FN]     mintPublic(uint256) — detected
[PRICE]  0.0042 ETH (0.0014 × 3)
[GAS]    180k @ 0.05 gwei  →  ~$0.02
[SENT]   0xtxhash...
[OK]     block 12345678  gasUsed 142,330
[VIEW]   https://basescan.org/tx/0xtxhash...
```

---

## Common Failure Modes

- `execution reverted: NotEnabled` → public mint not active yet, check `saleActive()` or wait
- `InsufficientFunds` → price miscalculated, retry with verbose price detection
- `AlreadyMinted` → wallet hit per-wallet cap, switch wallet
- `InvalidMerkleProof` → allowlist-only, public mint not started
- `revert no reason` → custom mint flow (Sound, Foundation) → manual ABI inspection needed
