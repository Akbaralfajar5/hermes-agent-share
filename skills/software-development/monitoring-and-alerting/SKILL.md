---
name: monitoring-and-alerting
description: Monitor processes, bots, and VPS health — disk, memory, CPU, uptime. Alert to Telegram when anomalies detected. Use for background processes (PM2, mining, trading bots), VPS health checks, and automated watchdogs via cron jobs.
---

# Monitoring & Alerting

## Overview

Background processes fail silently. Disks fill up. Memory leaks. Bots crash at 3 AM. Monitoring catches problems before users do. Set up watchers that check health and alert via Telegram when something is wrong.

## When to Use

- Running background processes (PM2, mining, trading bots)
- VPS with multiple services
- Cron jobs that must succeed
- Production deployments that need uptime tracking
- Memory/resource-intensive workloads

**When NOT to use:** Local development, throwaway experiments, one-off scripts.

## The Watchdog Pattern

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Cron Job   │────→│ Health Check │────→│ Alert/Report  │
│  (interval) │     │   (script)   │     │  (Telegram)   │
└─────────────┘     └──────────────┘     └───────────────┘
                          │
                    ┌─────┴─────┐
                    │ Threshold │
                    │  Check    │
                    └───────────┘
```

**Key principle:** Silent when healthy, LOUD when not. Empty stdout = no notification sent.

## Health Check Scripts

### PM2 Process Check

```bash
#!/bin/bash
# Check if PM2 processes are running
ISSUES=""

for proc in charon example-target-bot mining-worker; do
  STATUS=$(pm2 jlist 2>/dev/null | jq -r ".[] | select(.name==\"$proc\") | .pm2_env.status")
  if [ "$STATUS" != "online" ]; then
    ISSUES="$ISSUES\n❌ $proc: $STATUS"
  fi
done

if [ -n "$ISSUES" ]; then
  echo -e "PM2 ALERT:$ISSUES"
fi
# Empty output = silent, no alert sent
```

### Disk Space Check

```bash
#!/bin/bash
THRESHOLD=85
USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
  echo "⚠️ Disk usage: ${USAGE}% (threshold: ${THRESHOLD}%)"
  echo "Top 5 largest dirs:"
  du -sh /* 2>/dev/null | sort -rh | head -5
fi
```

### Memory Check

```bash
#!/bin/bash
THRESHOLD=90
USAGE=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
  echo "⚠️ Memory usage: ${USAGE}%"
  echo "Top 5 processes:"
  ps aux --sort=-%mem | head -6
fi
```

### Combined VPS Health

```bash
#!/bin/bash
ALERTS=""

# Disk
DISK=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
[ "$DISK" -gt 85 ] && ALERTS="$ALERTS\n💾 Disk: ${DISK}%"

# Memory
MEM=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
[ "$MEM" -gt 90 ] && ALERTS="$ALERTS\n🧠 Memory: ${MEM}%"

# CPU (1-min load avg vs core count)
CORES=$(nproc)
LOAD=$(cat /proc/loadavg | awk '{print $1}')
HIGH=$(echo "$LOAD > $CORES" | bc -l 2>/dev/null)
[ "$HIGH" = "1" ] && ALERTS="$ALERTS\n🔥 CPU load: $LOAD (${CORES} cores)"

# PM2 processes
for proc in charon example-target-bot; do
  STATUS=$(pm2 jlist 2>/dev/null | jq -r ".[] | select(.name==\"$proc\") | .pm2_env.status")
  [ "$STATUS" != "online" ] && ALERTS="$ALERTS\n⚙️ $proc: $STATUS"
fi

# Uptime
UPTIME=$(uptime -p)

if [ -n "$ALERTS" ]; then
  echo -e "🚨 VPS Health Alert:$ALERTS\n⏱️ Uptime: $UPTIME"
fi
```

## Cron Job Setup

### Hermes Cron (Recommended)

```python
# Create monitoring cron job via Hermes
cronjob(
    action="create",
    name="vps-health-watchdog",
    schedule="*/15 * * * *",  # every 15 minutes
    prompt="Run ~/.hermes/scripts/vps-health.sh. If output is non-empty, report to user. If empty, stay silent.",
    script="~/.hermes/scripts/vps-health.sh",
    no_agent=True,  # script-only, no LLM needed
    deliver="telegram"  # alert goes to Telegram home
)
```

### System Cron (Fallback)

```bash
# Edit crontab
crontab -e

# Every 15 minutes, check health, alert if issues
*/15 * * * * /home/ubuntu/.hermes/scripts/vps-health.sh >> /var/log/health-check.log 2>&1
```

## Application-Level Monitoring

### Next.js API Health Endpoint

```typescript
// src/app/api/health/route.ts
import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function GET() {
  const checks: Record<string, string> = {};

  // Database
  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );
    const start = Date.now();
    await supabase.from('_pg_stat_statements').select('query').limit(1);
    checks.database = `ok (${Date.now() - start}ms)`;
  } catch (e: any) {
    checks.database = `error: ${e.message}`;
  }

  // Memory
  const mem = process.memoryUsage();
  checks.heap = `${Math.round(mem.heapUsed / 1024 / 1024)}MB`;

  const hasError = Object.values(checks).some(v => v.startsWith('error'));

  return NextResponse.json(
    { status: hasError ? 'degraded' : 'healthy', checks },
    { status: hasError ? 503 : 200 }
  );
}
```

### Bot Process Monitoring (Node.js)

```typescript
// watchdog.ts — runs alongside bot
import { exec } from 'child_process';

function checkBot(botName: string): Promise<boolean> {
  return new Promise((resolve) => {
    exec(`pm2 jlist`, (err, stdout) => {
      if (err) return resolve(false);
      const processes = JSON.parse(stdout);
      const bot = processes.find((p: any) => p.name === botName);
      resolve(bot?.pm2_env?.status === 'online');
    });
  });
}

setInterval(async () => {
  const bots = ['charon', 'example-target-bot', 'mining-worker'];
  for (const bot of bots) {
    const alive = await checkBot(bot);
    if (!alive) {
      console.error(`[WATCHDOG] ${bot} is DOWN — restarting...`);
      exec(`pm2 restart ${bot}`);
      // Alert via Hermes or direct Telegram API
    }
  }
}, 60_000); // check every minute
```

## Log Monitoring

### Detect Errors in Logs

```bash
#!/bin/bash
# Check last 100 lines of PM2 logs for errors
LOG_FILE="$HOME/.pm2/logs/charon-error.log"
RECENT_ERRORS=$(tail -100 "$LOG_FILE" 2>/dev/null | grep -c "ERROR\|FATAL\|Exception")

if [ "$RECENT_ERRORS" -gt 5 ]; then
  echo "⚠️ charon: $RECENT_ERRORS errors in last 100 log lines"
  tail -5 "$LOG_FILE"
fi
```

### Log Rotation

```bash
# PM2 built-in
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk usage | >80% | >90% |
| Memory usage | >85% | >95% |
| CPU load | >cores × 1.5 | >cores × 3 |
| Process status | restarted | down >5min |
| Error rate | >5/100 lines | >20/100 lines |
| Response time | >500ms | >2000ms |
| Disk I/O wait | >20% | >50% |

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It's been running fine, no need to monitor" | Survivorship bias. You don't know about the silent failures |
| "I'll notice if something breaks" | You won't. It'll break at 3 AM on a weekend |
| "PM2 auto-restarts, that's enough" | Auto-restart hides crashes. You need to know it happened |
| "Monitoring is overkill for small projects" | One disk-full incident costs more time than a year of monitoring |

## Verification

- [ ] Health check script runs on schedule (cron or PM2)
- [ ] Alerts deliver to Telegram when threshold exceeded
- [ ] Alert is silent when everything is healthy
- [ ] PM2 processes monitored for status changes
- [ ] Disk and memory checked at regular intervals
- [ ] Error log patterns detected and reported
- [ ] Health endpoint available for external monitoring
