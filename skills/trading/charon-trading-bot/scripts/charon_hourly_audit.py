#!/usr/bin/env python3
"""Charon hourly auto-learn: analyze closed trades, derive insights,
print compact JSON report to stdout (consumed by cron prompt).
"""
import sqlite3, json, statistics
from datetime import datetime, timezone

DB = '/home/ubuntu/charon/charon.sqlite'
WINDOW_MS = 60 * 60 * 1000
ALL_WINDOW_MS = 24 * 60 * 60 * 1000

def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    cutoff_1h = now_ms - WINDOW_MS
    cutoff_24h = now_ms - ALL_WINDOW_MS

    closed_1h = con.execute("""
        SELECT * FROM dry_run_positions
        WHERE status='closed' AND closed_at_ms >= ?
        ORDER BY closed_at_ms DESC
    """, (cutoff_1h,)).fetchall()
    closed_24h = con.execute("""
        SELECT * FROM dry_run_positions
        WHERE status='closed' AND closed_at_ms >= ?
        ORDER BY closed_at_ms DESC
    """, (cutoff_24h,)).fetchall()
    open_now = con.execute("SELECT * FROM dry_run_positions WHERE status='open'").fetchall()
    strat_row = con.execute("SELECT id, config_json FROM strategies WHERE enabled=1").fetchone()
    strat = json.loads(strat_row['config_json']) if strat_row else {}

    def stats(rows):
        if not rows: return None
        pnls = [r['pnl_percent'] or 0 for r in rows]
        sols = [r['pnl_sol'] or 0 for r in rows]
        wins = sum(1 for p in pnls if p > 0)
        return {
            'n': len(rows),
            'wins': wins,
            'losses': len(rows) - wins,
            'win_rate': round(wins/len(rows)*100, 1),
            'total_pnl_sol': round(sum(sols), 4),
            'avg_pnl_pct': round(statistics.mean(pnls), 2),
            'median_pnl_pct': round(statistics.median(pnls), 2),
        }

    def by_route(rows):
        out = {}
        for r in rows:
            try:
                snap = json.loads(r['snapshot_json'])
                route = (snap.get('candidate', {}).get('signals') or {}).get('route') or 'unknown'
            except Exception:
                route = 'unknown'
            out.setdefault(route, []).append(r['pnl_percent'] or 0)
        return {
            k: {'n': len(v),
                'wr': round(sum(1 for x in v if x > 0) / len(v) * 100, 1),
                'avg_pct': round(statistics.mean(v), 2)}
            for k, v in out.items()
        }

    def by_mcap(rows):
        b = {'<10k': [], '10-30k': [], '30-60k': [], '60-100k': [], '>100k': []}
        for r in rows:
            mc = r['entry_mcap'] or 0
            pnl = r['pnl_percent'] or 0
            if mc < 10000: b['<10k'].append(pnl)
            elif mc < 30000: b['10-30k'].append(pnl)
            elif mc < 60000: b['30-60k'].append(pnl)
            elif mc < 100000: b['60-100k'].append(pnl)
            else: b['>100k'].append(pnl)
        return {
            k: {'n': len(v),
                'wr': round(sum(1 for x in v if x > 0) / len(v) * 100, 1),
                'avg_pct': round(statistics.mean(v), 2)}
            for k, v in b.items() if v
        }

    def by_exit_reason(rows):
        out = {}
        for r in rows:
            reason = r['exit_reason'] or 'unknown'
            out.setdefault(reason, []).append(r['pnl_percent'] or 0)
        return {
            k: {'n': len(v), 'avg_pct': round(statistics.mean(v), 2)}
            for k, v in out.items()
        }

    report = {
        'ts': datetime.now(tz=timezone.utc).isoformat(),
        'open_now': len(open_now),
        'strategy_id': strat_row['id'] if strat_row else None,
        'strategy_params': {
            'min_mcap_usd': strat.get('min_mcap_usd'),
            'max_mcap_usd': strat.get('max_mcap_usd'),
            'sl_percent': strat.get('sl_percent'),
            'tp_percent': strat.get('tp_percent'),
            'trailing_percent': strat.get('trailing_percent'),
            'max_hold_ms': strat.get('max_hold_ms'),
            'min_holders': strat.get('min_holders'),
            'blocked_routes': strat.get('blocked_routes', []),
        },
        'last_1h': {
            'overall': stats(closed_1h),
            'by_route': by_route(closed_1h),
            'by_mcap_bucket': by_mcap(closed_1h),
            'by_exit_reason': by_exit_reason(closed_1h),
        },
        'last_24h': {
            'overall': stats(closed_24h),
            'by_route': by_route(closed_24h),
            'by_mcap_bucket': by_mcap(closed_24h),
            'by_exit_reason': by_exit_reason(closed_24h),
        },
    }

    worst = sorted(closed_1h, key=lambda r: r['pnl_percent'] or 0)[:5]
    report['worst_recent'] = [
        {
            'symbol': r['symbol'],
            'mint': r['mint'][:8] + '..',
            'pnl_pct': round(r['pnl_percent'] or 0, 1),
            'exit_reason': r['exit_reason'],
            'entry_mcap': r['entry_mcap'],
            'hold_min': round((r['closed_at_ms'] - r['opened_at_ms']) / 60000, 1) if r['closed_at_ms'] else None,
        } for r in worst
    ]

    print(json.dumps(report, indent=2, default=str))

if __name__ == '__main__':
    main()
