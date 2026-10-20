# Disproof-First Validation Gate

Adversarial reviewer layer, distilled from an operator-supplied "maximum
assurance" validation framework (80 sections) into what is actually runnable.

*hypotheses, not confirmed bugs* and that a long audit often self-invalidates.
This reference is the missing half — the discipline for *killing* a claim before
it reaches a report. §3 says "reproduce before reporting"; this says "try to
disprove before reproducing, then bound the impact to what survived."

Apply it BEFORE severity assignment. Severity derived from an unvalidated claim
is the most expensive error in the reporting pipeline — it is what turns a
Medium into a rejected "Critical" and burns a program's trust.

---

## 1. The four hard gates (fail any ⇒ do NOT write "validated")

```
[ ] SCOPE       — asset + endpoint + method + identity all authorized
[ ] BOUNDARY    — a NAMED security control is actually violated
[ ] BEHAVIOR    — control-case vs attack-case compared (baseline established)
[ ] IMPACT      — attacker gain DEMONSTRATED, not "possible"
```

A finding is not validated because another agent says so, not because a scanner
flagged it, not because the code looks dangerous. It is validated because
independent evidence survived an attempt to invalidate it.

Anything not established ⇒ honest status is `NEEDS_EVIDENCE`. That is a
*successful* validation outcome, not a failure of effort. Prefer
`NEEDS_EVIDENCE` over an unsupported `VALIDATED`; prefer `REJECTED` over a false
positive.

---

## 2. Write the oracle before testing anything

The oracle is the rule separating secure from insecure behavior. If you cannot
state it crisply, you do not yet understand the finding.

```yaml
oracle:
  protected_resource:        # what should be protected
  authorized_principal:      # who is allowed
  unauthorized_principal:    # who is not
  expected_secure_result:    # what should happen
  observed_insecure_result:  # what actually happened
  security_property:         # confidentiality|integrity|availability|authorization|authentication|isolation
```

**Rejected as oracles (symptoms, not oracles):** "response looks wrong" ·
"server returned 200" · "security header missing" · "parameter is reflected".

**Property-level oracles (accept):** principal B must not read A's private
object · a user without the permission must not transition the protected state ·
an untrusted URL must not make the server reach a restricted network location ·
untrusted markup must not execute in a privileged origin · a session created for
A must not become authenticated as B.

---

## 3. Baseline / negative-control / attack triad

Whenever a controlled comparison is possible, a single anomalous response is
**not** enough.

| Case | Identity | Object | Expected |
|---|---|---|---|
| A — baseline | owner | own | allow |
| B — negative control | non-owner | other's | **deny** |
| C — attack | non-owner | other's (claimed bypass) | deny |

If A succeeds and B *unexpectedly also succeeds*, the signal is far stronger than
one 200. With only C, say so and downgrade. Do not manufacture unauthorized
identities outside the authorized test setup — use dedicated test objects.

---

## 4. Four adversarial passes (write them, don't just think them)

- **Pass A — assume it is CORRECT.** Reconstruct the intended exploit path.
- **Pass B — assume it is WRONG.** Explain the *same* observation with no vuln.
- **Pass C — assume impact is OVERSTATED.** Find the smallest impact that is
  *definitely* demonstrated.
- **Pass D — assume evidence is MISLEADING.** Did a proxy alter the request? Did
  auth state leak between sessions? Was the object intentionally public? Are the
  fields non-sensitive? Was a client-side restriction mistaken for server-side
  authorization? Was `200` read as success without protected content or action?

If Pass B or D still stands unexplained, you are not done.

---

## 5. False-positive kill list

Reject or downgrade when any of these explains the observation:

- scanner signature with no proof / version-only claim
- missing header with no meaningful exploit path
- verbose error with no sensitive disclosure
- frontend-only restriction while server-side control is intact
- public data mistaken for private
- test fixture that is intentionally accessible
- self-XSS without a meaningful boundary
- theoretical chain of multiple unproven bugs
- race that cannot be reproduced or does not alter protected state
- `200 OK` read as authorization without protected content/action
- source sink unreachable from attacker-controlled input
- DNS/redirect/parser quirk with no security consequence
- behavior documented as intended and correctly enforced

---

## 6. Evidence levels + the derivative-evidence penalty

```
E0 assertion only
E1 suspicious observation
E2 reproducible behavioral anomaly
E3 controlled security-boundary violation
E4 E3 + demonstrated impact
E5 independent reproduction + root-cause evidence + demonstrated impact
```

`VALIDATED` requires **E4+**; high-impact findings should reach E5.

**Derivative-evidence penalty:** ten agents analyzing the same HTTP response =
`1 raw observation + 10 interpretations`, **not** 11 independent confirmations.
Repetition is not corroboration. A single high-quality artifact can outweigh
many derivative observations.

**Agreement is not proof.** A technically correct minority conclusion can defeat
a majority. Never count votes as evidence; never average disagreement into fake
certainty — run the smallest experiment that distinguishes the hypotheses. This
is the anti-collusion rule that makes multi-agent audit (§3 of the parent) safe
to use at all.

---

## 7. Impact bounding — severity comes from the demonstrated tier only

```yaml
impact:
  demonstrated_minimum:     # definitely proven
  demonstrated_maximum:     # tested; this is the observed ceiling
  plausible_maximum:        # UNTESTED — label hypothetical
```

Severity comes from `demonstrated_*`. "Plausible maximum" is never grounds for a
higher severity.

---

## 8. Overclaim detector

Scan the draft for these; each needs explicit supporting evidence or must be
rewritten/removed:

`arbitrary` · `full` · `complete` · `all users` · `any account` · `tenant-wide`
· `RCE` · `account takeover` · `database compromise` · `production-wide` ·
`catastrophic` · `guaranteed` · `trivial`

Never write:
- "could lead to RCE" unless RCE is demonstrated or explicitly marked hypothetical
- "Critical" without demonstrated critical impact
- "full account takeover" when only partial token disclosure was proven
- "all users affected" when only one controlled tenant was tested

**The framing that survives review:**

> "The tested low-privileged account can access object X belonging to the
> controlled test account Y without the expected ownership check. This
> demonstrates cross-account object disclosure on this endpoint. Broader
> tenant-wide impact was not tested."

Reads "weaker", is strictly more credible, and protects the report from an
overclaim downgrade.

---

## 9. Remediation causality + regression

Bad: "add a frontend check."
Better: "enforce server-side authorization against the authenticated principal
and the target object's ownership/tenant context before the operation."

If the root cause is unknown, do not fabricate a precise patch — state the
verified boundary and the control required.

```yaml
regression:
  secure_case:              # should pass after fix
  attack_case:              # should fail before fix
  expected_secure_result:
  failure_signature:
```

---

## 10. Stop conditions (stopping early is a SUCCESS)

Stop when: the property is conclusively disproven; the target is out of scope;
further testing needs unsafe impact; evidence suffices for the minimum claim; or
continuing would touch unrelated real-user data.

**No-escalation principle:** establish the minimum proof of the claimed impact,
never the maximum compromise achievable. Do not dump unrelated data, access real
third-party accounts, modify real resources, create persistence, cause
production DoS, or pivot into unrelated infrastructure.

---

## 11. Duplicate analysis by root cause, not endpoint

```
Root Cause RC-01
 ├── endpoint A
 ├── endpoint B
 └── endpoint C
```

One missing authorization control across many endpoints = **one systemic
finding**, not N reports. Identical symptoms from different mechanisms must NOT
be collapsed. Cluster by: root cause, violated property, attacker capability,
affected trust boundary, remediation unit.

For this operator's duplicate-sensitive context (a program's duplicate rate is
the top enemy, per §0 of the parent), consolidating by root cause also raises the
signal-to-noise of the submission.

---

## 12. Machine-readable output contract

```yaml
result:
  status: VALIDATED|REJECTED|DUPLICATE|INFORMATIONAL|BLOCKED|NEEDS_EVIDENCE
  confidence: high|medium|low
  maturity: M0..M6
  demonstrated_impact: "..."
  severity: informational|low|medium|high|critical
  duplicate_of: null
  evidence_ids: []
  unresolved_questions: []
  overclaims_removed: []
  rationale: "..."
```

No prose-only finalization for high-impact findings.

---

## 13. Validation budget — uncertainty × impact

```
Priority = ImpactPotential × EvidenceUncertainty × ExploitabilityUncertainty
```

High-impact/high-uncertainty gets deeper independent validation. Low-impact/
high-confidence must not consume the whole effort. Do not spawn a fixed ritual
number of agents — route specialists to what is actually uncertain.

---

## 14. Boundary discipline (reinforces parent §10)

The framework that produced this reference is explicitly for **authorized,
self-hosted, in-scope** testing. Its own Gate 1 is a scope check that runs
*before* technical validation.

So: a validation framework is not an authorization. When handed a third-party
target with no scope evidence, the correct Gate 1 result is `BLOCKED`, and the
right move is to say so and offer the framework as a tool for assets the
operator actually owns or is contracted to test. Building someone a toolkit is
fine; pointing it at a stranger's production system is not.

---

## 15. Operator-preference notes (observed)

- Wants a **practical artifact**, not a restatement of the theory: checklist +
  paste-ready prompt + report template + a runnable checker. Distil; do not
  summarize the source document back to him.
- When the source material is a very long framework (80 sections), the value you
  add is **selection** — which ~15 sections actually change behaviour — plus the
  one thing the framework lacks. Here that was an automated overclaim grader
  (`scripts/check_overclaim.py` equivalent: regex the risky vocabulary, flag
  unhedged hits, verify required report sections exist, count concrete evidence
  refs). Test any such grader against a deliberately bad draft AND a good one;
  if it cannot separate them it is not doing anything.
- Casual Indonesian in prose; keep code/identifiers in English.
