# API Response Formats

## Schedule Endpoint
```
GET https://unixpunks.xyz/api/schedule
```

Response:
```json
{
  "activeBatch": 4,
  "windows": [
    {
      "batch": 1,
      "startIso": "2026-05-12T16:07:18.000Z",
      "endIso": "2026-05-15T06:43:15.580Z",
      "tsRangeStart": 1498176000,
      "tsRangeEnd": 1498185999,
      "timestampsCount": 1111,
      "consumedCount": 1084,
      "soldOut": false
    }
  ]
}
```

## Find MintCode Endpoint
```
POST https://unixpunks.xyz/api/find-mint-code
Content-Type: application/json

{"timestamp": 1498206500, "wallet": "0x..."}
```

### Success Response
```json
{"ok": true, "mintCode": "0xa3207e2a63a59d386cd0bd8e7074eadd8d8a432494131ecde84bf7bbf6dde1fd"}
```

### Error Responses
```json
{"ok": false, "error": "invalid_timestamp"}
{"ok": false, "error": "rate_limit", "retryInMs": 9700}
{"ok": false, "error": "batch_not_active"}
{"ok": false, "error": "already_claimed"}
```

## Rate Limit Behavior

- **Limit**: ~10 seconds per IP address
- **Response**: Returns `retryInMs` field with exact wait time
- **Bypass**: Use rotating residential proxy (each request = new IP)

## Mint Transaction

Contract: `0x9E464d954E07abeD84081F399feE729FF99f8f93`

Function signature:
```solidity
function mint(bytes32 mintCode) external payable
```

- Value: 0.001111 ETH
- Gas limit: 150000-200000
- Reverts if mintCode already claimed
