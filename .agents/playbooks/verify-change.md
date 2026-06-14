# Verify a change

Verification demonstrates the requested behavior rather than merely showing
that code compiles.

## 1. State the claim

Write one observable claim for each requested outcome:

```text
Given <starting state>, when <action occurs>, then <observable result> follows.
```

Include failure behavior and important unchanged behavior where relevant.

## 2. Choose evidence

Use the lowest-cost evidence that proves the claim:

1. Focused unit or component test
2. Direct command or CLI reproduction
3. Offline integration or smoke test
4. Disposable-vault installer test
5. Hermes/Obsidian runtime or attended GUI test

Do not test installers against the real `~/Memoria`. Do not claim live-runtime
verification when only static or synthetic tests ran.

## 3. Execute

- Start with the narrow regression test.
- Run related tests for the affected component.
- Use `scripts/test.sh all` for shared behavior or before PR handoff.
- Compare actual output and side effects with the stated claim.
- Inspect logs, generated files, audit entries, or diffs when those are part of
  the contract.
- Clean up only artifacts created by this verification run.

## 4. Record

Report:

- Claims verified
- Commands or interactions performed
- Relevant results
- Tests not run and the concrete reason
- Residual risk that needs a live runtime, Windows, Obsidian, network access, or
  another unavailable dependency

“Tests pass” is supporting evidence, not the entire verification report.
