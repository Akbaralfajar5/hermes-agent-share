---
name: superagent-contract
description: Smart contract tools — universal reader (multi-chain), writer (governor-gated), deploy engine (Foundry), CREATE2. SUPERAGENT v4.0 H8-H10.
---

# superagent-contract — Smart Contract Tools

Universal contract read/write/deploy. ABI auto-fetch dari Sourcify/Blockscout (keyless).

Scripts: `~/superagent-v4/skills/hermes/scripts/{contract_reader,contract_writer,deploy_engine,browser_engine}.py`
References: `~/superagent-v4/skills/hermes/references/{contract_read,contract_write,deploy,browser}.md`

## 1. Contract Reader (Read-Only — No Governor)

Multi-chain, resolve proxy (EIP-1967), deteksi ERC-20/721/1155.

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/superagent-v4/skills/hermes/scripts"))
from contract_reader import ContractReader

reader = ContractReader(rpc_url=os.environ.get("RPC_EVM_ETHEREUM", "https://eth.llamarpc.com"))
info = reader.read("0x...contract...")  # auto-fetch ABI, detect type
print(info.name, info.symbol, info.decimals)  # for ERC-20
print(reader.call("balanceOf", owner="0x...user..."))
```

## 2. Contract Writer (Governor-Gated)

Kirim tx ke fungsi apa pun — sim → screen → governor → konfirmasi.

```python
from contract_writer import ContractWriter
writer = ContractWriter(
    rpc_url=os.environ["RPC_EVM_ETHEREUM"],
    private_key=os.environ["PRIVATE_KEY"],
    governor_db=os.environ.get("HERMES_GOVERNOR_DB", "~/.hermes/governor.db")
)
tx = await writer.write("0x...contract...", "transfer", args=("0x...to...", 1000))
print(tx.hash)
```

**Gates**: simulation → gas guard → spend cap → slippage → kill-switch → user confirm.

## 3. Deploy Engine (Foundry — Governor-Gated)

Compile, test, deploy, verify smart contracts.

```bash
# Prasyarat
curl -L https://foundry.paradigm.xyz | bash && foundryup
# Butuh juga: HERMES_MASTER_PW, RPC_EVM_*, ETHERSCAN_API_KEY (opsional buat verify)
```

```python
from deploy_engine import DeployEngine
engine = DeployEngine(
    private_key=os.environ["PRIVATE_KEY"],
    rpc_url=os.environ["RPC_EVM_BASE"],
    governor_db=os.environ.get("HERMES_GOVERNOR_DB")
)
# Compile + test
result = engine.compile_and_test("/path/to/project")
print(result.test_results)

# Deploy
addr = engine.deploy("/path/to/project", constructor_args=("MyToken", "MTK"))
print(f"Deployed: {addr}")

# Verify on Sourcify (keyless) or Etherscan
engine.verify(addr, "/path/to/project")
```

CREATE2 deterministic deploy: `engine.deploy_create2("/path/to/project", salt="0x...")`.

## 4. Browser dApp Automation (H8)

```python
from browser_engine import BrowserEngine
browser = BrowserEngine(
    profile_path=os.environ.get("HERMES_BROWSER_PROFILE", "~/.hermes/browser-profile")
)
await browser.start()
await browser.navigate("https://app.uniswap.org")
await browser.connect_wallet()       # Connect MetaMask/Phantom
await browser.click("#swap-button")
await browser.confirm_metamask()     # Governor-gated sign
```

## Env Vars

```bash
RPC_EVM_ETHEREUM=https://eth.llamarpc.com
RPC_EVM_BASE=https://mainnet.base.org
RPC_SOLANA=https://api.mainnet-beta.solana.com
HERMES_GOVERNOR_DB=~/.hermes/governor.db
HERMES_BROWSER_PROFILE=~/.hermes/browser-profile
PRIVATE_KEY=  # or use wallet_manager
```
