---
name: doubt-driven-development
description: Adversarial fresh-context review of every non-trivial decision in-flight. Use when stakes are high (production, security, irreversible), working in unfamiliar code, or a confident output is cheaper to verify now than to debug later. Spawn a subagent biased to DISPROVE, not approve.
---

# Doubt-Driven Development

## Overview

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts." Doubt-driven development materializes a **fresh-context reviewer** — biased to disprove — before any non-trivial output stands.

This is NOT code review post-commit. This is **in-flight cross-examination** while course-correction is still cheap.

## When to Use

A decision is **non-trivial** when ANY of these are true:
- Introduces or modifies branching logic
- Crosses a module or service boundary
- Asserts a property the type system cannot verify (thread safety, idempotence, ordering)
- Correctness depends on context the future reader cannot see
- Blast radius is irreversible (production deploy, on-chain tx, data migration, public API)

**When NOT to use:**
- Mechanical operations (renaming, formatting, file moves)
- Following a clear, unambiguous user instruction
- Reading or summarizing existing code
- One-line changes with obvious correctness
- User explicitly asked for speed over verification

## The Process

```
Doubt cycle:
- [ ] Step 1: CLAIM — wrote the claim + why-it-matters
- [ ] Step 2: EXTRACT — isolated artifact + contract, stripped reasoning
- [ ] Step 3: DOUBT — spawned fresh-context subagent with adversarial prompt
- [ ] Step 4: RECONCILE — classified every finding against the artifact text
- [ ] Step 5: STOP — met stop condition (trivial findings, 3 cycles, or user override)
```

### Step 1: CLAIM — Surface what stands

Name the decision in 2-3 lines:

```
CLAIM: "The new caching layer is thread-safe under read-heavy workload."
WHY THIS MATTERS: a race here corrupts user data and is hard to detect in QA.
```

If you can't write the claim that compactly, you have a vibe, not a decision.

### Step 2: EXTRACT — Smallest reviewable unit

A fresh-context reviewer needs the **artifact** and the **contract**, not the journey.

- Code: the diff or function — not the whole file
- Decision: proposal in 3-5 sentences + constraints it must satisfy
- Assertion: claim + supporting evidence (kept distinct from CLAIM)

**Strip your reasoning.** If you hand over conclusions, you'll get back validation of your conclusions.

### Step 3: DOUBT — Spawn fresh-context subagent

Use `delegate_task` to spawn a leaf subagent with an **adversarial prompt**:

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

**Pass ARTIFACT + CONTRACT only. Do NOT pass the CLAIM.** Handing the reviewer your conclusion biases it toward agreement.

**Hermes implementation:**
```python
delegate_task(
    goal="Adversarial code review — find issues only, do not validate",
    context="<adversarial prompt + ARTIFACT + CONTRACT>",
    toolsets=["terminal", "file"]  # read-only access
)
```

### Step 4: RECONCILE — Classify findings

The reviewer's output is data, not verdict. **You are still the orchestrator.** Re-read the artifact against each finding:

1. **Contract misread** — reviewer flagged something because CONTRACT was unclear. Fix contract, re-classify.
2. **Valid + actionable** — real issue, change the artifact, re-loop.
3. **Valid trade-off** — real but cost of fixing > cost of accepting. Document explicitly.
4. **Noise** — flagged something correct under context reviewer didn't have. Note it, move on.

### Step 5: STOP — Bounded loop

Stop when:
- Next iteration returns only trivial/already-considered findings, OR
- 3 cycles completed (escalate to user, don't grind a fourth), OR
- User says "ship it"

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "I'm confident, skip doubt" | Confidence correlates poorly with correctness on novel problems |
| "Spawning reviewer is expensive" | Debugging wrong commit in production is more expensive |
| "Reviewer will just nitpick" | Only if unscoped. Constrain prompt to "issues that would make this fail" |
| "I'll review at the end" | Post-hoc review catches problems when fix cost is highest |
| "If I doubt every step I'll never ship" | Applies to non-trivial decisions only, not every keystroke |

## Red Flags

- Spawning reviewer for a one-line rename
- Treating reviewer output as authoritative without re-reading artifact
- Looping >3 cycles without escalating to user
- Prompting reviewer with "is this good?" instead of "find issues"
- Skipping doubt under time pressure on high-stakes decision
- Doubt theater: 2+ cycles with substantive findings but zero classified as actionable

## Integration with Other Skills

- **requesting-code-review**: complementary. Code review is post-hoc verdict; doubt-driven is in-flight per-decision.
- **security-audit-review**: when reviewer surfaces security findings, drop into security audit.
- **systematic-debugging**: when reviewer surfaces a real failure mode, use debugging skill to localize.
- **test-driven-development**: TDD's RED step is doubt made concrete — a failing test is a disproof attempt.
