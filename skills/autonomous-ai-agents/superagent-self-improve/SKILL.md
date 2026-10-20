---
name: superagent-self-improve
description: Self-improvement loop — compounding memory engine, reflection, auto-fix reversible ops, proposal-driven upgrades. SUPERAGENT v4.0 x4.
---

# superagent-self-improve — Self-Improvement Loop

Agent belajar dari tiap sesi, auto-fix masalah operasional, usul upgrade — semua lewat gerbang struktural.

Scripts: `~/superagent-v4/tools/{memory_engine,reflection}.py`

## How It Works

```
OBSERVE → REFLECT → LEARN → DIAGNOSE → AUTO-FIX (safe only) → PROPOSE (rest)
```

## Compounding Memory

```python
from tools.memory_engine import MemoryEngine
mem = MemoryEngine(db_path=os.environ.get("HERMES_MEMORY_DB"))

# Remember facts
mem.remember("Base RPC ankr timeout → llamarpc works", kind="blocker", tags="rpc,base")
mem.remember("Meridian: SOL above bins_above enabled", kind="config", tags="meridian,sol")

# Recall relevant context
context = mem.recall("Base RPC", limit=5)

# Useful memories get reinforced (higher weight → more likely to appear)
# Irrelevant ones decay naturally
```

## Reflection + Auto-Fix

```python
from tools.reflection import daily_cycle, auto_fix, can_autofix, propose, Proposal

# Daily cycle (run via cron or heartbeat)
report = daily_cycle(mem)
# → learns patterns, generates proposals, returns summary

# Auto-fix safe operational issues
if can_autofix("retry_with_fallback_rpc"):
    auto_fix("retry_with_fallback_rpc", handlers={
        "retry_with_fallback_rpc": rotate_to_fallback_rpc
    })

# Safe auto-actions (reversible, no funds):
#   retry_with_fallback_rpc · rotate_rpc · switch_llm_provider
#   restart_crashed_process · clear_cache · requote · backoff_and_retry

# Everything else → proposal
proposal_id = propose(
    title="Tambahkan fallback RPC Base permanen",
    description="Ankr sering timeout (>5x/hari), auto-switch ke llamarpc",
    affected_files=["config.py"]
)
# → written to ~/.hermes/proposals/
# → operator must review + approve + re-lock
```

## Hard Limits (ENFORCED in code, not just prompt)

```
NEVER autonomously:
✗ Sign tx / move funds / approve spending
✗ Change spend cap or disable governor
✗ Regenerate SKILLS.lock
✗ Edit FROZEN_PATHS (SOUL.md, AGENTS.md, governor.py, mev.py, security.md,
  skill_integrity.py, reflection.py, USER.md, x4.md)
✗ Apply its own proposals
```

## Proposal Flow

```
agent finds improvement → reflection.propose() → file di ~/.hermes/proposals/
  → operator reviews → if approved, operator edits manually
  → operator: python tools/skill_integrity.py generate (re-lock)
```

## Env Vars

```bash
HERMES_MEMORY_DB=~/.hermes/memory.db
HERMES_PROPOSALS=~/.hermes/proposals
HERMES_REFLECTION_AUDIT=~/.hermes/reflection-audit.log
```
