module.exports = {
    // Network Configuration — EDIT THESE
    RPC_URL: 'https://sepolia-rpc.example.io',
    CHAIN_ID: 12345,
    EXPLORER: 'https://explorer.example.io',
    
    // Faucets
    FAUCET_URL: 'https://faucet.example.io/',
    FAUCET_API: '', // If API available
    
    // Key Contracts — EDIT THESE
    WETH: '0x4200000000000000000000000000000000000006', // Standard on OP Stack
    MULTICALL3: '0xcA11bde05977b3631167028862bE2a173976CA11', // Standard
    TOKEN_CONTRACT: '', // Protocol-specific token
    TOKEN_FAUCET: '', // Protocol-specific faucet
    NAME_REGISTRY: '', // Protocol-specific name service
    
    // Timing (adjust based on chain speed and rate limits)
    DELAY_BETWEEN_WALLETS_MS: 3000,
    DELAY_BETWEEN_TX_MS: 2000,
    
    // Multi-wallet settings
    NUM_WALLETS_TO_GENERATE: 10,
    FUND_AMOUNT_ETH: '0.001', // Amount to send to each sub-wallet
};
