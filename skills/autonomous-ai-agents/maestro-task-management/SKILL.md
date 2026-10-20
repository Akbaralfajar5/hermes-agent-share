---
name: maestro-task-management
description: "Manage tasks, missions, and workflows with Maestro task orchestration system."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maestro, task-management, orchestration, planning, workflow]
    homepage: https://github.com/ReinaMacCredy/maestro
    related_skills: [hermes-agent, writing-plans, subagent-driven-development]
---

# Maestro Task Management

Maestro is a task orchestration system for Hermes Agent that provides Claude-style blocker graph task management. It tracks tasks, dependencies, priorities, and ownership across sessions.

**When to use Maestro:**
- Multi-step projects with dependencies (skripsi research, website development, trading system setup)
- Long-running work that spans multiple sessions
- Coordinating parallel workstreams
- Tracking progress on complex initiatives

**Installation:** See `hermes-agent` skill → Hermes ecosystem tools section.

## Quick Start

```bash
# Add Bun to PATH (required for Maestro)
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro

# Create a single task
./dist/maestro task create "Task title" --priority 1

# Create multiple tasks from JSON plan
./dist/maestro task plan --file tasks.json

# List all tasks
./dist/maestro task list

# List ready tasks (no blockers)
./dist/maestro task ready

# Get next task to work on
./dist/maestro task next

# Show task details
./dist/maestro task show <slug-or-id>

# Update task status
./dist/maestro task update <id> --status in_progress
./dist/maestro task update <id> --status completed
```

## Task JSON Schema

For batch task creation via `task plan --file`:

```json
{
  "tasks": [
    {
      "title": "Task title",
      "priority": 0,
      "type": "task",
      "description": "Optional description"
    }
  ]
}
```

**Priority values:**
- `0` = P0 (critical)
- `1` = P1 (high)
- `2` = P2 (medium)
- `3` = P3 (low)
- `4` = P4 (backlog)

**NOT** `"P0"`, `"P1"` strings — use integers 0-4.

**Task types:**
- `task` — single actionable item
- `epic` — large multi-phase initiative
- `bug` — defect or issue
- `chore` — maintenance work

## Common Workflows

### Create Tasks for a Project

**Option 1: Use `write_file` tool (recommended in Hermes sessions):**

```python
# Write JSON plan via write_file tool
write_file(
    path="/tmp/project_tasks.json",
    content='''
{
  "tasks": [
    {
      "title": "Setup database schema",
      "priority": 0,
      "type": "task",
      "description": "PostgreSQL tables for users, products, orders"
    },
    {
      "title": "Build REST API endpoints",
      "priority": 1,
      "type": "task",
      "description": "CRUD operations for all entities"
    },
    {
      "title": "Add authentication middleware",
      "priority": 1,
      "type": "task",
      "description": "JWT-based auth with refresh tokens"
    }
  ]
}
'''
)

# Then create tasks
terminal(command="export PATH=\"$HOME/.bun/bin:$PATH\" && cd ~/maestro && ./dist/maestro task plan --file /tmp/project_tasks.json")
```

**Option 2: Heredoc in terminal (if write_file unavailable):**

```bash
# Write JSON plan
cat > /tmp/project_tasks.json << 'EOF'
{
  "tasks": [
    {
      "title": "Setup database schema",
      "priority": 0,
      "type": "task",
      "description": "PostgreSQL tables for users, products, orders"
    }
  ]
}
EOF

# Create all tasks
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro
./dist/maestro task plan --file /tmp/project_tasks.json
```

**Why prefer write_file:** Heredoc with `&` backgrounding triggers terminal tool errors. Use `write_file` for JSON plans, then run `task plan` in a separate terminal call.

### Filter Tasks by Category

```bash
# List all tasks, grep for your project
./dist/maestro task list | grep -E "Website|Trading|Skripsi"

# List only ready tasks (no blockers)
./dist/maestro task ready | grep "Website"
```

### Work on Next Task

```bash
# Get next ready task (highest priority, no blockers)
./dist/maestro task next --json

# Claim a specific task
./dist/maestro task update <slug> --status in_progress

# Mark completed
./dist/maestro task update <slug> --status completed
```

## Task Slugs

Maestro auto-generates slugs from task titles:
- `"BAB III: Tambahkan black box testing"` → `implement/bab-iii-tambahkan-black`

Use slugs or task IDs (`tsk-XXXXXX`) interchangeably in commands.

## Mission Control (TUI)

Interactive terminal UI for task management:

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro
./dist/maestro mission-control
```

## Integration with Hermes

Maestro runs as a separate CLI tool. To integrate with Hermes workflows:

1. **Create tasks from Hermes session:**
   ```bash
   terminal(command="export PATH=\"$HOME/.bun/bin:$PATH\" && cd ~/maestro && ./dist/maestro task create 'Implement user authentication'")
   ```

2. **Check task status:**
   ```bash
   terminal(command="export PATH=\"$HOME/.bun/bin:$PATH\" && cd ~/maestro && ./dist/maestro task list | grep 'auth'")
   ```

3. **Update task after completion:**
   ```bash
   terminal(command="export PATH=\"$HOME/.bun/bin:$PATH\" && cd ~/maestro && ./dist/maestro task update implement/user-authentication --status completed")
   ```

## Pitfalls

### Priority Format Error

**Wrong:**
```bash
./dist/maestro task create "Task" --priority P1
# Error: Invalid --priority 'P1'. Priority must be one of 0, 1, 2, 3, 4
```

**Right:**
```bash
./dist/maestro task create "Task" --priority 1
```

Use integers 0-4, not P0-P4 strings.

### JSON Schema Mismatch

**Wrong:**
```json
{
  "tasks": [
    {"title": "Task", "priority": "P1"}  // String priority
  ]
}
```

**Right:**
```json
{
  "tasks": [
    {"title": "Task", "priority": 1}  // Integer priority
  ]
}
```

### Bun Not in PATH

If `./dist/maestro` fails with "command not found", add Bun to PATH:

```bash
export PATH="$HOME/.bun/bin:$PATH"
```

Or use absolute path: `~/.bun/bin/bun ~/maestro/dist/maestro`

## Task Status Lifecycle

```
pending → in_progress → completed
         ↓
      blocked (has unresolved blockers)
```

Use `task update <id> --status <status>` to move tasks through the lifecycle.

## See Also

- `references/verified-commands.md` → Complete command reference with verified examples and production workflows
- `hermes-agent` skill → Hermes ecosystem tools for Maestro installation
- `writing-plans` skill → Planning methodology that pairs well with Maestro
- `subagent-driven-development` skill → Delegate tasks to subagents, track in Maestro
