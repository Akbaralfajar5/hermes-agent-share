# Domain Speed Testing

## Problem
Sites like example-target.com have multiple mirror domains (example-targetff.com, example-targetgg.com, etc.) with different response times. Choosing the fastest domain improves worker throughput.

## Bash Script (Parallel Testing)
```bash
#!/bin/bash
suffixes=(aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz
          00 11 22 33 44 55 66 77 88 99
          01 02 03 04 05 06 07 08 09 10 12 13 14 15 16 17 18 19 20)

for s in "${suffixes[@]}"; do
    domain="example-target${s}.com"
    result=$(curl -sL --max-time 5 --connect-timeout 3 \
        -o /dev/null -w "%{time_total} %{http_code}" "https://${domain}" 2>/dev/null)
    time_s=$(echo "$result" | awk '{print $1}')
    code=$(echo "$result" | awk '{print $2}')
    if [[ "$code" == "200" || "$code" == "301" || "$code" == "302" ]]; then
        echo "${domain} ${time_s} ${code}"
    fi
done | sort -t' ' -k2 -n
```

## Python Alternative
```python
import subprocess, concurrent.futures

def test_domain(suffix):
    domain = f"example-target{suffix}.com"
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "5", "--connect-timeout", "3",
             "-o", "/dev/null", "-w", "%{time_total} %{http_code}",
             f"https://{domain}"],
            capture_output=True, text=True, timeout=10
        )
        parts = r.stdout.strip().split()
        if len(parts) == 2 and parts[1] in ('200', '301', '302'):
            return (domain, float(parts[0]), parts[1])
    except:
        pass
    return None

suffixes = ['ff','gg','hh','ii','jj','kk','ll','mm','nn','oo','pp','qq','rr','ss','tt','xx','yy','zz']
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    results = [r for r in pool.map(test_domain, suffixes) if r]
results.sort(key=lambda x: x[1])

for domain, time_s, code in results:
    icon = "⚡" if time_s < 0.1 else "🟢" if time_s < 0.2 else "🟡" if time_s < 0.5 else "🔴"
    print(f"  {icon} {domain} — {time_s:.3f}s ({code})")
```

## Key Findings (example-target network, July 2026)
- **Fastest:** example-targetff.com (0.094s), example-targetii.com (0.095s), example-targetgg.com (0.106s)
- **Slowest:** example-targetrr.com (2.8s), example-targetss.com (1.7s)
- All 25+ responding domains serve the same site — speed difference is CDN routing
- Response times can vary by time of day and client location

## Pitfalls
- `curl` from datacenter VPS may not reflect user's actual latency
- Domain availability changes — some domains go offline without notice
- Always test from the user's network, not just from VPS
