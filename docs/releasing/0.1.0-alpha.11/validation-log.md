---
title: 0.1.0-alpha.11 validation log
parent: 0.1.0-alpha.11
grand_parent: Releasing
nav_order: 3
---

# 0.1.0-alpha.11 validation log

Date: 2026-06-29

Runtime candidate commit: `39d22f6e` (`agent/alpha11-next` from then-current
`main`), clean worktree at verification time. Later documentation-only closeout
commits preserve this runtime evidence without changing alpha.11 runtime code.

This is internal checkpoint evidence only. No release-please PR, tag, GitHub
Release, migration, upgrade path, or backwards-compatibility work is part of the
alpha.11 close-out path.

## Automated and headless gates

`scripts/verify rc --evidence-dir /tmp/memoria-alpha11-next-rc-escalated` passed.

- Source Gate: `bash scripts/test.sh all` passed with `607 passed`, including
  the L1 pytest suite plus static, docs, provenance, schema, and lint checks.
- Package Gate: `bash scripts/e2e-smoke.sh` passed. The disposable vault
  assembled, golden-copy drift stayed at zero, commit-gate checks ran, offline
  ingest and the alpha.11 argument canvas replay completed, and final integrity
  checks were green.
- Runtime Gate: `python3 -m pytest tests/test_alpha11_cycle.py -q` passed for
  the deterministic source-to-gap worker cycle. `bash scripts/test-l2.sh` passed
  against Hermes `v0.17.0` with the deterministic OpenAI-compatible smoke
  endpoint, including a denied direct Obsidian write and a recorded policy-gate
  deny audit row for task `20eef818-432e-4364-ab4a-1d3b4198a6db`.

Host evidence in the RC summary:

- Hermes: `Hermes Agent v0.17.0 (2026.6.19)`, upstream `190e1ffa`.
- Platform: WSL2 Linux `6.6.87.2-microsoft-standard-WSL2`, Python `3.13.12`.
- Evidence file: `/tmp/memoria-alpha11-next-rc-escalated/summary.json`.

## Test-vault runtime

The now-retired start-blocker verifier passed from the `Memoria-test` runtime
venv before `tmp/` disposition.

Covered evidence:

- disposable qmd bundle index/search;
- Zotero Local API item shape. Zotero is in scope only for item/source import;
  Zotero annotations are not an alpha.11 capability or release gate;
- PDF parser quote/page/span/bbox preservation;
- Inspector plugin file parity, REST manifest read, command registration,
  command execution, and workspace-view registration;
- worker queue `answer-query` dispatch in `Memoria-test`;
- `source_id` stability across citekey changes.

The verifier still reports the Inspector check as `partial-live-command` because
the command was activated through Obsidian REST but live visual rendering was not
pixel- or human-verified in this run.

## Product and quality evidence

`tests/test_alpha11_cycle.py` covers the deterministic source-to-gap cycle:
capture, Co-PI interview, digest/hub outputs, anchored note, gap re-run, Ask,
checked-only qmd search, Canvas, and cascade rollback.

The WP-Gate seeded-error run recorded before `tmp/` disposition reported
detection recall `1.0`, false-positive rate `0.0`, rollback completeness `1.0`,
residual error rate `0.0`, and ask-routed checkpoint value `1.0` for the
deterministic fixture.

Broader semantic quality, real-corpus parser quality, visual Obsidian rendering,
and attended PI checkpoint-cost calibration remain follow-up limitations. The
evidence above supports the sandbox checkpoint; it is not a non-sandbox
production claim.

## Tmp disposition

All tracked files in `docs/releasing/0.1.0-alpha.11/tmp/` were reviewed on
2026-06-29 before deletion. Durable content was routed as follows:

| Scratch evidence | Disposition |
| --- | --- |
| `0.1.0-alpha.11-design.md` | Durable decisions were folded into ADRs, system docs, the release plan, and current schema/policy tests. Remaining broad limitations are retained below. |
| `0.1.0-alpha.11-exec-plan.md` | Work-package scope and acceptance are summarized by the release plan gates, this validation log, and passing tests. |
| M0 and pre-approval reports/scripts | Historical feasibility evidence; superseded by source tests, package/runtime verification, and this validation log. |
| WP1-WP8 result files | Implementation evidence summarized here; executable coverage now lives in `tests/`, `scripts/verify`, doctors, and CI. |
| Start-blocker verifier/results | Live qmd/Zotero/PDF/Inspector/worker/source-id evidence summarized here; Zotero annotation import remains out of scope. |
| WP-Gate seeded-error results | Deterministic fixture metrics summarized here; the frozen bundle and tests remain in the source tree. |

Follow-up limitations preserved from the scratch review:

- visual Obsidian rendering by screenshot or human inspection was not proven in
  this session. No display variables (`DISPLAY`, `WAYLAND_DISPLAY`, or
  `XDG_RUNTIME_DIR`) were available even outside the sandbox, screenshot tools
  were absent, and `obsidian-cli` could not connect because Obsidian was not
  running;
- attended Co-PI/product use in `Memoria-test` remains weaker than the local
  deterministic worker-boundary cycle and REST/workspace evidence;
- broader semantic detector quality, live model-quality synthesis, larger
  real-corpus PDF parser quality, and Ask retrieval benchmarks remain future
  measurement work before any non-sandbox production claim.

## Checkpoint close-out status

GitHub queries on 2026-06-29 found no open `0.1.0-alpha.11` milestone, release,
or gate issues, and no `0.1.0-alpha.11` milestone exists. The release plan uses
`status: candidate`; this validation log preserves candidate evidence toward
close-out, not a tagged release.
