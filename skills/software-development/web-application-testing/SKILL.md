---
name: web-application-testing
description: "Security testing (OWASP, vulnerability scanning) and load/performance testing (Apache Bench, k6, Locust) for web applications — includes skripsi-ready report templates and result tables."
tags: [security, load-testing, performance, owasp, testing, benchmark, skripsi]
---

# Web Application Testing

Security and performance testing for web applications. Covers OWASP vulnerability scanning, penetration testing basics, load testing, and stress testing — with report templates suitable for academic research (skripsi).

## When to Use
- User needs to test a web application's security (OWASP, SQL injection, XSS)
- User needs performance/load testing (response time, throughput, stress)
- User mentions "pengujian keamanan", "load test", "stress test", "black box testing"
- User needs test result tables for skripsi BAB IV

## Tools

### Security Testing
```bash
sudo apt install nmap nikto sqlmap zaproxy
```

### Load Testing
```bash
sudo apt install apache2-utils  # Apache Bench
# k6: see https://k6.io/docs/getting-started/installation/
pip install locust
```

## Security Testing

### OWASP Top 10 Quick Checks
1. Broken Access Control — test admin endpoints without auth
2. Injection — SQLMap automated scan
3. XSS — manual payload injection
4. Security Misconfiguration — Nikto scan
5. Cryptographic Failures — HTTPS check

### Automated Scanning
```bash
# Port scan
nmap -sV localhost

# Web server scan
nikto -h http://localhost:3000 -o nikto_report.html -Format html

# SQL injection
sqlmap -u "http://localhost:3000/api/users?id=1" --batch

# OWASP ZAP
zap-cli quick-scan http://localhost:3000
```

### Manual Tests
```bash
# Auth bypass
curl http://localhost:3000/api/admin/users

# SQL injection in login
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"x"}'

# XSS
curl -X POST http://localhost:3000/api/comments \
  -d '{"text":"<script>alert(1)</script>"}'

# Exposed files
curl http://localhost:3000/.env
curl http://localhost:3000/uploads/
```

## Load Testing

### Apache Bench (Quick)
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:3000/

# With auth header
ab -n 1000 -c 50 -H "Authorization: Bearer TOKEN" http://localhost:3000/api/users
```

### k6 (Scriptable)
```javascript
// load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  let res = http.get('http://localhost:3000');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

### Locust (Python)
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_homepage(self):
        self.client.get("/")
    
    @task(1)
    def view_api(self):
        self.client.get("/api/products")
```

## Skripsi Report Templates

### Security Test Results Table
| No | Jenis Pengujian | Metode | Hasil | Status |
|----|----------------|--------|-------|--------|
| 1 | SQL Injection | SQLMap scan | Tidak ditemukan | ✓ Pass |
| 2 | XSS | Manual payload | Tidak ditemukan | ✓ Pass |
| 3 | Auth Bypass | Endpoint testing | Terproteksi | ✓ Pass |

### Load Test Results Table
| Jumlah User | Request/Second | Response Time (ms) | Success Rate |
|-------------|---------------|-------------------|--------------|
| 10 | 45.2 | 22 | 100% |
| 50 | 156.3 | 32 | 99.8% |
| 100 | 245.8 | 41 | 99.5% |
| 200 | 312.4 | 64 | 98.2% |

### Performance Metrics to Report
- Response Time: average, median, p95, p99
- Throughput: requests/second
- Error Rate: % failed requests
- Resource Usage: CPU, memory during test

## Pitfalls
- Always test on staging/development, never production without approval
- Apache Bench only tests single URL — use k6/Locust for multi-endpoint flows
- `ulimit -n 65536` if you hit "too many open files"
- For skripsi: include both the test methodology AND results with charts
- Security testing tools may trigger WAF/IDS — inform hosting provider
