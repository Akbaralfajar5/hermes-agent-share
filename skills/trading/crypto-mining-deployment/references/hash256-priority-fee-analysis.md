# $HASH Mining — Priority Fee & Competition Analysis (May 2026)

## Real On-Chain Data (blocks 25070060–25070075)

Sampled from Ethereum mainnet, contract `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc`.

### Distribution of priority fees used by successful miners

| Tier | Range | Notes |
|------|-------|-------|
| Top | 15–38 gwei | Gets first slots, wastes gas |
| Mid | 5–15 gwei | Reliable inclusion |
| Sweet spot | 3–5 gwei | Best ROI — consistently included |
| Low | 0.2–3 gwei | Still gets in when block not full |
| Zero | 0.0 gwei | Occasionally included |

### Notable patterns

- `0xdee4534273` — multi-wallet farmer, uses **0.2 gwei**, gets included in almost every block (10–15 TXs per block from this address cluster)
- `0xf7a53279ac` + `0xda528d1529` — consistent **3 gwei**, appear in nearly every block
- Top miner `0xa046e04915` — used **38 gwei** once, got first slot
- Block 25070063 had 21 mine TXs — only 10 valid (10/block limit)

### Conclusion

**Use 3–5 gwei** for optimal ROI. 25 gwei is overkill — the 10 mints/block limit means TX reverts are due to competition, not low fee. Raising fee above 5 gwei doesn't meaningfully improve inclusion rate but significantly increases gas cost per mint.

At 25 gwei: ~$5.24/mint → break-even HASH > $0.052
At 3 gwei: ~$0.63/mint → break-even HASH > $0.0063

## Query Script

```bash
# Check current competition from any machine with curl + python3
CONTRACT="0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc"
RPC="https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"

for block_num in $(seq $(($(curl -s -X POST $RPC -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | python3 -c "import json,sys; print(int(json.load(sys.stdin)['result'],16))") - 5)) $(($(curl -s -X POST $RPC -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | python3 -c "import json,sys; print(int(json.load(sys.stdin)['result'],16))"))); do
  curl -s -X POST "$RPC" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf '0x%x' $block_num)\",true],\"id\":1}" | \
    python3 -c "
import json,sys
data=json.load(sys.stdin)
block=data.get('result')
if not block: sys.exit()
CONTRACT='$CONTRACT'
txs=[tx for tx in block['transactions'] if tx.get('to') and tx['to'].lower()==CONTRACT]
if txs:
    print(f'Block {int(block[\"number\"],16)}: {len(txs)} mine txs')
    for tx in txs:
        pf=int(tx.get('maxPriorityFeePerGas') or '0x0',16)/1e9
        gp=int(tx.get('gasPrice') or '0x0',16)/1e9
        print(f'  {tx[\"from\"][:12]} priority={pf:.1f}gwei total={gp:.1f}gwei')
" 2>/dev/null
done
```

## SSH Pitfalls on Vast.ai

### SSH drops after pkill

When you `pkill -f "node miner"` or `pkill -f hash-miner-v4`, the SSH session often drops immediately (exit code 255). This is because the miner process was holding the SSH session open somehow, or the kill signal propagates to the SSH process.

**Workaround:** Write a restart script to a file first, then execute it in background:
```bash
# Step 1: Write script
ssh user@host 'cat > /tmp/restart.sh << SCRIPT
#!/bin/bash
pkill -f "node miner" 2>/dev/null
pkill -f hash-miner-v4 2>/dev/null
sleep 3
cd /root/hash-miner
screen -dmS hash-gpu bash -c "PRIVATE_KEY=0x... RPC_URL=https://... node miner-gpu-v3.js >> miner-gpu.log 2>&1"
SCRIPT
chmod +x /tmp/restart.sh && echo written'

# Step 2: Execute via `at now` (more reliable than & background)
ssh user@host 'at now < /tmp/restart.sh'

# Step 3: Wait and verify
sleep 15
ssh user@host 'tail -10 /root/hash-miner/miner-gpu.log && screen -list'
```

**Alternative — single command with `nohup` (if `at` not available):**
```bash
# Pass env vars inline to screen, NOT via .env file
ssh user@host 'screen -dmS hash-gpu bash -c "cd /root/hash-miner && PRIVATE_KEY=0x... RPC_URL=https://... node miner-gpu-v3.js >> miner-gpu.log 2>&1" && echo started'
```

**Key insight:** Always pass `PRIVATE_KEY` and `RPC_URL` **inline** in the screen command, not via `.env` file. Node.js does not auto-load `.env` — requires `dotenv` package. Inline env vars in the screen command are the most reliable approach.

### Multiple stale screen sessions

After SSH drops mid-restart, you may end up with multiple `hash-gpu` screen sessions running old code. Always check with `screen -list` and kill all before starting fresh:
```bash
screen -ls | grep hash-gpu | awk '{print $1}' | xargs -I{} screen -S {} -X quit 2>/dev/null
```
