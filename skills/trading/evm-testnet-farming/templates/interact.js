const { ethers } = require('ethers');
const fs = require('fs');
const config = require('./config');

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const WETH_ABI = [
    'function deposit() payable',
    'function withdraw(uint256 amount)',
    'function balanceOf(address) view returns (uint256)',
];

const ERC20_ABI = [
    'function balanceOf(address) view returns (uint256)',
    'function transfer(address to, uint256 amount) returns (bool)',
    'function name() view returns (string)',
    'function symbol() view returns (string)',
];

// Simple Storage contract bytecode (set/get uint256)
const STORAGE_BYTECODE = '0x608060405234801561001057600080fd5b5060c78061001f6000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c806360fe47b11460375780636d4ce63c146049575b600080fd5b60476042366004606b565b600055565b005b60005460405190815260200160405180910390f35b600060208284031215607c57600080fd5b503591905056fea264697066735822122000000000000000000000000000000000000000000000000000000000000000000064736f6c63430008130033';
const STORAGE_ABI = ['function set(uint256 x)', 'function get() view returns (uint256)'];

async function interact(walletData, provider, allWallets, index) {
    const wallet = new ethers.Wallet(walletData.privateKey, provider);
    const balance = await provider.getBalance(wallet.address);
    
    console.log(`\n[${index + 1}] ${wallet.address} (${ethers.formatEther(balance)} ETH)`);
    
    if (balance === 0n) {
        console.log('   ⚠️ No ETH, skip');
        return { wallet: wallet.address, status: 'skipped' };
    }
    
    const txs = [];
    
    // 1. Self-transfer
    try {
        const tx = await wallet.sendTransaction({ to: wallet.address, value: 0n });
        await tx.wait();
        txs.push({ action: 'self-transfer', hash: tx.hash });
        console.log('   ✅ Self-transfer');
    } catch (e) { console.log('   ❌ Self-transfer:', e.message.slice(0, 60)); }
    await sleep(config.DELAY_BETWEEN_TX_MS);
    
    // 2. Wrap ETH
    try {
        const weth = new ethers.Contract(config.WETH, WETH_ABI, wallet);
        const amt = ethers.parseEther('0.0001');
        const tx = await weth.deposit({ value: amt });
        await tx.wait();
        txs.push({ action: 'wrap', hash: tx.hash });
        console.log('   ✅ Wrap ETH');
        await sleep(config.DELAY_BETWEEN_TX_MS);
        
        // 3. Unwrap
        const tx2 = await weth.withdraw(amt);
        await tx2.wait();
        txs.push({ action: 'unwrap', hash: tx2.hash });
        console.log('   ✅ Unwrap WETH');
    } catch (e) { console.log('   ❌ WETH:', e.message.slice(0, 60)); }
    await sleep(config.DELAY_BETWEEN_TX_MS);
    
    // 4. Deploy contract
    try {
        const tx = await wallet.sendTransaction({ data: STORAGE_BYTECODE });
        const receipt = await tx.wait();
        txs.push({ action: 'deploy', hash: tx.hash, contract: receipt.contractAddress });
        console.log(`   ✅ Deploy: ${receipt.contractAddress}`);
        
        // 5. Interact with it
        await sleep(config.DELAY_BETWEEN_TX_MS);
        const store = new ethers.Contract(receipt.contractAddress, STORAGE_ABI, wallet);
        const tx2 = await store.set(42 + index);
        await tx2.wait();
        txs.push({ action: 'contract-call', hash: tx2.hash });
        console.log('   ✅ Contract interaction');
    } catch (e) { console.log('   ❌ Deploy:', e.message.slice(0, 60)); }
    await sleep(config.DELAY_BETWEEN_TX_MS);
    
    // 6. Transfer to next wallet
    if (allWallets.length > 1 && index < allWallets.length - 1) {
        try {
            const tx = await wallet.sendTransaction({
                to: allWallets[(index + 1) % allWallets.length].address,
                value: ethers.parseEther('0.00001'),
            });
            await tx.wait();
            txs.push({ action: 'transfer', hash: tx.hash });
            console.log('   ✅ Inter-wallet transfer');
        } catch (e) { console.log('   ❌ Transfer:', e.message.slice(0, 60)); }
    }
    
    return { wallet: wallet.address, txs };
}

async function main() {
    const wallets = JSON.parse(fs.readFileSync('./wallets.json', 'utf8'));
    const provider = new ethers.JsonRpcProvider(config.RPC_URL);
    
    console.log(`🚀 Testnet Interaction — ${wallets.length} wallets`);
    console.log(`📡 ${config.RPC_URL} (Chain ${config.CHAIN_ID})`);
    
    const results = [];
    for (let i = 0; i < wallets.length; i++) {
        results.push(await interact(wallets[i], provider, wallets, i));
        await sleep(config.DELAY_BETWEEN_WALLETS_MS);
    }
    
    fs.writeFileSync('./results.json', JSON.stringify(results, null, 2));
    const totalTx = results.reduce((s, r) => s + (r.txs?.length || 0), 0);
    console.log(`\n🎯 Total: ${totalTx} transactions across ${wallets.length} wallets`);
}

main().catch(console.error);
