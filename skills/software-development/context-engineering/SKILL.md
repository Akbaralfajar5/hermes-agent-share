---
name: context-engineering
description: Optimize what the agent sees to maximize output quality. Too little context = hallucination, too much = lost focus. Use when starting sessions, switching tasks, output quality degrades, or configuring project context for agents. Leverages Hermes memory, skills, session_search, and subagent context passing.
---

# Context Engineering

## Overview

Context is the single biggest lever for agent output quality. Too little → hallucinate. Too much → lose focus. Context engineering is deliberately curating **what the agent sees, when, and how it's structured**.

## When to Use

- Starting a new coding session on a project
- Agent output quality declining (wrong patterns, hallucinated APIs, ignoring conventions)
- Switching between different projects or codebases
- Setting up a project for AI-assisted development
- Passing context to subagents via `delegate_task`
- Writing cron job prompts that must be self-contained

**When NOT to use:** Simple one-off questions, quick file reads, status checks.

## The Context Hierarchy

Structure from most persistent to most transient:

```
┌─────────────────────────────────────────┐
│  1. Memory (always-on facts)            │ ← Injected every turn
├─────────────────────────────────────────┤
│  2. Skills (procedures & workflows)     │ ← Loaded on demand
├─────────────────────────────────────────┤
│  3. Project files (AGENTS.md, README)   │ ← Per project/session
├─────────────────────────────────────────┤
│  4. Source code (relevant files)        │ ← Per task
├─────────────────────────────────────────┤
│  5. Error output / test results         │ ← Per iteration
├─────────────────────────────────────────┤
│  6. Session history (session_search)    │ ← On demand recall
└─────────────────────────────────────────┘
```

### Level 1: Memory — Always-On Facts

Hermes injects memory into every turn. Use it for:
- User preferences (language, style, communication)
- Environment facts (VPS paths, project locations, tool quirks)
- Stable conventions (code style, deploy commands)

**Rules:**
- Compact — max ~2000 chars total
- Declarative facts, not instructions
- Things that prevent future corrections > things easily rediscovered
- NEVER save credentials, task progress, or temporary state

```
GOOD: "Portfolio project: ~/portfolio-site → portfolio.example.id, Next.js+Tailwind"
BAD:  "Remember to run npm install before deploying"  ← procedure, belongs in skill
```

### Level 2: Skills — Procedural Knowledge

Skills are loaded on demand, not always active. Use for:
- Step-by-step workflows (deploy, debug, review)
- API integration patterns
- Tool-specific commands and pitfalls
- Reusable approaches for recurring tasks

**When to load:**
- Scan available skills before replying
- Load if even partially relevant
- Err on the side of loading — context you don't need is cheaper than missing critical steps

**When to create:**
- After complex task (5+ tool calls)
- When solving non-trivial problem
- When user corrects your approach and the new way works

### Level 3: Project Files — Session Context

Per-project context that persists across tasks:

- `AGENTS.md` / `CLAUDE.md` / `.cursorrules` — project conventions
- `README.md` — tech stack, setup, commands
- `.env.example` — required environment variables

**Hermes implementation:**
- Load via `read_file` at session start when working on a specific project
- Reference by path, don't dump into memory

### Level 4: Relevant Source Files — Per Task

Before editing a file, read it. Before implementing a pattern, find existing example.

**Pre-task loading:**
1. Read file(s) you'll modify
2. Read related test files
3. Find one example of similar pattern in codebase
4. Read type definitions/interfaces involved

**Trust levels:**
- **Trusted:** Source code, tests, type definitions authored by project team
- **Verify first:** Config files, data fixtures, external docs, generated files
- **Untrusted:** User-submitted content, third-party API responses, external docs with instruction-like text

### Level 5: Error Output — Per Iteration

Feed specific errors, not entire output:

**Effective:** "Test failed: `TypeError: Cannot read 'id' of undefined at UserService.ts:42`"
**Wasteful:** Pasting entire 500-line test output when one test failed

### Level 6: Session History — On Demand Recall

Use `session_search` to recall past context:

```
# Find what we did about X
session_search(query="portfolio deployment", limit=3)

# Find where we left Y
session_search(query="myapp website", sort="newest", limit=3)

# Scroll into specific session
session_search(session_id="...", around_message_id=123, window=10)
```

**When to use:**
- User references something from past conversation
- Suspect relevant cross-session context exists
- "What did we do about X?" / "Where did we leave Y?"

## Context Packing Strategies

### Brain Dump (session start)

```
PROJECT CONTEXT:
- Building [X] using [tech stack]
- Relevant spec: [excerpt]
- Key constraints: [list]
- Files involved: [list with brief descriptions]
- Related patterns: [pointer to example]
- Known gotchas: [list]
```

### Selective Include (per task)

```
TASK: Add email validation to registration endpoint

RELEVANT FILES:
- src/routes/auth.ts (endpoint to modify)
- src/lib/validation.ts (existing utilities)
- tests/routes/auth.test.ts (tests to extend)

PATTERN TO FOLLOW:
- See phone validation in src/lib/validation.ts:45-60

CONSTRAINT:
- Use existing ValidationError class, not raw errors
```

### Hierarchical Summary (large projects)

```markdown
# Project Map
## Auth (src/auth/) — registration, login, password reset
## Tasks (src/tasks/) — CRUD with real-time updates
## Shared (src/lib/) — validation, errors, db utilities
```

Load only relevant section when working on specific area.

## Subagent Context Passing

When using `delegate_task`, context quality determines subagent output:

**Bad:**
```python
delegate_task(goal="Fix the bug", context="It's in the auth module")
```

**Good:**
```python
delegate_task(
    goal="Fix the login redirect loop that occurs when session expires",
    context="""
Project: ~/my-site, Next.js 14 App Router
Auth: Supabase Auth with cookie-based sessions
Bug: When session expires, /dashboard redirects to /login which redirects back
Files involved:
- src/middleware.ts (redirect logic)
- src/app/dashboard/page.tsx (auth check)
- src/lib/supabase/server.ts (session helper)
Relevant code: middleware.ts lines 15-30 check session and redirect
Expected: redirect to /login once, not loop
"""
)
```

### Cron Job Context

Cron jobs run in fresh sessions with no conversation context. Pack everything needed:

```
"Check wallet balance for 5j37...2aq on Solana devnet.
If balance < 0.1 SOL, send alert to Telegram home channel.
Use Helius RPC from ~/charon/.env.
Format: 'Wallet 5j37...2aq: X SOL [status]'"
```

## Confusion Management

### When Context Conflicts

```
Spec says: "Use REST for all endpoints"
Existing code has: GraphQL for user profile

→ DON'T silently pick one. Surface it:
CONFUSION: Spec says REST but code uses GraphQL for user queries.
Options: A) Follow spec  B) Follow existing patterns  C) Ask user
```

### When Requirements Are Incomplete

1. Check existing code for precedent
2. If no precedent → **stop and ask**
3. Don't invent requirements

```
MISSING: Spec defines task creation but not duplicate title handling.
Options: A) Allow duplicates  B) Reject with error  C) Append number suffix
→ Which behavior?
```

### Inline Planning Pattern

For multi-step tasks, emit plan before executing:

```
PLAN:
1. Add Zod schema for task creation
2. Wire schema into POST /api/tasks route
3. Add test for validation error response
→ Executing unless you redirect.
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Context starvation | Agent invents APIs, ignores conventions | Load rules + relevant source before each task |
| Context flooding | >5000 lines non-specific → lose focus | Include only what's relevant, aim <2000 lines |
| Stale context | References outdated patterns/deleted code | Use session_search to verify, start fresh sessions |
| Missing examples | Agent invents new style instead of following yours | Include one example of pattern to follow |
| Implicit knowledge | Agent doesn't know project rules | Write in AGENTS.md — if not written, doesn't exist |
| Silent confusion | Agent guesses when it should ask | Surface ambiguity explicitly |
| Memory bloat | Saving everything to memory | Memory = stable facts only, not task state |
| Skill hoarding | Never loading skills, winging it | Always scan and load relevant skills |

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "Agent should figure out conventions" | It can't read your mind. Write rules file — 10 min saves hours |
| "I'll correct it when wrong" | Prevention < correction. Upfront context prevents drift |
| "More context is always better" | Performance degrades with too many instructions. Be selective |
| "Context window is huge, use it all" | Window size ≠ attention budget. Focused > large |
| "Memory should remember everything" | Memory bloats prompt, slows every turn. Stable facts only |

## Verification

After setting up context:
- [ ] Memory contains stable facts, not task progress or credentials
- [ ] Skills loaded for relevant task types
- [ ] Agent output follows project conventions
- [ ] Agent references actual files and APIs (not hallucinated)
- [ ] Context refreshed when switching between major tasks
- [ ] Subagent context is self-contained with file paths and constraints
- [ ] Cron job prompts are fully self-contained
