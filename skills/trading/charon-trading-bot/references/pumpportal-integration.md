# PumpPortal Integration — src/signals/pumpportal.js

Complete source for integrating PumpPortal WebSocket into Charon standalone mode.

## Wire into src/app.js

In the standalone mode block (after `startWebsocket()`):

```js
const { startPumpPortal, setPumpPortalCandidateHandler } = await import('./signals/pumpportal.js');
setPumpPortalCandidateHandler(processCandidateFromSignals);
// ...
startPumpPortal();
```

## Full Source: src/signals/pumpportal.js

```js
import WebSocket from 'ws';
import { now } from '../utils.js';
import { activeStrategy } from '../db/settings.js';
import { trending, storeSignalEvent, trendingSignalPass } from './trending.js';
import { graduated } from './graduated.js';

const SOL_PRICE_USD = 150; // rough estimate; used only for mcap filter
const RECONNECT_DELAY_MS = 5000;
const TRADE_TRACK_TTL_MS = 10 * 60 * 1000;

const watchedTokens = new Map(); // mint -> { seenAt, buys, sells, volume, lastMcapSol }
let candidateHandler = null;

export function setPumpPortalCandidateHandler(fn) {
  candidateHandler = fn;
}

function mcapUsd(marketCapSol) {
  return (marketCapSol || 0) * SOL_PRICE_USD;
}

function pruneWatched() {
  const cutoff = now() - TRADE_TRACK_TTL_MS;
  for (const [mint, data] of watchedTokens) {
    if (data.seenAt < cutoff) watchedTokens.delete(mint);
  }
}

async function maybeEmitCandidate(mint, token) {
  if (!candidateHandler) return;
  const strat = activeStrategy();
  const mcap = mcapUsd(token.marketCapSol);
  if (strat.min_mcap_usd > 0 && mcap < strat.min_mcap_usd) return;
  if (strat.max_mcap_usd > 0 && mcap > strat.max_mcap_usd) return;

  const trendingToken = {
    address: mint,
    name: token.name,
    symbol: token.symbol,
    market_cap: mcap,
    price: token.priceUsd || 0,
    volume: token.volumeSol * SOL_PRICE_USD || 0,
    swaps: (token.buys || 0) + (token.sells || 0),
    buys: token.buys || 0,
    sells: token.sells || 0,
    liquidity: token.vSolInBondingCurve * SOL_PRICE_USD || 0,
    holder_count: 0,
    source: 'pumpportal',
    seenAt: now(),
  };

  if (!trendingSignalPass(trendingToken)) return;

  trending.set(mint, trendingToken);
  storeSignalEvent(mint, 'trending', 'pumpportal', trendingToken);

  const graduatedCoin = graduated.get(mint) || null;
  const route = graduatedCoin ? 'graduated_trending' : 'pumpportal_new';

  await candidateHandler({
    mint,
    fee: null,
    signature: token.signature || null,
    graduatedCoin,
    trendingToken,
    route,
  });
}

export function startPumpPortal() {
  let ws;
  let pingTimer;
  const subscribedTrades = new Set();

  function connect() {
    ws = new WebSocket('wss://pumpportal.fun/api/data');

    ws.on('open', () => {
      console.log('[pumpportal] connected');
      ws.send(JSON.stringify({ method: 'subscribeNewToken' }));
      pingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.ping();
      }, 30_000);
    });

    ws.on('message', async (raw) => {
      let msg;
      try { msg = JSON.parse(raw); } catch { return; }

      if (msg.txType === 'create') {
        const mint = msg.mint;
        if (!mint || !String(mint).endsWith('pump')) return;

        pruneWatched();
        watchedTokens.set(mint, {
          seenAt: now(),
          name: msg.name,
          symbol: msg.symbol,
          uri: msg.uri,
          signature: msg.signature,
          traderPublicKey: msg.traderPublicKey,
          marketCapSol: msg.marketCapSol || 0,
          vSolInBondingCurve: msg.vSolInBondingCurve || 0,
          initialBuy: msg.initialBuy || 0,
          buys: msg.initialBuy > 0 ? 1 : 0,
          sells: 0,
          volumeSol: msg.solAmount || 0,
        });

        if (!subscribedTrades.has(mint)) {
          subscribedTrades.add(mint);
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ method: 'subscribeTokenTrade', keys: [mint] }));
          }
        }

        console.log(`[pumpportal] new token: ${msg.symbol} (${mint.slice(0, 8)}...) mcap=$${mcapUsd(msg.marketCapSol).toFixed(0)}`);
        return;
      }

      if ((msg.txType === 'buy' || msg.txType === 'sell') && msg.mint) {
        const mint = msg.mint;
        const token = watchedTokens.get(mint);
        if (!token) return;

        if (msg.txType === 'buy') token.buys = (token.buys || 0) + 1;
        else token.sells = (token.sells || 0) + 1;
        token.volumeSol = (token.volumeSol || 0) + (msg.solAmount || 0);
        token.marketCapSol = msg.marketCapSol || token.marketCapSol;
        token.vSolInBondingCurve = msg.vSolInBondingCurve || token.vSolInBondingCurve;

        const mcap = mcapUsd(token.marketCapSol);
        const strat = activeStrategy();

        if (mcap >= strat.min_mcap_usd && mcap <= strat.max_mcap_usd) {
          const lastEmit = token.lastEmitAt || 0;
          if (now() - lastEmit > 60_000) {
            token.lastEmitAt = now();
            await maybeEmitCandidate(mint, token).catch(err =>
              console.log(`[pumpportal] candidate error: ${err.