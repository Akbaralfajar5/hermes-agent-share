---
name: incremental-implementation
description: Build features in thin vertical slices — implement, test, verify, commit. Use when implementing any multi-file change, building features from plans, or when a task feels too big to land in one step. Max ~100 lines before testing.
---

# Incremental Implementation

## Overview

Build in thin vertical slices — implement one piece, test it, verify it, commit, then expand. Each increment leaves the system in a **working, testable state**. This is the execution discipline that makes large features manageable.

## When to Use

- Implementing any multi-file change
- Building a new feature from a task breakdown or plan
- Refactoring existing code
- Any time tempted to write more than ~100 lines before testing
- When delegated a task from `writing-plans` or `plan` skill

**When NOT to use:** Single-file, single-function changes where scope is already minimal.

## The Increment Cycle

```
Implement → Test → Verify → Commit → Next slice
     ▲                                     │
     └─────────────────────────────────────┘
```

For each slice:
1. **Implement** — smallest complete piece of functionality
2. **Test** — run test suite (or write test if none exists)
3. **Verify** — confirm slice works (tests pass, build succeeds, manual check)
4. **Commit** — save progress with descriptive message
5. **Next slice** — carry forward, don't restart

## Slicing Strategies

### Vertical Slices (Preferred)

Build one complete path through the stack:

```
Slice 1: Create task (DB + API + basic UI) → tests pass, user can create
Slice 2: List tasks (query + API + UI) → tests pass, user can see tasks
Slice 3: Edit task (update + API + UI) → tests pass, user can modify
Slice 4: Delete task (delete + API + UI) → tests pass, full CRUD
```

Each slice delivers working end-to-end functionality.

### Contract-First Slicing

When backend and frontend develop in parallel:

```
Slice 0: Define API contract (types, interfaces, endpoints)
Slice 1a: Backend against contract + API tests
Slice 1b: Frontend against mock data matching contract
Slice 2: Integrate and test end-to-end
```

### Risk-First Slicing

Tackle riskiest piece first:

```
Slice 1: Prove WebSocket connection works (highest risk)
Slice 2: Build real-time updates on proven connection
Slice 3: Add offline support and reconnection
```

If Slice 1 fails, discover before investing in 2 and 3.

## Implementation Rules

### Rule 0: Simplicity First

Before writing code: "What is the simplest thing that could work?"

```
SIMPLICITY CHECK:
✗ Generic EventBus with middleware for one notification
✓ Simple function call

✗ Abstract factory for two similar components
✓ Two straightforward components

✗ Config-driven form builder for three forms
✓ Three form components
```

Three similar lines is better than premature abstraction. Implement naive, obviously-correct first. Optimize only after correctness proven.

### Rule 0.5: Scope Discipline

Touch only what the task requires.

**Do NOT:**
- "Clean up" code adjacent to your change
- Refactor imports in files you're not modifying
- Remove comments you don't fully understand
- Add features not in the spec
- Modernize syntax in files you're only reading

If you notice something worth improving outside scope — note it, don't fix it:
```
NOTICED BUT NOT TOUCHING:
- src/utils/format.ts has unused import (unrelated)
- Auth middleware could use better error messages (separate task)
→ Want me to create tasks for these?
```

### Rule 1: One Thing at a Time

Each increment changes one logical thing. Don't mix concerns.

**Bad:** One commit adding component + refactoring existing one + updating build config.
**Good:** Three separate commits.

### Rule 2: Keep It Buildable

After each increment, project must build and existing tests must pass. Don't leave codebase broken between slices.

### Rule 3: Feature Flags for Incomplete Features

```typescript
const ENABLE_SHARING = process.env.FEATURE_SHARING === 'true';
if (ENABLE_SHARING) { /* new sharing UI */ }
```

Merge small increments without exposing incomplete work.

### Rule 4: Safe Defaults

New code defaults to safe, conservative behavior:
```typescript
export function createTask(data: TaskInput, options?: { notify?: boolean }) {
  const shouldNotify = options?.notify ?? false;
  // ...
}
```

### Rule 5: Rollback-Friendly

Each increment independently revertable:
- Additive changes (new files) are easy to revert
- Modifications should be minimal and focused
- DB migrations should have rollback migrations
- Don't delete + replace in same commit — separate them

## Working with Subagents

When using `delegate_task` for implementation:

```
"Implement Task 3 from the plan.
Start with DB schema + API endpoint only.
Don't touch UI yet — next increment.
After implementing, run tests to verify nothing broke."
```

Be explicit about what's in scope and NOT in scope per increment.

For large plans (10+ tasks), use `subagent-driven-development` skill with this incremental approach embedded.

## Hermes-Specific Patterns

### Using `execute_code` for multi-step

When you need 3+ tool calls with processing logic between them:

```python
from hermes_tools import terminal, read_file, patch

# Step 1: Implement
patch(path="src/api/tasks.ts", old_string="...", new_string="...")

# Step 2: Test
result = terminal("npm test -- --testPathPattern=tasks")
if result["exit_code"] != 0:
    print(f"FAIL: {result['output']}")
else:
    # Step 3: Commit
    terminal("git add -A && git commit -m 'feat: add task creation endpoint'")
    print("Slice complete ✓")
```

### Using `todo` for tracking slices

```
todo(todos=[
    {"id": "1", "content": "DB schema + migration", "status": "in_progress"},
    {"id": "2", "content": "API endpoint + validation", "status": "pending"},
    {"id": "3", "content": "Frontend component", "status": "pending"},
    {"id": "4", "content": "Integration test", "status": "pending"}
])
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "I'll test it all at the end" | Bugs compound. Bug in Slice 1 makes Slices 2-5 wrong |
| "Faster to do it all at once" | Feels faster until something breaks and you can't find which of 500 lines caused it |
| "Too small to commit separately" | Small commits are free. Large commits hide bugs |
| "I'll add feature flag later" | If feature isn't complete, it shouldn't be user-visible |
| "This refactor is small enough to include" | Mixed changes are harder to review and debug |
| "Let me run build again just to be sure" | After successful run, repeating adds nothing unless code changed |

## Red Flags

- More than 100 lines written without running tests
- Multiple unrelated changes in single increment
- "Let me just quickly add this too" scope expansion
- Skipping test/verify step to move faster
- Build or tests broken between increments
- Large uncommitted changes accumulating
- Building abstractions before third use case
- Touching files outside task scope "while I'm here"
- Running same build/test command twice without code change between

## Verification

After completing all increments for a task:
- [ ] Each increment individually tested and committed
- [ ] Full test suite passes
- [ ] Build is clean
- [ ] Feature works end-to-end as specified
- [ ] No uncommitted changes remain
