---
name: ethers-js
cluster: blockchain
description: "JavaScript/TypeScript libraries for Ethereum blockchain interaction — ethers.js (v5/v6) and viem. Covers wallet management, smart contract calls, EIP-7702 delegation, and multi-wallet operations."
tags: ["ethereum","javascript","typescript","blockchain","viem","ethers"]
dependencies: []
composes: []
similar_to: []
called_by: []
authorization_required: false
scope: general
model_hint: claude-sonnet
embedding_hint: "ethereum javascript typescript blockchain smart contracts wallets transactions viem ethers EIP-7702"
---

# ethers-js

## Purpose
Ethers.js is a JavaScript library for interacting with the Ethereum blockchain, enabling developers to manage wallets, sign transactions, and call smart contracts programmatically. It abstracts low-level Ethereum APIs for easier integration in web and Node.js applications.

## When to Use
Use ethers.js when building Ethereum-based dApps that require wallet operations, transaction handling, or smart contract interactions in JavaScript environments. It's ideal for projects needing a lightweight alternative to Web3.js, especially for browser-based or server-side Ethereum scripting.

## Key Capabilities
- Wallet management: Create, import, and derive wallets using mnemonic phrases or private keys.
- Provider support: Connect to Ethereum nodes via HTTP, WebSocket, or third-party services like Infura.
- Transaction handling: Sign and send transactions, including gas estimation and nonce management.
- Smart contract interactions: Read and write to contracts using ABI definitions, with support for events and multicall.
- Utility functions: Encode/decode data, handle big numbers, and compute hashes for Ethereum-specific tasks.

## Usage Patterns
Always import ethers.js as a module in your JavaScript file. Initialize a provider first, then create a wallet or signer. For asynchronous operations, use async/await patterns. Set up error catching around all blockchain calls to handle network failures. Use environment variables for sensitive data like private keys (e.g., `process.env.PRIVATE_KEY`).

## Common Commands/API (ethers v6)

> **IMPORTANT:** ethers v6 has breaking changes from v5. Use `ethers.JsonRpcProvider` (not `ethers.providers.JsonRpcProvider`), `ethers.parseEther` (not `ethers.utils.parseEther`), `ethers.formatEther` (not `ethers.utils.formatEther`). BigInt is native (no more BigNumber class).

- Create a wallet:
  ```javascript
  const { ethers } = require('ethers');
  const wallet = ethers.Wallet.createRandom();
  console.log(wallet.address, wallet.privateKey, wallet.mnemonic.phrase);
  ```
- Connect to a provider:
  ```javascript
  const provider = new ethers.JsonRpcProvider('https://rpc-url.example.com');
  const network = await provider.getNetwork();
  console.log('Chain ID:', network.chainId.toString());
  ```
- Call a smart contract:
  ```javascript
  const contract = new ethers.Contract(address, abi, signerOrProvider);
  const result = await contract.functionName(arg1);
  ```
- Sign and send a transaction:
  ```javascript
  const wallet = new ethers.Wallet(privateKey, provider);
  const tx = await wallet.sendTransaction({ to: '0xAddress', value: ethers.parseEther('1.0') });
  const receipt = await tx.wait();
  ```
- Get balance:
  ```javascript
  const balance = await provider.getBalance(address);
  console.log(ethers.formatEther(balance), 'ETH'); // balance is BigInt
  ```
- Deploy a contract:
  ```javascript
  const tx = await wallet.sendTransaction({ data: bytecode });
  const receipt = await tx.wait();
  console.log('Deployed at:', receipt.contractAddress);
  ```

### v5 → v6 Migration Cheatsheet
| v5 | v6 |
|----|-----|
| `ethers.providers.JsonRpcProvider` | `ethers.JsonRpcProvider` |
| `ethers.utils.parseEther('1.0')` | `ethers.parseEther('1.0')` |
| `ethers.utils.formatEther(bn)` | `ethers.formatEther(bigint)` |
| `ethers.utils.formatUnits(bn, 'gwei')` | `ethers.formatUnits(bigint, 'gwei')` |
| `ethers.BigNumber.from(x)` | Native `BigInt(x)` or `0n` |
| `bn.eq(0)` | `bigint === 0n` |
| `ethers.utils.getAddress(addr)` | `ethers.getAddress(addr)` |
| `new ethers.providers.Web3Provider(window.ethereum)` | `new ethers.BrowserProvider(window.ethereum)` |

## Provider Pitfalls

### staticNetwork: true — required for some RPC providers
Some providers (dRPC, certain Ankr endpoints) return HTTP 500 when ethers.js auto-detects the network via `eth_chainId`. Fix:

```javascript
// WRONG — causes "server response 500 Internal Server Error" on some providers:
new ethers.JsonRpcProvider(RPC_URL)

// CORRECT — skip network auto-detection, hardcode chain:
new ethers.JsonRpcProvider(RPC_URL, 1, { staticNetwork: true })
// Second arg: chain ID (1 = mainnet). Third arg: options.
```

Diagnosis: if `curl -X POST RPC_URL -d '{"method":"eth_blockNumber",...}'` works but ethers.js throws 500, it's the network detection call failing. `staticNetwork: true` bypasses it.

**RPC reliability from cloud VPS (Vast.ai, RunPod, etc.):**
- Alchemy free tier (`https://eth-mainnet.g.alchemy.com/v2/KEY`) — most reliable from cloud IPs
- Infura free tier — good fallback
- dRPC (`lb.drpc.live`) — may return 500 from datacenter IPs even when curl works; `staticNetwork: true` alone may not fix it if the provider is actively blocking the IP
- publicnode/llamarpc — unreliable for `eth_call`, OK for basic queries

### PRIVATE_KEY env var — must be set before process starts
`process.env.PRIVATE_KEY` is read at module load time. Setting it in `.env` file requires `dotenv` package. Without dotenv, pass via shell:
```bash
PRIVATE_KEY=0x... RPC_URL=https://... node script.js
```
NOT via `export` in a separate command before `node` — that works in interactive shell but not in `screen` or `nohup` wrappers unless exported in the same command.

## Integration Notes
Integrate ethers.js into Node.js projects by installing via npm: `npm install ethers`. For browser use, include via a CDN or bundle with Webpack. If using third-party providers like Infura, set the API key in an environment variable (e.g., `$INFURA_API_KEY`) and pass it to the provider URL. Handle Web3 compatibility by using ethers.js's `Web3Provider` wrapper if needed. For testing, use Hardhat or Ganache and connect with a local provider like `new ethers.providers.JsonRpcProvider('http://localhost:8545')`.

## Error Handling
Wrap all ethers.js calls in try/catch blocks to handle common errors like network issues or invalid inputs. Check for specific error types, such as `ethers.errors.ServerError` for provider failures. Use `provider.on('error', handler)` for event-based error listening. Example:
```javascript
try {
  await provider.getBlockNumber();
} catch (error) {
  if (error.code === 'SERVER_ERROR') console.error('Network issue:', error.message);
}
```
Always validate inputs before operations, like ensuring addresses are checksummed with `ethers.utils.getAddress(address)`.

## Concrete Usage Examples
1. **Generate and fund a wallet (v6):**
   ```javascript
   const { ethers } = require('ethers');
   const wallet = ethers.Wallet.createRandom();
   const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
   const connected = wallet.connect(provider);
   console.log('Address:', wallet.address);
   const balance = await provider.getBalance(wallet.address);
   console.log('Balance:', ethers.formatEther(balance));
   ```

2. **Interact with an ERC-20 token contract (v6):**
   ```javascript
   const { ethers } = require('ethers');
   const abi = ['function balanceOf(address) view returns (uint256)', 'function transfer(address to, uint256 amount) returns (bool)'];
   const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
   const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
   const contract = new ethers.Contract('0xTokenAddress', abi, wallet);
   const balance = await contract.balanceOf(wallet.address);
   const tx = await contract.transfer('0xRecipient', ethers.parseUnits('10', 18));
   await tx.wait();
   ```

3. **Multi-wallet batch operations:**
   ```javascript
   const wallets = JSON.parse(fs.readFileSync('./wallets.json'));
   for (const w of wallets) {
       const signer = new ethers.Wallet(w.privateKey, provider);
       const tx = await signer.sendTransaction({ to: target, value: ethers.parseEther('0.001') });
       await tx.wait();
   }
   ```

## Viem (Modern Alternative)

**Viem** is a modern TypeScript-first Ethereum library that's becoming the standard for new projects. It's faster, smaller, and has better TypeScript support than ethers.js.

### When to Use Viem vs Ethers
- **Use viem:** New projects, TypeScript-first codebases, need tree-shaking, want modern patterns (separate clients for read/write)
- **Use ethers:** Existing ethers codebase, need v5 compatibility, prefer unified wallet/provider pattern

### Key Differences
| Feature | ethers.js v6 | viem |
|---------|-------------|------|
| Bundle size | ~116 KB | ~30 KB (tree-shakeable) |
| TypeScript | Good | Excellent (built-in) |
| Pattern | Unified provider/signer | Separate public/wallet clients |
| BigInt | Native | Native |
| Chain config | Manual | Built-in chain objects |

### Viem Patterns

**Install:**
```bash
npm install viem
```

**Create wallet:**
```javascript
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts';

const privateKey = generatePrivateKey();
const account = privateKeyToAccount(privateKey);
console.log(account.address, privateKey);
```

**Connect to provider (read-only):**
```javascript
import { createPublicClient, http } from 'viem';
import { mainnet } from 'viem/chains';

const publicClient = createPublicClient({
  chain: mainnet,
  transport: http('https://rpc-url.example.com')
});

const blockNumber = await publicClient.getBlockNumber();
const balance = await publicClient.getBalance({ address: '0x...' });
```

**Send transaction (write):**
```javascript
import { createWalletClient, http, parseEther } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { mainnet } from 'viem/chains';

const account = privateKeyToAccount('0x...');
const walletClient = createWalletClient({
  account,
  chain: mainnet,
  transport: http('https://rpc-url.example.com')
});

const hash = await walletClient.sendTransaction({
  to: '0x...',
  value: parseEther('1.0')
});

// Wait for confirmation
const receipt = await publicClient.waitForTransactionReceipt({ hash });
```

**Contract interaction:**
```javascript
import { createPublicClient, createWalletClient, http, getContract } from 'viem';

const publicClient = createPublicClient({ chain, transport: http(rpcUrl) });
const walletClient = createWalletClient({ account, chain, transport: http(rpcUrl) });

const contract = getContract({
  address: '0x...',
  abi: [...],
  client: { public: publicClient, wallet: walletClient }
});

// Read
const balance = await contract.read.balanceOf([account.address]);

// Write
const hash = await contract.write.transfer(['0xRecipient', parseEther('10')]);
await publicClient.waitForTransactionReceipt({ hash });
```

**EIP-7702 Delegation (Pectra):**
```javascript
import { createWalletClient, createPublicClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

const DELEGATE_CONTRACT = '0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be';
const account = privateKeyToAccount('0x...');

const chain = {
  id: 1,
  name: 'Ethereum',
  rpcUrls: { default: { http: ['https://rpc-url.example.com'] } }
};

const publicClient = createPublicClient({ chain, transport: http(chain.rpcUrls.default.http[0]) });
const walletClient = createWalletClient({ account, chain, transport: http(chain.rpcUrls.default.http[0]) });

// Check if already delegated
const code = await publicClient.getCode({ address: account.address });
if (code && code !== '0x') {
  console.log('Already delegated');
} else {
  // Delegate via EIP-7702
  const hash = await walletClient.sendTransaction({
    to: DELEGATE_CONTRACT,
    value: 0n,
    authorizationList: [{
      contractAddress: DELEGATE_CONTRACT,
      chainId: chain.id,
      nonce: await publicClient.getTransactionCount({ address: account.address })
    }]
  });
  
  await publicClient.waitForTransactionReceipt({ hash });
  console.log('Delegation confirmed:', hash);
}
```

**Multi-wallet operations:**
```javascript
import { readFileSync } from 'fs';
import { createPublicClient, createWalletClient, http, parseEther } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

const wallets = JSON.parse(readFileSync('wallets.json', 'utf-8'));
const publicClient = createPublicClient({ chain, transport: http(rpcUrl) });

for (const w of wallets) {
  const account = privateKeyToAccount(w.privateKey);
  const walletClient = createWalletClient({ account, chain, transport: http(rpcUrl) });
  
  const hash = await walletClient.sendTransaction({
    to: target,
    value: parseEther('0.001')
  });
  
  await publicClient.waitForTransactionReceipt({ hash });
}
```

### Viem Pitfalls
1. **Separate clients** — Unlike ethers where `wallet.sendTransaction()` does everything, viem requires separate `publicClient` (read) and `walletClient` (write). You need BOTH for most operations.
2. **Chain config required** — Viem requires explicit chain config. Use built-in chains (`import { mainnet } from 'viem/chains'`) or define custom chains with `id`, `name`, `rpcUrls`.
3. **No automatic gas estimation** — Unlike ethers, viem doesn't auto-estimate gas for complex operations. Set explicit `gas` parameter if estimation fails.
4. **EIP-7702 support** — Requires Pectra-enabled RPC. Not all providers support it yet (as of 2026).

## Graph Relationships
- Related to cluster: blockchain (e.g., shares connections with other blockchain tools like web3.js, viem).
- Linked by tags: ethereum (e.g., relates to skills for Ethereum development), javascript (e.g., connects to JS-based libraries), blockchain (e.g., associates with general blockchain utilities).
