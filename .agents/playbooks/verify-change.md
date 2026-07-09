# Verify a change

Verification demonstrates the requested behavior rather than merely showing
that code compiles. [Test selection](../system/test-selection.md) owns which
commands to run; this playbook owns claims, evidence, and reporting.

## 1. State the claim

Write one observable claim for each requested outcome:

```text
Given <starting state>, when <action occurs>, then <observable result> follows.
```

Include failure behavior and important unchanged behavior where relevant.

## 2. Collect evidence

Use the lowest-cost evidence that proves the claim. Start with a focused test or
direct command when one proves the behavior; promote to `scripts/verify` gates
only as required by [Test selection](../system/test-selection.md).

Do not test installers against the real `~/Memoria`. Do not claim live-runtime
verification when only static or synthetic tests ran.

## 3. Execute

- Start with the narrow regression test.
- Run related tests for the affected component.
- Compare actual output and side effects with the stated claim.
- Inspect logs, generated files, audit entries, or diffs when those are part of
  the contract.
- Clean up only artifacts created by this verification run.

Manual adapter checks apply only when an optional adapter is in scope. Record
release or manual evidence in the relevant release parent issue or sub-issue,
not in docs.

## 4. Record

Report:

- Claims verified
- Commands or interactions performed
- Relevant results
- Tests not run and the concrete reason
- Residual risk that needs a live runtime, Windows, Obsidian, network access, or
  another unavailable dependency

“Tests pass” is supporting evidence, not the entire verification report.

*(If `superpowers:verification-before-completion` is installed, its
claim-honesty discipline complements this playbook. These steps remain
authoritative regardless.)*
