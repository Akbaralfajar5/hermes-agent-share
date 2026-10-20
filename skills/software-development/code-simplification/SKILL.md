---
name: code-simplification
description: Reduce code complexity while preserving exact behavior. Use after features work and tests pass but implementation feels heavy. Use during review when readability issues are flagged. Use when encountering deep nesting, long functions, or unclear names. Chesterton's Fence — understand before changing.
---

# Code Simplification

## Overview

Simplify code by reducing complexity while preserving exact behavior. Goal is not fewer lines — it's code that a new team member would understand faster. Every simplification must pass: "Would someone unfamiliar with this code grasp it quicker?"

## When to Use

- After a feature is working and tests pass, but implementation feels heavier than needed
- During code review when readability/complexity issues are flagged
- When encountering deeply nested logic, long functions, or unclear names
- After merging changes that introduced duplication or inconsistency
- When refactoring code written under time pressure

**When NOT to use:**
- Code is already clean and readable — don't simplify for the sake of it
- You don't understand what the code does yet — comprehend first
- Code is performance-critical and "simpler" version would be measurably slower
- About to rewrite the module entirely — simplifying throwaway code wastes effort

## The Five Principles

### 1. Preserve Behavior Exactly

Don't change what the code does — only how it expresses it. All inputs, outputs, side effects, error behavior, edge cases must remain identical.

```
ASK BEFORE EVERY CHANGE:
→ Same output for every input?
→ Same error behavior?
→ Same side effects and ordering?
→ All existing tests still pass without modification?
```

### 2. Follow Project Conventions

Simplification = making code more consistent with codebase, not imposing external preferences.

```
Before simplifying:
1. Read project conventions (AGENTS.md, CLAUDE.md, README)
2. Study how neighboring code handles similar patterns
3. Match: import ordering, function style, naming, error handling, type depth
```

Simplification that breaks project consistency is not simplification — it's churn.

### 3. Clarity Over Cleverness

Explicit code beats compact code when compact version requires a mental pause.

```typescript
// UNCLEAR: Dense ternary chain
const label = isNew ? 'New' : isUpdated ? 'Updated' : isArchived ? 'Archived' : 'Active';

// CLEAR: Readable mapping
function getStatusLabel(item: Item): string {
  if (item.isNew) return 'New';
  if (item.isUpdated) return 'Updated';
  if (item.isArchived) return 'Archived';
  return 'Active';
}
```

### 4. Maintain Balance

Over-simplification traps:
- **Inlining too aggressively** — removing a helper that gave a concept a name
- **Combining unrelated logic** — two simple functions merged into one complex function
- **Removing "unnecessary" abstraction** — some exist for extensibility/testability
- **Optimizing for line count** — fewer lines ≠ simpler

### 5. Scope to What Changed

Default to simplifying recently modified code. Avoid drive-by refactors of unrelated code unless explicitly asked. Unscoped simplification creates noise in diffs and risks regressions.

## The Simplification Process

### Step 1: Chesterton's Fence — Understand Before Touching

Before changing or removing anything, understand why it exists.

```
BEFORE SIMPLIFYING, ANSWER:
- What is this code's responsibility?
- What calls it? What does it call?
- Edge cases and error paths?
- Tests that define expected behavior?
- Why might it have been written this way?
- Check git log: what was original context?
```

If you can't answer these, read more context first.

### Step 2: Identify Simplification Opportunities

**Structural complexity:**
| Pattern | Signal | Fix |
|---------|--------|-----|
| Deep nesting (3+ levels) | Hard to follow flow | Extract guard clauses or helpers |
| Long functions (50+ lines) | Multiple responsibilities | Split into focused functions |
| Nested ternaries | Mental stack required | if/else, switch, or lookup |
| Boolean parameter flags | `doThing(true, false, true)` | Options objects or separate functions |
| Repeated conditionals | Same `if` in multiple places | Extract predicate function |

**Naming and readability:**
| Pattern | Signal | Fix |
|---------|--------|-----|
| Generic names (`data`, `result`, `temp`) | Meaningless | Rename to describe content |
| Abbreviated names (`usr`, `cfg`, `btn`) | Unclear | Full words unless universal (`id`, `url`) |
| Comments explaining "what" | Redundant | Delete — code is clear |
| Comments explaining "why" | Valuable | Keep — intent code can't express |

**Redundancy:**
| Pattern | Signal | Fix |
|---------|--------|-----|
| Duplicated logic (5+ lines) | Copy-paste | Extract shared function |
| Dead code | Unreachable/unused | Remove (confirm dead first) |
| Unnecessary abstractions | Wrapper adds no value | Inline directly |
| Over-engineered patterns | Factory-for-factory | Simple direct approach |

### Step 3: Apply Changes Incrementally

One simplification at a time. Run tests after each change.

```
FOR EACH SIMPLIFICATION:
1. Make the change
2. Run test suite
3. Pass → commit or continue
4. Fail → revert and reconsider
```

**Rule of 500:** If refactoring touches >500 lines, use automation (codemods, sed scripts, AST transforms), not manual edits.

### Step 4: Verify the Result

```
COMPARE BEFORE AND AFTER:
- Genuinely easier to understand?
- No new patterns inconsistent with codebase?
- Diff clean and reviewable?
- Would teammate approve as net improvement?
```

If "simplified" version is harder to understand — revert.

## Language-Specific Quick Reference

### Python
```python
# Verbose dict building → comprehension
result = {item.id: item.name for item in items}

# Nested conditionals → early return
def process(data):
    if data is None: raise TypeError("Data is None")
    if not data.is_valid(): raise ValueError("Invalid data")
    if not data.has_permission(): raise PermissionError("No permission")
    return do_work(data)
```

### TypeScript/JavaScript
```typescript
// Unnecessary async wrapper
function getUser(id: string): Promise<User> { return userService.findById(id); }

// Verbose conditional → concise
const displayName = user.nickname || user.fullName;
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It's working, no need to touch" | Working code that's hard to read will be hard to fix when it breaks |
| "Fewer lines is always simpler" | 1-line nested ternary ≠ simpler than 5-line if/else |
| "I'll quickly simplify unrelated code too" | Unscoped simplification = noisy diffs + regression risk |
| "Types make it self-documenting" | Types document structure, not intent |
| "This abstraction might be useful later" | Don't preserve speculative abstractions |
| "I'll refactor while adding this feature" | Separate refactoring from feature work |

## Red Flags

- Simplification requires modifying tests to pass (likely changed behavior)
- "Simplified" code is longer and harder to follow
- Renaming to match your preferences rather than project conventions
- Removing error handling "to make code cleaner"
- Simplifying code you don't fully understand
- Batching many simplifications into one untested commit

## Verification Checklist

- [ ] All existing tests pass without modification
- [ ] Build succeeds with no new warnings
- [ ] Linter/formatter passes
- [ ] Each simplification is reviewable, incremental change
- [ ] Diff is clean — no unrelated changes mixed in
- [ ] Simplified code follows project conventions
- [ ] No error handling removed or weakened
- [ ] No dead code left behind
