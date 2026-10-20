/**
 * Arc Agent Mass Registration - Multi-Worker Template
 * 
 * Registers 1000+ AI agents (ERC-8004) on Arc Testnet.
 * Flow per account: generate wallet → solve captcha → claim faucet → register agent
 * 
 * Usage:
 *   npx tsx arc-mass-register.ts --accounts 1000 --workers 10 --proxy-file proxies.txt
 * 
 * Prerequisites:
 *   npm install viem tsx https-proxy-agent socks-proxy-agent node-fetch
 *   Edit TWOCAPTCHA_KEY below
 *   Add proxies to proxies.txt (one per line: socks5://user:pass@host:port)
 * 
 * Key discoveries (May 2026):
 *   - Circle faucet GraphQL: POST https://faucet.circle.com/api/graphql
 *   - Mutation: RequestToken, input: { destinationAddress, blockchain: "ARC", token: "USDC" }
 *   - Auth: reCAPTCHA v2 Enterprise token via "recaptcha-v2-token" header
 *   - v2 sitekey: 6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve
 *   - v3 tokens from 2Captcha are REJECTED (Enterprise assessment too strict)
 *   - ERC-8004 register(string metadataURI) on 0x8004A818BFB912233c491871b3d84c89A494BD9e
 *   - Gas: ~0.006 USDC per tx, 20 USDC faucet = thousands of txs
 * 
 * See ~/arc-agent/mass-register.ts for the full working implementation.
 * See references/arc-testnet.md for complete Arc farming strategy.
 */

// Template structure - see mass-register.ts for full code
// Key constants:
const CONFIG = {
  TWOCAPTCHA_KEY: "YOUR_2CAPTCHA_KEY",
  RECAPTCHA_V2_SITEKEY: "6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve",
  GRAPHQL_URL: "https://faucet.circle.com/api/graphql",
  IDENTITY_REGISTRY: "0x8004A818BFB912233c491871b3d84c89A494BD9e",
  METADATA_URI: "ipfs://bafkreibdi6623n3xpf7ymk62ckb4bo75o3qemwkpfvp5i25j66itxvsoei",
  ARC_CHAIN_ID: 5042002,
  ARC_RPC: "https://rpc.testnet.arc.network",
};

// Worker pattern:
// 1. solveRecaptchaV2() → 2Captcha API (RecaptchaV2TaskProxyless, isEnterprise: true)
// 2. claimFaucet(address, proxy) → GraphQL with "recaptcha-v2-token" header
// 3. registerAgent(privateKey) → viem sendTransaction to IdentityRegistry
// 4. Parse Transfer event for agentId
// 5. Save to results.csv

export { CONFIG };
