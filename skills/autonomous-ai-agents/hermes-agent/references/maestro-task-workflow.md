# Maestro Task Management Workflow

Maestro is a task orchestration framework for Hermes Agent that implements Claude-style blocker graphs. It tracks tasks, dependencies, ownership, and status across multiple sessions and agents.

## Installation

```bash
# Install Bun runtime (required)
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"

# Clone and build Maestro
git clone https://github.com/ReinaMacCredy/maestro.git ~/maestro
cd ~/maestro
bun install
bun run build

# Verify
./dist/maestro --version
```

## Core Concepts

- **Task:** A unit of work with title, description, priority, status, and optional blockers
- **Slug:** Human-readable identifier (e.g., `implement/add-auth-middleware`)
- **Priority:** 0-4 (0 = critical, 4 = backlog) — NOT P0-P4
- **Status:** `pending`, `in_progress`, `completed`, `blocked`
- **Blocker graph:** Tasks can block other tasks; `task ready` shows only unblocked tasks

## Creating Tasks

### Single Task

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro

# Basic task
./dist/maestro task create "Add authentication middleware"

# With priority (0-4, not P0-P4)
./dist/maestro task create "Fix critical bug" --priority 0

# With description
./dist/maestro task create "Implement rate limiting" \
  --description "Add express-rate-limit middleware to all API routes"
```

**Pitfall:** Priority uses numeric values 0-4, NOT P0-P4 strings. Using `--priority P1` will fail with "Invalid --priority 'P1'".

### Batch Task Creation (Recommended)

For multiple related tasks, use JSON plan files:

```bash
# Create plan file
cat > /tmp/tasks.json << 'EOF'
{
  "tasks": [
    {
      "title": "Setup database schema",
      "priority": 0,
      "type": "task",
      "description": "Create PostgreSQL tables for user management"
    },
    {
      "title": "Implement user registration API",
      "priority": 1,
      "type": "task",
      "description": "POST /api/register endpoint with validation"
    },
    {
      "title": "Add email verification",
      "priority": 2,
      "type": "task",
      "description": "Send verification email after registration"
    }
  ]
}
EOF

# Import all tasks atomically
./dist/maestro task plan --file /tmp/tasks.json
```

**Output:**
```
[ok] 3 task(s) created
    --> tsk-abc123
    --> tsk-def456
    --> tsk-ghi789
```

**Benefits:**
- Atomic creation (all or nothing)
- Consistent formatting
- Easy to version control
- Can be generated programmatically

## Viewing Tasks

```bash
# List all tasks
./dist/maestro task list

# Filter by status
./dist/maestro task list --status pending
./dist/maestro task list --status in_progress

# Show only ready tasks (no blockers)
./dist/maestro task ready

# Show specific task details
./dist/maestro task show <id-or-slug>
./dist/maestro task show tsk-abc123
./dist/maestro task show implement/add-auth-middleware
```

**Slug vs ID:**
- **ID:** `tsk-abc123` (unique, never changes)
- **Slug:** `implement/add-auth-middleware` (human-readable, derived from title)

Most commands accept either.

## Working with Tasks

### Claim Next Task

```bash
# Get next ready task (highest priority, no blockers)
./dist/maestro task next

# JSON output for scripting
./dist/maestro task next --json
```

**Output:**
```json
{
  "task": {
    "id": "tsk-abc123",
    "title": "Setup database schema",
    "description": "Create PostgreSQL tables for user management",
    "type": "task",
    "priority": 0,
    "status": "pending",
    "slug": "implement/setup-database-schema",
    "assignee": "local-ubuntu",
    "claimedAt": "2026-05-04T10:43:24.166Z"
  }
}
```

**Note:** `task next` automatically claims the task for the current session. Use `task update` to change status as you work.

### Update Task Status

```bash
# Mark as in progress
./dist/maestro task update <id> --status in_progress

# Mark as completed
./dist/maestro task update <id> --status completed

# Reopen a completed task
./dist/maestro task reopen <id>
```

### Add Blockers

```bash
# Task A blocks Task B and C
./dist/maestro task block <task-a-id> <task-b-id> <task-c-id>

# Remove blocker
./dist/maestro task unblock <task-a-id> <task-b-id>
```

## Priority Levels

| Value | Name | Use Case |
|-------|------|----------|
| 0 | Critical | Production outages, security issues, blocking bugs |
| 1 | High | Important features, high-impact bugs |
| 2 | Medium | Standard features, minor bugs |
| 3 | Low | Nice-to-haves, refactoring |
| 4 | Backlog | Future work, ideas |

**Default:** Priority 2 (medium) if not specified.

## Task Types

- `task` — Standard work item (default)
- `epic` — Large feature spanning multiple tasks
- `bug` — Bug fix
- `chore` — Maintenance, refactoring, tooling

## Filtering and Searching

```bash
# Filter by priority
./dist/maestro task list --priority 0

# Filter by type
./dist/maestro task list --type bug

# Search by keyword (title, description)
./dist/maestro task list | grep -i "auth"

# Show only your tasks
./dist/maestro task mine

# Show stuck tasks (in_progress but no activity)
./dist/maestro task stuck
```

## Session Management

Maestro tracks which session owns which task. If a session dies, tasks can be released:

```bash
# List tasks owned by a session
./dist/maestro task mine

# Release tasks from a dead session
./dist/maestro task release-owned <session-id>

# Heartbeat to keep task alive
./dist/maestro task heartbeat <id>
```

## Mission Control (TUI)

Interactive terminal UI for task management:

```bash
./dist/maestro mission-control
```

**Features:**
- Visual task board
- Keyboard navigation
- Real-time updates
- Dependency graph view

## Integration with Hermes Agent

Maestro is designed to work alongside Hermes Agent sessions. Typical workflow:

1. **Plan tasks** in Maestro (via JSON plan file)
2. **Claim next task** with `task next`
3. **Work on task** in Hermes Agent session
4. **Update status** as you progress
5. **Mark completed** when done
6. **Repeat** with `task next`

**Example:**
```bash
# In terminal 1: Maestro
cd ~/maestro
./dist/maestro task next --json > /tmp/current_task.json

# In terminal 2: Hermes Agent
hermes chat -q "$(jq -r '.task.description' /tmp/current_task.json)"

# After completion
./dist/maestro task update $(jq -r '.task.id' /tmp/current_task.json) --status completed
```

## Common Pitfalls

### Priority Format

**Wrong:**
```bash
./dist/maestro task create "Fix bug" --priority P1  # FAILS
```

**Right:**
```bash
./dist/maestro task create "Fix bug" --priority 1   # WORKS
```

### Task Not Showing in `task ready`

**Cause:** Task has unresolved blockers.

**Fix:**
```bash
# Check blockers
./dist/maestro task show <id>

# Remove blocker if resolved
./dist/maestro task unblock <blocker-id> <blocked-id>
```

### Session ID Not Detected

**Symptom:** Warning message: `[info] no agent session detected; using a per-user synthesized session`

**Cause:** Maestro looks for `CODEX_THREAD_ID` or `CLAUDECODE` env vars to coordinate with agent sessions.

**Fix (optional):** Export session ID before running Maestro:
```bash
export CODEX_THREAD_ID=$(hermes sessions list | head -1 | awk '{print $1}')
./dist/maestro task next
```

**Note:** This is optional — Maestro works fine with synthesized sessions for single-user setups.

## Task Lifecycle

```
pending → in_progress → completed
   ↓           ↓
blocked    (can reopen)
```

- **pending:** Ready to work (if no blockers)
- **in_progress:** Currently being worked on
- **completed:** Done
- **blocked:** Waiting on another task

## Best Practices

1. **Use JSON plan files** for batch task creation — easier to review and version control
2. **Set priorities correctly** — 0 for critical, 1 for high, 2 for normal
3. **Add descriptions** — future you will thank you
4. **Use blockers** for dependencies — prevents working on tasks out of order
5. **Update status regularly** — keeps the task board accurate
6. **Use slugs for readability** — easier to remember than IDs

## Example Workflow: Skripsi Project

```bash
cd ~/maestro

# Create task plan
cat > /tmp/skripsi_tasks.json << 'EOF'
{
  "tasks": [
    {
      "title": "BAB III: Add black box testing instrument",
      "priority": 1,
      "type": "task",
      "description": "Add black box testing as instrument in BAB III methodology"
    },
    {
      "title": "BAB III: Add storyboard/wireframe in Design phase",
      "priority": 1,
      "type": "task",
      "description": "Include sitemap + 1 example wireframe in §3.4.2, full set in Lampiran"
    },
    {
      "title": "Run full programmatic audit on proposal",
      "priority": 2,
      "type": "task",
      "description": "Check TOC, figures, formatting, year consistency (2026), references"
    }
  ]
}
EOF

# Import tasks
./dist/maestro task plan --file /tmp/skripsi_tasks.json

# View tasks
./dist/maestro task list | grep "BAB III"

# Get next task
./dist/maestro task next

# Work on it in Hermes...

# Mark completed
./dist/maestro task update <id> --status completed
```

## Key Insights

- **Priority is 0-4, not P0-P4** — common mistake when coming from other task systems
- **JSON plan files are the best way to create multiple tasks** — atomic, reviewable, versionable
- **Slugs are derived from titles** — use descriptive titles for readable slugs
- **`task ready` shows only unblocked tasks** — use this to see what's actually actionable
- **Maestro is session-aware** — tasks can be claimed by specific sessions, preventing conflicts in multi-agent setups
