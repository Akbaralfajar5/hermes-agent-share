# EQM Protocol Reference

## Contract Addresses

- **Solana Program ID:** `ZKGMUfxiRCXFPnqz9zgqAnuqJy15jk7fKbR4o6FuEQM`
  - Explorer: https://explorer.solana.com/address/ZKGMUfxiRCXFPnqz9zgqAnuqJy15jk7fKbR4o6FuEQM
  - Verified build (OtterSec): https://verify.osec.io/status/ZKGMUfxiRCXFPnqz9zgqAnuqJy15jk7fKbR4o6FuEQM
- **$EQM Token Mint:** `1MhvZzEe8gQ8Rb9CrT3Dn26Gkn9QRErzLMGkkTwveqm`
  - Solscan: https://solscan.io/token/1MhvZzEe8gQ8Rb9CrT3Dn26Gkn9QRErzLMGkkTwveqm
- **Admin pubkey:** `AgbSti5LyTfYHVytBhNP8HHz3Ko7bZfSvnsm9cJAEQM`

## Links

- Website: https://equium.xyz
- Docs: https://equium.xyz/docs
- Browser miner: https://equium.xyz/mine
- Desktop app: https://equium.xyz/download
- X/Twitter: https://x.com/EquiumEQM
- GitHub: https://github.com/HannaPrints/equium

## Equihash (96, 5) Parameters

- Personalization string: `"Equium-v1"` (9 bytes)
- Leaf generation: BLAKE2b, 60-byte output, `ZcashPoW` personalization, n=96, k=5
- Solution validity: `sha256(soln_indices || input_block) < target`
- Wagner algorithm: 5 rounds, 2^17 = 131,072 leaves per nonce attempt
- Memory requirement: ~50MB per solver instance (memory-hard)

## GPU Miner Roadmap

- v0 ✓ GPU BLAKE2b leaf generation
- v0.1 ✓ Hybrid mining loop (current — GPU leaves, CPU Wagner)
- v0.2: First Wagner round on GPU
- v0.3: All 5 Wagner rounds on GPU
- v0.4: WebGPU in browser miner

## Wallet Generated (May 2026)

- Address: `2BiM1SJyZn7a23YwTgap7hWdbGpg9aUYVdRXE7yr6ooT`
- Keypair file: `/tmp/eqm-keypair.json` (64-byte JSON array)
- Needs SOL funding before mining can start
