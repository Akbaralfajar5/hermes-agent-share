# Testing Hermes Ecosystem Tools After Installation

After installing Hermes ecosystem extensions (HUD, Maestro, Control Interface, Skill Factory), verify each tool works before declaring success.

## 1. Hermes HUD (Terminal Monitoring)

**What it does:** Real-time terminal dashboard showing memory, skills, cron jobs, and timeline events.

**Test:**

```bash
# Text mode (quick check)
~/hermes-hud/venv/bin/hermes-hud --text

# TUI mode (interactive)
~/hermes-hud/venv/bin/hermes-hud

# Neofetch-style modes
~/hermes-hud/venv/bin/hermes-hud --ai
~/hermes-hud/venv/bin/hermes-hud --br
~/hermes-hud/venv/bin/hermes-hud --fsociety
```

**Expected output (text mode):**

```
HUDState(
  memory=MemoryState(entries=N, total_chars=X/2200),
  user=MemoryState(entries=N, total_chars=X/1375),
  skills=SkillsState(skills=N),
  cron=CronState(jobs=...),
  timeline=TimelineState(events=...)
)
```

**Installation:** Requires Python venv with `pip install -e ".[neofetch]"` from source (not on PyPI).

---

## 2. Maestro (Task Orchestration)

**What it does:** Claude-style task management with blocker graphs, priority queues, and mission control TUI.

**Test:**

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro

# Create a task
./dist/maestro task create "Test task: Verify Maestro installation"

# List tasks
./dist/maestro task list

# Show task details
./dist/maestro task show <slug-or-id>

# Get next ready task (no blockers)
./dist/maestro task next

# Batch create from JSON plan
./dist/maestro task plan --file /path/to/plan.json
```

**Expected output:**

```
[ok] Task created: implement/test-task-verify-maestro
  Slug: implement/test-task-verify-maestro
  Title: Test task: Verify Maestro installation
  Status: pending
  Priority: P2
  Type: task
```

**Installation:** Requires Bun runtime (`curl -fsSL https://bun.sh/install | bash`). Build with `bun install && bun run build`.

**Priority values:** 0 (critical), 1 (high), 2 (medium), 3 (low), 4 (backlog). NOT `P0`/`P1` strings.

**JSON plan format:**

```json
{
  "tasks": [
    {
      "title": "Task title",
      "priority": 1,
      "type": "task",
      "description": "Optional description"
    }
  ]
}
```

---

## 3. Hermes Control Interface (Web Dashboard)

**What it does:** Web-based control panel for Hermes Agent with chat interface, real-time monitoring, and task management UI.

**Test:**

```bash
cd ~/hermes-control-interface
source ~/.nvm/nvm.sh && nvm use 20
npm run dev
```

**Expected output:**

```
VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: http://0.0.0.0:5173/
```

**Verify:**

```bash
# Check server is listening
netstat -tlnp | grep 5173
# tcp  0  0  0.0.0.0:5173  0.0.0.0:*  LISTEN  <pid>/node

# Test HTTP response
curl -s http://localhost:5173 | head -20
# Should return HTML with "Hermes Control Interface" title
```

**Requirements:**
- Node.js 20.19+ or 22.12+ (Vite requirement)
- If nvm is installed, must explicitly `nvm use 20` before `npm run dev`
- Default password: set in `~/hermes-control-interface/.env` as `HCI_PASSWORD`

**Remote access:** Edit `vite.config.js` to add `host: '0.0.0.0'` in `server` section. Port 5173 must be opened in cloud security group or firewall.

**Common issues:**
- **"Node.js 18.x.x. Vite requires 20.19+"** → nvm override, see `references/nodejs-upgrade-nvm-override.md`
- **"Cannot find native binding"** → npm optional dependency bug, delete `node_modules` and `package-lock.json`, reinstall
- **Timeout on remote access** → port 5173 blocked by cloud security group (not local firewall issue if UFW is inactive)

---

## 4. Hermes Skill Factory (Auto-Skill Generation)

**What it does:** Meta-skill that watches workflows and auto-generates skill proposals from detected patterns.

**Test:**

```bash
# Check if enabled
hermes skills list | grep -i "skill-factory"

# Should show:
# │ Skill Factory  │ hermes-skill-factory │ local │ local │ enabled │
```

**Installation:** Clone to `~/.hermes/skills/hermes-skill-factory` and run `./install.sh`.

**Usage (in Hermes session):**

```
/skill-factory propose   # Show detected patterns
/skill-factory generate  # Generate skill from pattern
```

**Verification:** After installation, skill should appear in `hermes skills list` with status `enabled`. If disabled, enable via `hermes skills config` or `/reset` to reload.

---

## Test Results Summary Template

After testing all tools, create a summary document:

```markdown
# Test Results

| Tool | Status | Notes |
|------|--------|-------|
| Hermes HUD | ✅ PASS | Monitoring working |
| Maestro | ✅ PASS | Task management working |
| Hermes Control Interface | ✅ PASS | Web dashboard accessible |
| Skill Factory | ✅ PASS | Plugin enabled |

**Overall Success Rate:** X/4 working
```

---

## Troubleshooting

### Hermes HUD not found
- Check venv activation: `source ~/hermes-hud/venv/bin/activate`
- Reinstall: `cd ~/hermes-hud && pip install -e ".[neofetch]"`

### Maestro command not found
- Check Bun in PATH: `export PATH="$HOME/.bun/bin:$PATH"`
- Rebuild: `cd ~/maestro && bun run build`

### Control Interface won't start
- Check Node version: `node --version` (must be 20.19+)
- If nvm installed: `source ~/.nvm/nvm.sh && nvm use 20`
- Clear npm cache: `rm -rf node_modules package-lock.json && npm install`

### Skill Factory not showing
- Check installation path: `ls ~/.hermes/skills/hermes-skill-factory/`
- Re-run install: `cd ~/.hermes/skills/hermes-skill-factory && ./install.sh`
- Reload skills: `/reset` in Hermes session

---

## Key Insights

- **Hermes HUD** is best for monitoring cron jobs and agent activity (useful for trading bots)
- **Maestro** is ideal for complex multi-step projects (thesis research, website development)
- **Hermes Control Interface** provides web access but requires Node.js 20+ and security group configuration
- **Skill Factory** runs passively — no immediate test output, but enables auto-skill generation over time

All tools are independent — one failing doesn't block the others.
