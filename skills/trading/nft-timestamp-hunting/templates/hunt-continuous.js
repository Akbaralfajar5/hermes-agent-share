const { ethers } = require('ethers');
const { HttpsProxyAgent } = require('https-proxy-agent');

// === CONFIG ===
const PRIVATE_KEY = 'YOUR_PRIVATE_KEY';
const WALLET = 'YOUR_WALLET_ADDRESS';
const CONTRACT = '0x9E464d954E07abeD84081F399feE729FF99f8f93';
const PROXY = 'http://user:pass@gw.dataimpulse.com:823'; // Optional

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function findMintCode(ts) {
  const res = await fetch('https://unixpunks.xyz/api/find-mint-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timestamp: ts, wallet: WALLET })
  });
  return res.json();
}

async function getSchedule() {
  const res = await fetch('https://unixpunks.xyz/api/schedule');
  return res.json();
}

async function hunt(start, end) {
  const tried = new Set();
  let attempts = 0;
  
  while (attempts < 500) {
    const ts = start + Math.floor(Math.random() * (end - start + 1));
    if (tried.has(ts)) continue;
    tried.add(ts);
    attempts++;
    
    try {
      const result = await findMintCode(ts);
      
      if (result.ok && result.mintCode) {
        console.log(`\n🎯 HIT! ts=${ts}`);
        console.log(`MintCode: ${result.mintCode}`);
        return result.mintCode;
      }
      
      if (result.error === 'rate_limit') {
        const wait = result.retryInMs || 10000;
        console.log(`[${attempts}] Rate limit, wait ${Math.round(wait/1000)}s`);
        await sleep(wait);
        tried.delete(ts);
        attempts--;
        continue;
      }
      
      if (attempts % 5 === 0) console.log(`[${attempts}] ts=${ts} -> ${result.error || 'miss'}`);
    } catch (e) {}
    
    await sleep(100);
  }
  return null;
}

async function mint(mintCode) {
  // Use proxy for RPC if needed
  // const agent = new HttpsProxyAgent(PROXY);
  // const provider = new ethers.JsonRpcProvider('https://eth.llamarpc.com', undefined, { fetchOptions: { agent } });
  
  const provider = new ethers.JsonRpcProvider('https://1rpc.io/eth');
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT, [
    'function mint(bytes32 mintCode) external payable'
  ], wallet);
  
  console.log('📝 Minting...');
  const tx = await contract.mint(mintCode, {
    value: ethers.parseEther('0.001111'),
    gasLimit: 200000
  });
  console.log(`TX: ${tx.hash}`);
  const receipt = await tx.wait();
  console.log(`✅ MINTED! Block ${receipt.blockNumber}`);
  return receipt;
}

async function main() {
  console.log('🚀 CPUNKS Continuous Hunter');
  console.log(`Wallet: ${WALLET}\n`);
  
  let minted = false;
  
  while (!minted) {
    try {
      const schedule = await getSchedule();
      
      // Find active batch with slots
      let batch = null;
      if (schedule.activeBatch) {
        batch = schedule.windows.find(w => w.batch === schedule.activeBatch);
        if (batch && batch.consumedCount >= batch.timestampsCount) {
          batch = null; // Sold out
        }
      }
      
      if (batch) {
        console.log(`\n🟢 BATCH ${batch.batch} LIVE`);
        console.log(`Claimed: ${batch.consumedCount}/${batch.timestampsCount}`);
        
        const mintCode = await hunt(batch.tsRangeStart, batch.tsRangeEnd);
        if (mintCode) {
          try {
            await mint(mintCode);
            console.log('\n🎉 SUCCESS! NFT MINTED!');
            minted = true;
          } catch (e) {
            console.log(`❌ Mint failed: ${e.message.slice(0,100)}`);
            console.log('Retrying hunt...');
          }
        } else {
          console.log('No hit, retrying...');
        }
      } else {
        // Wait for next batch
        const nextBatch = schedule.windows.find(w => w.consumedCount < w.timestampsCount);
        if (nextBatch) {
          const diff = Math.max(0, Math.floor((new Date(nextBatch.startIso) - Date.now()) / 1000));
          console.log(`Waiting for Batch ${nextBatch.batch} in ${diff}s...`);
          await sleep(Math.min(diff * 1000, 30000));
        } else {
          console.log('All batches sold out!');
          break;
        }
      }
    } catch (e) {
      console.log(`Error: ${e.message.slice(0,50)}`);
      await sleep(5000);
    }
  }
}

main().catch(console.error);
