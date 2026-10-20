---
name: superagent-power-pack
description: Power Pack — planner (NL→plan), swarm (multi-agent), skill forge, automation engine (WHEN/THEN), backtester, dashboard, voice mode, explainability. SUPERAGENT v4.0 m17.
---

# superagent-power-pack — Power Pack

Orkestrasi tingkat tinggi: planner, multi-agent swarm, skill forge, automation, backtest, dashboard, voice mode, explainability.

Scripts: `~/superagent-v4/tools/{planner,swarm,skill_forge,automation,backtest,dashboard,voice,explain,model_registry}.py`

## 1. Workflow Planner (NL → Plan)

```python
from tools.planner import make_plan, execute_plan
plan = make_plan("isi base lalu beli token 0xABC di 5 wallet")
print(plan.summary())  # step 💸 = nyentuh dana (governor-gated)

async def confirm_cb(step):
    # Governor checks run here automatically
    return input(f"Execute: {step.name}? (y/n): ").lower() == "y"

await execute_plan(plan, handlers=my_handlers, confirm_cb=confirm_cb)
```

## 2. Multi-Agent Swarm

```python
from tools.swarm import Swarm, Specialist
sw = Swarm([
    Specialist("researcher", my_researcher_fn),
    Specialist("monitor", my_monitor_fn),
    Specialist("executor", my_executor_fn, holds_keys=True)
])
await sw.dispatch({
    "researcher": {"task": "cari token baru di Base"},
    "monitor": {"task": "pantau wallet whale"}
})
print(sw.safety_report())  # warning kalau non-executor pegang key
```

## 3. Skill Forge — Agent Buat Skill Sendiri

```python
from tools.skill_forge import forge_proposal
forge_proposal("belum bisa baca Chainlink oracle", "m18")
# → bikin proposal di ~/.hermes/proposals/
#   operator yang acc + re-lock
```

## 4. Automation Engine (WHEN → THEN)

```python
from tools.automation import AutomationEngine
ae = AutomationEngine()
ae.add_rule("gas murah → swap", "price",
            {"metric": "gas", "chain": "ethereum"},
            actions=[{"action": "swap", "params": {"from": "ETH", "to": "USDC"}, "funds": True}])

# Trigger → all fund actions go through governor
await ae.fire(event, action_handlers=my_handlers, confirm_cb=my_confirm)
```

## 5. Backtester

```python
from tools.backtest import backtest
result = backtest(my_strategy_fn, candles, initial_capital=1000)
print(result.metrics())  # {return_pct, win_rate, trades, drawdown, sharpe}
```

## 6. Live Dashboard

```python
from tools.dashboard import build_dashboard_html, gather
html = build_dashboard_html(gather(governor=gov, alert_engine=ae))
# serve from VPS with AUTH
```

## 7. Voice Mode (Ngobrol Kayak Nelpon)

```python
from tools.voice import converse
converse("voice_note.ogg")  # STT → LLM (cascade) → TTS
# pip install pyttsx3 (TTS gratis offline)
```

## 8. Explainability

```python
from tools.explain import explain
print(explain())  # "apa & kenapa" dari audit trail governor
```

## Dynamic Model Registry (m7 v4.0)

```python
from tools.model_registry import ModelRegistry
reg = ModelRegistry(master_pw=os.environ["HERMES_MASTER_PW"])
reg.add("my-claude", api_key="sk-ant-...", base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-20250514", kind="anthropic", priority=2)

# Use in cascade
response = reg.call_with_cascade(messages, system_prompt="...")
# Falls back through all registered models on failure
```

Add model via NL: "add model claude opus" → agent calls `reg.add(...)`.

## Env Vars

```bash
HERMES_MODELS_DB=~/.hermes/models.db
HERMES_AUTOMATION_DB=~/.hermes/automation.db
HERMES_PROPOSALS=~/.hermes/proposals
HERMES_MASTER_PW=  # [WAJIB] buat enkripsi key model registry
HERMES_TTS_OUT=/tmp/hermes_reply.wav
```
