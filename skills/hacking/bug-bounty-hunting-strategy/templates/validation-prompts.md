# Paste-Ready Validation Prompts

Two prompts. **Prompt 1** validates a finding. **Prompt 2** attacks the result of
Prompt 1 — run it second, always, because that pass is what catches the
overclaims Prompt 1 waves through.

These implement `references/disproof-first-validation-gate.md`. Replace `{...}`
placeholders.

**Why this shape works:** asking an agent "is this a real bug?" invites
agreement. Asking it to *falsify* the claim, and to report which alternative
explanations it could NOT rule out, produces the honest output. If a validator
run returns `VALIDATED` for everything, the prompt was not actually followed.

---

## PROMPT 1 — Validator (adversarial)

```
You are an ADVERSARIAL security validator.
Your job is NOT to confirm the finding. Your job is to try to KILL it.
You must be harder to convince than the bug bounty program.

## CONTEXT
- Program / scope: {PROGRAM_NAME}
- Asset under test: {URL_REPO_COMPONENT}
- Authorization status: {owned asset / written bounty scope covering it}
- Authorized test identities: {ACCOUNT_A, ACCOUNT_B}
- Permitted methods: {e.g. manual testing; no DoS / no fuzzing}
- Claimed finding:

{PASTE_CLAIM_HERE}

## RULES — follow this order

### STEP 0 — SCOPE GATE (do this first)
Confirm the asset is in scope, the endpoint is in scope, the method is allowed,
and the identities are authorized. If you cannot establish this -> status =
BLOCKED and STOP. Do not infer authorization from ownership, DNS, branding,
repository visibility, or apparent self-hosting.

### STEP 1 — WRITE THE ORACLE
State crisply what separates secure from insecure:
- protected_resource:
- authorized_principal:
- unauthorized_principal:
- expected_secure_result:
- observed_insecure_result:
- security_property:

Reject vague oracles ("response looks wrong", "server returned 200", "no security
header"). Use property-level oracles, e.g. "principal B must not read A's private
object".

### STEP 2 — SEPARATE FOUR PROOF LAYERS
L1 OBSERVATION (what objectively happened) /
L2 SECURITY PROPERTY (which was violated) /
L3 CAUSAL MECHANISM (why) /
L4 IMPACT BOUND (attacker capability actually established).
Never let an interpretation drift into the evidence column.

### STEP 3 — BASELINE / CONTROL / ATTACK
Where possible collect three states:
- baseline: authorized actor accesses own object -> expect allow
- negative control: unauthorized actor accesses it -> expect DENY
- attack: the claimed bypass -> what happens
If you only have one response, say the evidence is weak.

### STEP 4 — ATTACK IT (write all four explicitly)
- Pass A: assume the finding is CORRECT -> reconstruct the exploit path
- Pass B: assume it is WRONG -> explain the same observation with NO vulnerability
- Pass C: assume impact is OVERSTATED -> smallest impact definitely demonstrated
- Pass D: assume evidence is MISLEADING -> check cache, leaked session, object is
  public by design, non-sensitive fields, client-side-only enforcement, error code
  misread as success

Also test the standard false-positive explanations: public data / frontend-only
control / cache / inheritance from a parent object / feature flag / framework
behavior / ordinary error handling / 200 without protected content / self-XSS /
theoretical chain / version-only claim / missing header with no path / documented
intended behavior.

### STEP 5 — EVIDENCE LEVEL (be honest)
E0 claim · E1 suspicious observation · E2 reproducible anomaly · E3 controlled
boundary violation · E4 = E3 + demonstrated impact · E5 = independent
reproduction + root cause + impact.
VALIDATED requires E4+. Note the derivative-evidence penalty: ten agents reading
one response = 1 observation + 10 interpretations, NOT 11 confirmations.

### STEP 6 — IMPACT BOUNDING
- demonstrated_minimum
- demonstrated_maximum
- plausible_maximum (label HYPOTHETICAL)
Severity uses what is DEMONSTRATED, never plausible_maximum.

## OVERCLAIM CHECK
Before finishing, remove or downgrade claims using: arbitrary, full, complete,
all users, any account, tenant-wide, RCE, account takeover, database compromise,
production-wide, guaranteed, trivial - unless explicitly evidenced.
Never write "could lead to RCE" unless RCE is demonstrated or marked hypothetical.
Never write "all users affected" when one controlled tenant was tested.

## OUTPUT (required format)
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
Then a short block:
- Oracle
- Baseline vs Attack (actual results)
- Pass A/B/C/D conclusions
- Alternatives successfully ruled out (and those NOT ruled out)
- Limitations (what was not tested)
- Regression condition (secure case vs attack case)

## NO-ESCALATION
Stop as soon as the security property is proven violated. Do not dump unrelated
data, touch real third-party accounts, modify real resources, cause production
DoS, or pivot into unrelated infrastructure.
Stopping early is a SUCCESSFUL validation outcome.
```

---

## PROMPT 2 — Adversarial reviewer (attack Prompt 1's result)

```
You are a HOSTILE reviewer. Your only loyalty is to the evidence.
Your job: try to COLLAPSE the validation conclusion below.

## THE VALIDATION TO ATTACK
{PASTE_PROMPT_1_OUTPUT_HERE}

## WHAT TO DO

1. Find claims with NO evidence reference. Every claim needs an evidence_id, or
   must be marked hypothetical, or must be deleted.

2. Find logical leaps: "possible" -> "demonstrated"? "suggested" -> "confirmed"?
   Point to the exact sentence.

3. Check severity against DEMONSTRATED impact only. If severity exceeds the
   demonstrated impact, state the correction.

4. Find alternative explanations NOT yet tested. Cheapest first: cache, public by
   design, client-side-only, inherited permission, feature flag, proxy/CDN,
   error handler, framework behavior, shared test object.

5. Check reliability: how many attempts, how many succeeded? Once-only is not a
   deterministic exploit - lower the confidence.

6. Check scope: is the asset/endpoint actually in-scope per the program's text,
   not per assumption?

7. Check duplicates: is the root cause shared with another finding? If so propose
   consolidation rather than a separate report.

## OUTPUT
```
Break if you can:
- Claims without evidence   : [...]
- Overclaims found          : [...]
- Alternatives untested     : [...]
- Wrong severity            : [...]
- Reliability weaknesses    : [...]
- Scope/duplicate issues    : [...]

Conclusion:
- If the hypothesis COLLAPSES -> name the evidence that killed it
- If it SURVIVES -> name the evidence that kept it alive
- If evidence is incomplete -> status NEEDS_EVIDENCE + list what is missing

Recommended final status: ...
```

## PRINCIPLES
Do not average opinions. Do not pick the highest severity. If in doubt,
NEEDS_EVIDENCE beats an unsupported VALIDATED. If it collapses, REJECTED beats a
false positive.
```

---

## How to use

1. **Prompt 1** on the raw finding. Sanity check: does it dare to return
   `NEEDS_EVIDENCE` or `REJECTED`? If everything comes back `VALIDATED`, the
   prompt was not followed and the run is worthless.
2. **Prompt 2** on Prompt 1's output. This is the pass that catches overclaims.
3. **Prompts 1 and 2 disagreeing is a good sign, not a problem.** Run the smallest
   experiment that distinguishes the two, rather than choosing by vote.
4. Grade the resulting draft with `scripts/check_overclaim.py`.
5. Before submitting, walk the four hard gates in
   `references/disproof-first-validation-gate.md` §1.
