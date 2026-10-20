# rpow2 Balance API

## Check Balance

**Endpoint:** `GET https://api.rpow2.com/me`

**Authentication:** Cookie-based (rpow_session)

```bash
curl -s -H "Cookie: rpow_session=YOUR_SESSION_TOKEN" https://api.rpow2.com/me
```

**Response:**

```json
{
  "email": "user@example.com",
  "balance_base_units": "171002136120",
  "minted_base_units": "171002136120",
  "sent_base_units": "0",
  "received_base_units": "0",
  "wrap_allowed": false,
  "solana_wallet": null,
  "srpow_supply_owned_base_units": "0"
}
```

## Fields

- **balance_base_units**: Current balance in smallest unit (base units)
- **minted_base_units**: Total mined (all-time)
- **sent_base_units**: Total sent to others
- **received_base_units**: Total received from others
- **wrap_allowed**: Whether user can wrap rpow2 → sPOW (Solana token)
- **solana_wallet**: Connected Solana wallet address (null if not connected)
- **srpow_supply_owned_base_units**: Wrapped sPOW tokens owned

## Balance Conversion

The exact conversion rate from base_units to tokens is not documented in the API response. Common patterns:

- **1 token = 1 billion base units** → 171,002,136,120 = 171.002 tokens
- **1 token = 1 million base units** → 171,002,136,120 = 171,002.136 tokens

Check the web dashboard at https://rpow2.com for the displayed balance to determine the correct conversion.

## Mining Performance Calculation

```bash
# Get balance at two points in time
BALANCE_START=$(curl -s -H "Cookie: rpow_session=..." https://api.rpow2.com/me | jq -r '.balance_base_units')
sleep 3600  # Wait 1 hour
BALANCE_END=$(curl -s -H "Cookie: rpow_session=..." https://api.rpow2.com/me | jq -r '.balance_base_units')

# Calculate mining rate
MINED=$((BALANCE_END - BALANCE_START))
echo "Mined in 1 hour: $MINED base units"
```

## Notes

- Balance updates in real-time as blocks are minted
- The miner log does NOT show balance — must query API or check web dashboard
- Cookie must be valid (check `exp` field in JWT — Unix timestamp)
- No rate limiting observed on `/me` endpoint (safe to poll frequently)
