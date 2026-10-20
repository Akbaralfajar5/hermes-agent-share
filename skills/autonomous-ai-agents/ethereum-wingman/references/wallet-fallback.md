# Wallet Generation Fallback (No Foundry)

## Overview
When Foundry's `cast` tool is unavailable, generate an EVM wallet using Python with `eth-account`. This produces a BIP-39 mnemonic (12 words) and derives the Ethereum address & private key.

## Prerequisites
- Python 3.9+
- `eth-account` package

## Isolated Environment (Recommended)
To avoid dependency conflicts with system packages, create a virtual environment:

```bash
python3 -m venv /tmp/wallet_venv
source /tmp/wallet_venv/bin/activate  # Windows: venv\Scripts\activate
pip install eth-account
```

## Single-Command Generation
```python
from eth_account import Account
import json

Account.enable_unaudited_hdwallet_features()
acct = Account.create()
print(json.dumps({
    "address": acct.address,
    "private_key": acct.key.hex(),
    "mnemonic": acct._mnemonic
}, indent=2))
```

**Sample output:**
```json
{
  "address": "0xC89F322DC092888975Df76A6d338a33abb401C5B",
  "private_key": "b713f0bcdddecaa3f0621bfcc5b367be74271106dd352e7822deee92e216de94",
  "mnemonic": "between quiz betray rabbit away flash elder crucial suit clerk blue fun"
}
```

**Deterministic derivation from an existing mnemonic:**
```python
from eth_account import Account
Account.enable_unaudited_hdwallet_features()
acct = Account.from_mnemonic("your twelve words here...")
print(f"Address: {acct.address}")
print(f"Private Key: {acct.key.hex()}")
```

## Security Notes
- The mnemonic **IS** the wallet. Store it offline (paper, steel). Never store digitally.
- The private key shown is for export only. For daily use, import into an encrypted keystore once `cast` is available: `cast wallet import -i my-wallet`.
- If you accidentally expose a private key in shell history, clear it: `history -c` and remove `~/.bash_history`.
- Never commit mnemonic or private key to version control.

## Why a Virtual Environment?
Hermes Agent's Python environment contains many packages. Installing `eth-account` globally may cause dependency conflicts (e.g., anthropic version mismatches). An isolated venv prevents this and keeps wallet generation self-contained.

## Limitations
- Development/learning use only. For production, use hardware wallets or `cast` with encrypted keystore.
- `Account.create()` generates a fresh random mnemonic. Use `Account.from_mnemonic()` for deterministic wallets.
- The derivation path is BIP-44 (m/44'/60'/0'/0/0). If you need a different path (e.g., BIP-84 for native segwit), use a dedicated library like `bip-utils`.