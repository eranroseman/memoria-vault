---
release: v0.1.0-alpha.10
status: draft        # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- v0.1.0-alpha.10
parent: Releasing
nav_order: 2
---

# Release plan -- v0.1.0-alpha.10

**Current status: draft internal checkpoint.** alpha.10 scope is not finalized.
The first carryover is
[#859](https://github.com/eranroseman/memoria-vault/issues/859): decide, from
observed usage, whether measurement-led memory work or Hermes cleanup should be
the next real bottleneck to address. It is not a formal release: no
release-please PR, no tag, and no GitHub Release.

## 1. Scope -- what this release is

alpha.10 starts as a carryover checkpoint for #859. Do not add the NLI/MaxSAT
contradiction engine, new memory machinery, or Hermes cleanup work to scope until
the baseline in #859 shows that work is worth doing.

## 2. Definition of done -- gates

v0.1.0-alpha.10 ships when every gate sub-issue under the release parent issue is
closed. Create the parent and gates when scope is shaped.

| Gate | Proves | Verified by | Issue |
| --- | --- | --- | --- |
| G1 | Baseline and scope decision recorded for #859. | S0 + issue evidence | — |

## 3. Validation -- stages

The staged test plan will be finalized after scope is shaped.

| Stage | Proves |
| --- | --- |
| S0 | `static-contract`: release docs, links, spelling, and status checks are clean. |

## 4. Blockers

Not enumerated here. By definition the blockers are any open gate/stage
sub-issue, plus any open High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (later)

- Full NLI/decomposed-gate/MaxSAT contradiction automation remains out of scope
  unless #859 proves missed contradictions are a real bottleneck.
- Broad Hermes cleanup remains out of scope unless #859 selects a specific item
  and assigns it to alpha.10.

## 6. Known limitations

- Limitation: alpha.10 is a draft internal checkpoint. Impact: there is no release
  artifact or frozen scope yet. Workaround: use #859 and future release issues as
  the live state. Tracking:
  [#859](https://github.com/eranroseman/memoria-vault/issues/859).

## 7. Documentation integrity

Before the checkpoint is approved, run the standard docs sweep: `docs_doctor`,
`status_doctor`, `check_test_refs`, cspell, and a manual scan for changed behavior.

## 8. Runtime readiness

Runtime evidence is required only for scoped work that changes installed behavior.
Do not test against the production vault.

## 9. Release close-out sweep

Before closeout, move unfinished scratch forward, fold durable findings into
ADRs/docs/issues, and delete completed `tmp/` files only after disposition.

## 10. Cut procedure

1. Close every gate and stage issue under the release parent.
2. Complete documentation and runtime readiness checks for scoped work.
3. Do not cut a tag or GitHub Release for this internal checkpoint.
4. Set this plan to `status: complete`, `released: false`.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Measurement-led memory work | After #859 baseline | Decide whether contradiction, retrieval, ingest, or supervision attribution is the next bottleneck. |
| Hermes cleanup | After #859 triage | Pick only the cleanup item that pays for itself. |

## 12. Appendix

No appendix yet.
