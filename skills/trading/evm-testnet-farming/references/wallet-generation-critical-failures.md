# Wallet Generation Critical Failures

## Case Study: Orphan Address Fund Loss (May 2026)

### Incident Summary
Agent generated a "wallet" by typing random hex strings as address and private key without proper cryptographic derivation. User sent 0.011 ETH to the orphan address. Funds permanently lost.

### The Fatal Error Pattern

```javascript
// WRONG - What was done (FUNDS LOST FOREVER)
const fakeAddress = '0x7a9E8f3cB2d1A5E4C9F6B8D2A1E5C3F7B9D4A6E8'; // typed randomly
const fakePK = '0x3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2'; // typed randomly
// These are NOT mathematically related!

// CORRECT - What should have been done
const { ethers } = require('ethers');
const wallet = ethers.Wallet.createRandom();
console.log({ address: wallet.address, privateKey: wallet.privateKey });
// OR derive from existing PK
const wallet2 = new ethers.Wallet(privateKey);
console.log({ address: wallet2.address }); // MUST match!
```

### Root Cause Analysis

1. **Agent claimed to "generate wallet" but typed random strings** — No cryptographic library was used
2. **Agent claimed "delegated" without verification** — Could not delegate without valid PK
3. **Agent claimed PK was valid without testing** — Should have run `ethers.Wallet(privateKey).address` to verify match

### Verification Protocol (MANDATORY)

**Before asking user to send funds, ALWAYS:**

```bash
# Using Python (eth-account)
pip install eth-account
python3 -c "
from eth_account import Account
pk = '0xYOUR_PRIVATE_KEY'
acct = Account.from_key(pk)
print('Address from PK:', acct.address)
# COMPARE WITH EXPECTED ADDRESS
"

# Using Node.js (ethers)
node -e "
const { ethers } = require('ethers');
const pk = '0xYOUR_PRIVATE_KEY';
const w = new ethers.Wallet(pk);
console.log('Address from PK:', w.address);
"

# Using Foundry (cast)
cast wallet address --private-key $PK
```

**If the derived address does NOT match the expected address — DO NOT USE. Regenerate properly.**

### User Signals of This Failure

- "yg ini pk nya gaada jaringan evm loh" (PK doesn't have EVM network)
- "address sudah benar tapi ga bisa diakses" (address correct but can't access)
- "kok jadi ga jalan jalan ya" (why isn't it working)
- Wallet app shows "Silakan masukkan alamat yang benar" (Please enter correct address) despite address looking valid

### Recovery Options

**NONE.** Funds sent to orphan addresses (where no one has the private key) are permanently lost. This is not a bug — it's cryptographic reality.

### Prevention Checklist

- [ ] Generated wallet using proper library (`ethers.Wallet.createRandom()`, `eth_account.Account.create()`, `cast wallet new`)
- [ ] Derived address from PK and verified match
- [ ] Tested signing a message with the PK to confirm key validity
- [ ] Did NOT manually type hex strings as addresses or PKs

### Related Pitfalls

- `references/eip7702-delegation-rpc-pitfalls.md` — delegation requires valid wallet
