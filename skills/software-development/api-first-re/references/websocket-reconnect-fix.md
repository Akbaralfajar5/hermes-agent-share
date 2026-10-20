# WebSocket Bot Reconnect Fix Pattern

## Problem: Reconnect Loop
When a WebSocket bot disconnects and reconnects, common bugs cause infinite reconnect loops:
1. **Socket leak** — new socket created per reconnect without closing old one
2. **Duplicate reconnect timers** — multiple disconnect events fire multiple `startBot()`
3. **No exponential backoff** — server kicks bot, bot reconnects immediately, server kicks again

## Fix Pattern (Node.js)
```javascript
let activeSocket = null;
let reconnectAttempts = 0;

async function startBot() {
  // CRITICAL: Close previous socket before creating new one
  if(activeSocket) {
    activeSocket.removeAllListeners();
    activeSocket.disconnect();
    activeSocket = null;
  }
  
  // Exponential backoff: 30s, 60s, 120s, 240s, max 300s
  const backoffDelay = Math.min(30000 * Math.pow(2, reconnectAttempts), 300000);
  if(reconnectAttempts > 0) {
    log(`Backoff: waiting ${backoffDelay/1000}s`);
    await new Promise(r => setTimeout(r, backoffDelay));
  }
  
  const socket = io(url, { 
    auth: { token }, 
    transports: ['websocket'], 
    reconnection: false  // CRITICAL: disable auto-reconnect, handle manually
  });
  activeSocket = socket;
  
  socket.on('connect', () => {
    reconnectAttempts = 0; // Reset on success
  });
  
  socket.on('disconnect', (reason) => {
    reconnectAttempts++;
    if(!disconnectTimer) {
      const delay = reason === 'io server disconnect' ? 5000 : 30000;
      disconnectTimer = setTimeout(() => { 
        disconnectTimer = null;
        startBot(); 
      }, delay);
    }
  });
}
```

## Key Points
1. **`reconnection: false`** — disable socket.io auto-reconnect, handle manually
2. **`removeAllListeners()` + `disconnect()`** — clean up old socket before new one
3. **`reconnectAttempts` counter** — exponential backoff only increases, resets on success
4. **Guard duplicate timers** — `if(!disconnectTimer)` prevents multiple timers
5. **Different delay per reason** — `io server disconnect` = server kicked (short delay), `transport close` = network issue (longer delay)
6. **Log disconnect reason** — helps debug ban vs network vs server restart

## Signs of Ban vs Network Issue
- `io server disconnect` repeated rapidly → server banning/kicking
- `transport close` intermittently → normal network hiccups
- Auth fails with `BANNED` → wallet/account banned, stop reconnecting
