# Vast.ai GPU Search via API

Search available (unrented) instances programmatically without logging in.

## Endpoint

```
GET https://console.vast.ai/api/v0/bundles/?q=<URL-encoded JSON filter>
```

## Filter Schema

```json
{
  "gpu_name": {"in": ["RTX 5090", "RTX 4090"]},
  "num_gpus": {"gte": 4},
  "rentable": {"eq": true},
  "rented": {"eq": false}
}
```

## Full Search Script

```bash
curl -s "https://console.vast.ai/api/v0/bundles/?q=%7B%22gpu_name%22%3A%7B%22in%22%3A%5B%22RTX+5090%22%2C%22RTX+4090%22%5D%7D%2C%22num_gpus%22%3A%7B%22gte%22%3A4%7D%2C%22rentable%22%3A%7B%22eq%22%3Atrue%7D%2C%22rented%22%3A%7B%22eq%22%3Afalse%7D%7D" | python3 -c "
import json, sys
data = json.load(sys.stdin)
offers = data.get('offers', [])
results = []
for o in offers:
    results.append({
        'id': o.get('id'),
        'gpu': o.get('gpu_name'),
        'num_gpus': o.get('num_gpus'),
        'price': o.get('dph_total'),
        'reliability': o.get('reliability2'),
        'country': o.get('geolocation'),
        'cuda': o.get('cuda_max_good'),
        'dlperf': o.get('dlperf'),
    })
results.sort(key=lambda x: x['price'] or 999)
for r in results[:15]:
    print(f\"ID:{r['id']} | {r['num_gpus']}x {r['gpu']} | \${r['price']:.3f}/hr | Reliability:{r['reliability']:.2%} | {r['country']} | CUDA:{r['cuda']}\")
"
```

## Search for 8x GPU (higher throughput)

Change `"gte": 4` to `"gte": 8` in the filter.

## Key Response Fields

| Field | Description |
|-------|-------------|
| `id` | Instance ID (use to rent) |
| `gpu_name` | GPU model string |
| `num_gpus` | Number of GPUs |
| `dph_total` | Price per hour (USD) |
| `reliability2` | Reliability score (0-1) |
| `geolocation` | Country/region |
| `cuda_max_good` | Max CUDA version |
| `dlperf` | DL performance score |
| `cpu_name` | CPU model |
| `cpu_cores_effective` | Available CPU cores |
| `ram_total_gb` | Total RAM |

## Picking the Best Instance

Priority order for $HASH mining:
1. **GPU type** — RTX 5090 > RTX 4090 > RTX 3090
2. **Num GPUs** — more = better (8x > 4x)
3. **Price** — lower $/hr
4. **Reliability** — >99% preferred
5. **CUDA version** — 12.8+ preferred

## Automated Monitoring (Hermes Cronjob)

Good GPU instances (4x/8x RTX 5090) get rented within 2-5 minutes of appearing. Set up a Hermes cronjob to poll every 5 minutes and notify via Telegram when instances are available:

**Cronjob config:**
```
Name: Vast.ai GPU Monitor
Schedule: every 5m
Deliver: telegram:<user_id>
Enabled toolsets: terminal, web

Prompt:
Check Vast.ai API for available GPU instances with RTX 4090 or RTX 5090, minimum 4 GPUs, not rented.

Use this curl command:
curl -s "https://console.vast.ai/api/v0/bundles/?q=%7B%22gpu_name%22%3A%7B%22in%22%3A%5B%22RTX+5090%22%2C%22RTX+4090%22%5D%7D%2C%22num_gpus%22%3A%7B%22gte%22%3A4%7D%2C%22rentable%22%3A%7B%22eq%22%3Atrue%7D%2C%22rented%22%3A%7B%22eq%22%3Afalse%7D%7D"

Parse the JSON response and extract offers. Sort by price (dph_total ascending).

Only send a Telegram notification if there are available instances. Format the message as:

🔥 **Vast.ai GPU Alert!**

List top 5 cheapest available instances with:
- ID, GPU type, num_gpus, price/hr, reliability, country, CUDA version

End with: "Kirim SSH command kalau mau gue setup langsung!"

If no instances available, do NOT send any notification (stay silent).
```

This prevents spam while ensuring fast notification when something good appears.

## Notes

- Instances go fast — popular configs (8x RTX 5090) can be rented within minutes of appearing
- No auth required for search — public endpoint
- `rentable=true, rented=false` = currently available to rent
- Prices fluctuate — check at different times of day
