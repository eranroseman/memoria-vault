---
title: On-disk layout
parent: System and infrastructure
grand_parent: Reference
---

# On-disk layout

Where every file lives.

- The repo ships the vault source under **`vault-template/`**.
- The installer scaffolds a runtime vault, then populates it from `vault-template/` ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)).
- Repo and runtime vault share the same internal shape; runtime-only artifacts are listed below.
- The legal root categories come from [ADR-119](../adr/119-schema-driven-document-creation.md) and `vault-template/.memoria/schemas/folders.yaml`.
- `.memoria/` is runtime infrastructure. A PI workflow should never ask the PI to open it.

---

## The vault tree

```text
<vault>/
├── index.md                 generated workspace index
├── home.md                  launch/reset welcome note
├── _nav.md                  plain Markdown navigation rail
├── steering.md              program memory; the PI's standing steering
├── AGENTS.md                ground rules for any agent in the vault
├── troubleshooting.md       vault-root nav page
├── catalog/                 source and entity Concepts
│   ├── index.md              generated catalog index
│   ├── catalog.base           Sources Bases view
│   ├── sources/
│   └── entities/
├── knowledge/               digest, note, hub, and project Concepts
│   ├── index.md              generated knowledge index
│   ├── digests/  notes/  hubs/  projects/
│   └── views/knowledge.base
├── capabilities/            operation, skill, adapter, and workflow Concepts
│   ├── index.md              generated capabilities index
│   ├── capabilities.base
│   ├── operations/  skills/  adapters/  workflows/
├── inbox/                   transient attention projections, not Concepts
└── system/                  visible infrastructure
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            read-only system dashboards
    ├── patterns/              shared prompt preamble
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── metrics/               derived metric notes and eval/runs.jsonl
    └── logs/                  audit.jsonl, capture-intake.jsonl, patterns.jsonl, sessions/
```

The three bundle roots (`catalog`, `knowledge`, `capabilities`) are declared in
`folders.yaml`, along with the transient `inbox/` projection root, machine staging
roots under `.memoria/staging/`, and the quarantine root `.memoria/quarantine`.
The Linter flags stray root folders.
What the Concept homes mean is in [Document types](document-types.md).

---

## `.memoria/` - the runtime tooling layer

Hidden runtime infrastructure; everything agents and operations need, shipped in
`vault-template/.memoria`:

```text
.memoria/
├── schemas/                 THE single schema source (ADR-119)
│   ├── types/<type>.yaml      per-type Concept schemas
│   ├── folders.yaml           type→folder homes, staging roots, quarantine, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution, classify, hybrid scores, cluster params)
├── config/                  provider and runtime policy (`providers.yaml`)
├── blobs/                   gitignored provider payloads and staged source content
├── plugins/memoria-policy-gate/   fail-closed write-gate package for optional adapters
├── scripts/                 wrappers for operator-managed scheduled tasks
├── memoria.sqlite           SQLite working-state DB
├── state/                   runtime state owned by the CLI/engine
├── audit/                   git-trackable audit anchors
├── index/ · staging/ · quarantine/   disposable search/input mirrors and holding areas
├── design-system.md · project-hints.yaml.example
```

Alpha.14 deliberately does **not** ship hidden operation-package homes, installed
profile packages, lane override packages, or profile tool registries. Operation
manifests live under `capabilities/operations/`; operation code lives in the
installed `memoria_vault` package.

The policy gate's stable implementation lives in the installed
`memoria_vault.runtime.policy` package. Optional adapters may ship their own
thin entrypoints, but the baseline workspace does not contain a hidden adapter
code home.

## `.githooks/` - source hooks

Shipped in `vault-template/.githooks`: the canonical pre-commit schema gate that
the installer copies into the runtime vault's `.git/hooks/` after the user
initializes the vault repository. File-change work is observed through
`memoria workspace scan`, not a Hermes-backed post-commit queue.

Runtime-only (created in the deployed vault, never shipped):

| Path | Created by | Holds |
| --- | --- | --- |
| `.memoria/golden/` | installer (`golden_restore.py stage`) | The restorable golden copy of every system file + `manifest.json` (SHA-256). |
| `.memoria/data/extracts/` | runtime ingest helpers | Full-text extracts per citekey, when a workflow needs an intermediate extract store. |
| `.memoria/data/retraction_watch.csv` | retraction refresh cron | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python used by the Memoria CLI/runtime package. |
| `.git/hooks/pre-commit` | installer | The pre-commit hook (once the vault is a git repo). |

---

## Editor configuration

Alpha.14 ships no editor app configuration. Optional editors may keep local
state beside or inside a working copy, but that state is not part of the
standalone template, installer skeleton, golden copy, request lifecycle, or
source-of-truth layout.

### The Bases views

The `.base` files sit alongside their data: `catalog/catalog.base`,
`knowledge/views/knowledge.base`, and `capabilities/capabilities.base`
([ADR-116](../adr/116-obsidian-surface-architecture.md)). What each view shows is in
[Dashboards](dashboards.md#the-bases-views).

---

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `docs_doctor.py`, test drivers — install tooling never deploys into the vault. |
| qmd user cache | Model files and global qmd cache managed by qmd; Memoria keeps workspace config/index state inside `.memoria/index/qmd/`. |
| OS diagnostic state directory | Redacted support bundles and raw diagnostic captures; see [Diagnostics](diagnostics.md). |

---

## Related

- How `vault-template/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Document types](document-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)
