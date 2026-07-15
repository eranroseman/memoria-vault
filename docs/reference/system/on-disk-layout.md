---
title: On-disk layout
parent: System and infrastructure
nav_order: 2
grand_parent: Reference
---

# On-disk layout

Where every file lives.

- The installed Python package ships the minimal workspace seed under
  `memoria_vault.product.workspace_seed`.
- `memoria init` copies only runtime-required seed files, then creates writable
  runtime and content directories from `.memoria/schemas/folders.yaml`. It also
  initializes generated control/projection files such as `index.md`,
  `bibliography.bib`, `.memoria/overrides.jsonl`, `.memoria/journal-head`, and
  `system/manifest.jsonl`.
- Product operation manifests ship inside the installed Python package, not the
  runtime vault.
- The legal root categories come from `.memoria/schemas/folders.yaml`.
- `.memoria/` is runtime infrastructure. A PI workflow should never ask the PI to open it.

---

## The vault tree

```text
<vault>/
├── index.md                 generated workspace index
├── steering.md              program memory; the PI's standing steering
├── bibliography.bib         generated portable bibliography
├── notes/                   claim and question notes
├── hubs/                    topic hubs with human salience
├── projects/<slug>/         project.md, outline.md, draft.md, code/<artifact-id>.md, evidence/gap/export artifacts
├── digests/<work_id>.md     checked source digests
├── fulltexts/<work_id>.md    generated full-text reproductions
├── inbox/                   transient attention projections, not Concepts
└── system/                  visible infrastructure
    ├── vocabulary.md          controlled vocabularies
    ├── manifest.jsonl         generated visible audit manifest
    ├── logs/                  audit.jsonl, lint-findings.jsonl, sessions/*.jsonl
    ├── worklists/<slug>/      batch worklist-item projections (see glossary: Worklist)
    └── metrics/               exported metrics
```

The workspace bundle roots are declared in `folders.yaml`, along with the
transient `inbox/` projection root, machine staging roots under `.memoria/staging/`,
and the quarantine root `.memoria/quarantine`. The Linter flags stray root folders.
What the Concept homes mean is in [Document types](../data-model/document-types.md).

---

## `.memoria/` - the runtime tooling layer

Hidden runtime infrastructure. Seed files are copied from the installed package;
writable runtime directories are created from `folders.yaml`:

```text
.memoria/
├── schemas/                 single source for schema contracts
│   ├── types/<type>.yaml      per-type Concept schemas
│   └── folders.yaml           type→folder homes, staging roots, quarantine, skeleton
├── config/                  provider config (`providers.yaml`) and the shadow-first feedback flag (`feedback.yaml`)
│   └── last-backup           gitignored local backup stamp bound to the current blob inventory
├── eval/                    seeded-error verdict bundle and last-run.md
├── patterns/_preamble.md    shared operation prompt preamble
├── overrides.jsonl          Git-tracked log of PI overrides recorded at init and beyond
├── blobs/                   gitignored provider payloads and staged source content
├── code-runs/<run-id>/      gitignored recorded code-execution run artifacts
├── journal/                 derived per-machine JSONL synchronization exports
├── journal-head             Git-tracked live hash-chain tip for the event log
├── backup-transaction.json  Git-ignored identity-bound backup recovery marker
├── restore-transaction.json Git-ignored interrupted-restore recovery marker
├── memoria.sqlite           authoritative state, including the event log
├── memoria.sqlite-{wal,shm,journal}   transient SQLite sidecars
├── locks/worker.lock         fail-closed no-follow workspace writer lock
├── index/ · staging/ · quarantine/   disposable search/input mirrors and holding areas
```

The append-only, hash-chained `event_log` in `memoria.sqlite` is the journal of
record. Trust-sensitive readers query it in event order. A journal append
commits there first and advances the working-tree `journal-head`; its committed
Git value must remain a prefix of the live chain. The per-machine JSONL files
are derived exports for synchronization. `memoria workspace scan` holds the
workspace writer lock while it verifies the chain and export subset, removes an
incomplete final JSONL fragment, and re-emits any missing export rows.

Backups live outside this tree. `memoria workspace backup <target>` publishes a
manifest-bound SQLite/blob/head snapshot; `last-backup` records the target and
blob inventory used by the failing doctor health check. See
[Backup and recovery](backup-and-recovery.md).

> **Unshipped:** dashboards, note templates, hidden operation-package homes,
> installed profile packages, lane override packages, cron wrappers, and
> profile tool registries are not part of the current package.

The Memoria Obsidian adapter is the default editor plugin. Operation manifests live under
`memoria_vault.product.capabilities.operations`; operation code lives in the
installed `memoria_vault` package.

## Packaged Seed Inventory

The package seed contains only files with direct runtime readers:

| Seed path | Runtime reader |
| --- | --- |
| `.githooks/pre-commit` | Installer copies it to `.git/hooks/pre-commit`; the hook runs schema/frontmatter checks before commit. |
| `.gitignore` | `memoria init` installs it so generated DBs, journals, indexes, blobs, and local caches stay out of git. |
| `.memoria/config/providers.yaml` | Provider config for enrichment and operation runners. |
| `.memoria/config/feedback.yaml` | Shadow-first I1 feedback flag (`production_enabled`, default false), read by `feedback_production_enabled` and surfaced read-only in `memoria doctor bundle`. |
| `.memoria/eval/alpha15-seeded-errors.json` | Seeded-error verdict bundle read by CLI, worker, and seeded-error runtime tests. |
| `.memoria/patterns/_preamble.md` | Shared operation prompt preamble read by operation prompt assembly. |
| `.memoria/schemas/folders.yaml` | Type homes, staging roots, quarantine root, and `memoria init` skeleton. |
| `.memoria/schemas/types/*.yaml` | Per-type frontmatter contracts used by schema validation, linter, and pre-commit. |
| `.obsidian/app.json` | Obsidian file/link defaults chosen to avoid root clutter and frontmatter UI rewriting. |
| `.obsidian/core-plugins.json` | Core plugin settings for Memoria: navigation/read plugins on, workflow-mutating plugins off. |
| `.obsidian/community-plugins.json` | Enables the bundled `memoria-obsidian` plugin. |
| `.obsidian/plugins/memoria-obsidian/` | Built proof adapter files; calls local HTTP and records empirical events through `/operation/run`. |
| `steering.md` | Standing program memory read and edited through the CLI and knowledge runtime. |
| `system/vocabulary.md` | Controlled vocabulary read by schema/linter and knowledge runtime. |

The policy gate's stable implementation lives in the installed
`memoria_vault.runtime.policy` package. The seeded Obsidian plugin is an editor
entrypoint only; the baseline workspace still has no hidden adapter code home.

## `.githooks/` - source hooks

Seeded from the installed package: the canonical pre-commit schema gate that the
installer copies into the runtime vault's `.git/hooks/`. File-change work is
observed through `memoria workspace scan`, not a post-commit queue.

Runtime-only (created in the deployed vault, never shipped):

| Path | Created by | Holds |
| --- | --- | --- |
| `.memoria/data/retraction_watch.csv` | retraction refresh command | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python used by the Memoria CLI/runtime package. |
| `.git/hooks/pre-commit` | installer | The pre-commit hook (once the vault is a git repo). |

---

## Editor configuration

`memoria init` seeds a small `.obsidian/` settings bundle for users who open the
workspace in Obsidian. That bundle installs only the Memoria plugin and core
Obsidian settings. Per-machine Obsidian state, tokens, saved workspaces, and
non-Memoria plugins remain local user configuration and are not source of truth.

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `verify`, test drivers — install tooling never deploys into the vault. |
| search index | Generated checked-only BM25 input tree and manifest under `.memoria/index/search/`. |
| OS diagnostic state directory | Redacted support bundles and raw diagnostic captures; see [Diagnostics](../pipelines-and-io/diagnostics.md). |

---

## Related

- How the package seed becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Document types](../data-model/document-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md)
