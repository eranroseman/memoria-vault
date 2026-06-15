---
topic: decisions
id: 44
title: L1 component tests live in a repo-side pytest tree, not inline in shipped modules
status: accepted
date_proposed: 2026-06-09
date_resolved: 2026-06-09
assumes: [29]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 44
---

# ADR-44: L1 component tests live in a repo-side pytest tree

## Context

[ADR-29](29-testing-framework.md) chose to host L1 component tests as inline
`python <module> --self-test` blocks inside each module. The stated rationale was
that the `vault/.memoria/` modules are a *distributed* artifact (the installer copies
them to user machines), so inline tests could **self-verify in situ**.

On review, that justification does not hold: nothing runs `--self-test` on a deployed
vault — not the installer, not any runtime or troubleshooting path. The tests ship to
user machines purely as a side effect of being inline, and are never exercised there.
The two things a post-install check would actually want are better served otherwise —
**corruption** by a checksum (the golden copy already carries a SHA-256 manifest, and
`golden_restore.py check` flags any drifted system file), and **environment** (wrong Python, missing deps) by the
installer's existing `pip install` plus a one-line import check. Neither needs the unit
tests to ship. Meanwhile the inline blocks bloat the modules, ship dead code to users,
and reinvent a test runner (`scripts/test.sh`'s hand-rolled `check()`).

## Decision

L1 component tests move to a conventional **repo-side `tests/` pytest tree** and are
**removed from the modules**. Each former `_self_test()` becomes `tests/test_<name>.py`;
a `conftest.py` wires the module directories onto `sys.path` (the hyphenated `scripts/`
tools load via `importlib`). `python-selftest.yml`, `scripts/test.sh`, and the
pre-commit hook run `pytest`. The deployed vault carries **zero test code**.

This **amends ADR-29's L1 implementation only** — the pyramid (L0–L5), the coverage
matrix, drift control, and gate mapping are unchanged. The installer-side **checksum +
import smoke check** is the right home for in-situ verification and is **deferred to
alpha.2**, when the installer is being reworked anyway.

## Consequences

- Test code stops shipping in `vault/.memoria/`; modules shrink to production code.
- `pytest` becomes a dev/CI dependency (it is **not** added to the vault runtime
  `requirements.txt` — the shipped runtime stays dependency-light).
- Standard tooling is available: fixtures, `pytest -k`, assertion introspection, and
  `coverage.py` can now measure the matrix instead of asserting it by hand.
- Until the alpha.2 installer work lands, a deployed install has **no** post-install
  self-check. This is the status quo (it never had one) — not a regression.

## Alternatives considered

**Keep inline self-tests (ADR-29 as written).** Rejected: the in-situ justification is
unrealized, and the cost (shipped dead code, bloated modules, a bespoke runner) is real.

**Thin pytest wrapper that subprocess-invokes the existing `--self-test`.** Rejected:
the test code would still live in — and ship with — the modules; it only adds a runner.

**Split by ship-boundary (pytest for `scripts/`, inline for `vault/`).** Rejected as the
end state: it keeps two mechanisms. A single tree is simpler, and the in-situ need is
met by the deferred installer checksum/import check instead.
