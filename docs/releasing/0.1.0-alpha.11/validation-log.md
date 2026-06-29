---
title: 0.1.0-alpha.11 validation log
parent: 0.1.0-alpha.11
grand_parent: Releasing
nav_order: 3
---

# 0.1.0-alpha.11 validation log

Date: 2026-06-29

Runtime candidate commit: `39d22f6e` (`agent/alpha11-next` from then-current
`main`), clean worktree at verification time. Later docs/test closeout commits
preserve this runtime evidence without changing alpha.11 runtime code.
Post-candidate evidence on current `main` adds tests/docs only; the latest
headless Inspector render coverage is recorded below.

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

Post-candidate CI evidence:

- PR [#1013](https://github.com/eranroseman/memoria-vault/pull/1013), merged as
  `7d31bfd5`, passed all required checks.
- `tests/test_memoria_inspector.py` now includes a headless Obsidian-view render
  fixture that feeds the Memoria Inspector queue, lint, integrity flag, graph,
  board, audit, and fleet inputs and asserts the populated panels render the
  expected product signals.
- A follow-up live Obsidian launch attempt on 2026-06-29 found `obsidian` and
  `obsidian-cli` installed, with `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, and
  `XDG_RUNTIME_DIR=/run/user/1000/`. `obsidian --no-sandbox --disable-gpu
  "obsidian://open?path=/home/eranr/Memoria-test"` processed the URI and
  `~/.config/obsidian/obsidian.log` recorded that the main app package loaded,
  but no Obsidian process stayed running and `obsidian-cli --help` still returned
  `The CLI is unable to find Obsidian. Please make sure Obsidian is running and
  try again.` This did not produce live GUI evidence.
- Final live GUI evidence on 2026-06-29 succeeded after running `obsidian-cli`
  with `XDG_RUNTIME_DIR=/run/user/1000`. Evidence: `obsidian-cli vault
  info=name` returned `Memoria-test`, `vault info=path` returned
  `/home/eranr/Memoria-test`, `plugin id=memoria-inspector` returned enabled
  version `0.1.0-alpha.11`, `command
  id=memoria-inspector:open-memoria-inspector` executed, `dev:dom
  selector='.memoria-inspector' text` showed the Inspector control buttons,
  worker queue, lint, integrity, knowledge graph, board, audit, and fleet
  panels, `dev:screenshot path=/tmp/memoria-alpha11-inspector.png` wrote a
  1625x1392 PNG (`sha256:
  d2e3f52e00ed2163da936e9359f79025c7fbf680e6c37d2660b5194f6b8c466d`), and
  `dev:errors` returned `No errors captured.`
- Additional live GUI surface checks on 2026-06-29: `plugins:enabled` included
  `agent-client`, `dataview`, `memoria-inspector`, `obsidian-citation-plugin`,
  and `obsidian-local-rest-api`; `dev:dom` found the Agent Client pane; the five
  shipped spaces and five shipped dashboards opened with `No errors captured`;
  and representative views from all seven shipped `.base` files returned through
  `base:query` without YAML or missing-view errors.

## Test-vault runtime

The now-retired start-blocker verifier passed from the `Memoria-test` runtime
venv before `tmp/` disposition.

Covered evidence:

- disposable qmd bundle index/search;
- Zotero Local API item shape. Zotero is in scope only for item/source import;
  no Zotero annotation import or annotation handling is assumed;
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

`tests/test_memoria_inspector.py` covers the Inspector control-panel boundary in
two directions: UI controls enqueue worker-owned operation jobs instead of
writing canonical files directly, and a populated operational fixture renders
the main product panels from the same queue, metrics, graph, journal, board, and
audit files the runtime vault exposes.

The WP-Gate seeded-error run recorded before `tmp/` disposition reported
detection recall `1.0`, false-positive rate `0.0`, rollback completeness `1.0`,
residual error rate `0.0`, and ask-routed checkpoint value `1.0` for the
deterministic fixture.

Broader semantic quality, real-corpus parser quality, and attended PI
checkpoint-cost calibration remain follow-up limitations. The evidence above
supports the sandbox checkpoint; it is not a non-sandbox production claim.

## Tmp disposition

All tracked files in `docs/releasing/0.1.0-alpha.11/tmp/` were reviewed on
2026-06-29 before deletion. Durable content was routed as follows:

| Scratch evidence | Disposition |
| --- | --- |
| `0.1.0-alpha.11-design.md` | Durable decisions were folded into ADRs, system docs, the release plan, and current schema/policy tests. Remaining broad limitations are retained below. |
| `0.1.0-alpha.11-exec-plan.md` | Work-package scope and acceptance are summarized by the release plan gates, this validation log, and passing tests. |
| M0 and pre-approval reports/scripts | Historical feasibility evidence; superseded by source tests, package/runtime verification, and this validation log. |
| WP1-WP8 result files | Implementation evidence summarized here; executable coverage now lives in `tests/`, `scripts/verify`, doctors, and CI. |
| Start-blocker verifier/results | Live qmd/Zotero/PDF/Inspector/worker/source-id evidence summarized here; Zotero is import-only, with no annotation handling assumed. |
| WP-Gate seeded-error results | Deterministic fixture metrics summarized here; the frozen bundle and tests remain in the source tree. |

Follow-up limitations preserved from the scratch review:

- live Obsidian rendering is now proven for the alpha.11 Inspector and main
  shipped GUI surfaces in `Memoria-test`, but this remains a sandbox checkpoint,
  not a full non-sandbox production walkthrough;
- attended Co-PI/product use in `Memoria-test` remains weaker than the local
  deterministic worker-boundary cycle and REST/workspace evidence;
- broader semantic detector quality, live model-quality synthesis, larger
  real-corpus PDF parser quality, and Ask retrieval benchmarks remain future
  measurement work before any non-sandbox production claim.

## Checkpoint close-out status

GitHub queries on 2026-06-29 found no open `0.1.0-alpha.11` milestone, release,
or gate issues, and no `0.1.0-alpha.11` milestone exists. The release plan uses
`status: complete`, `released: false`; this validation log preserves close-out
evidence for the internal checkpoint, not a tagged release.
