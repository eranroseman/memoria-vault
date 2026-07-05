---
title: On-disk layout
parent: System and infrastructure
grand_parent: Reference
---

# On-disk layout

Where every file lives.

- The repo ships the vault source under **`vault-template/`**.
- The installer scaffolds a runtime vault, then populates it from `vault-template/`.
- Product operation manifests ship inside the installed Python package, not the runtime vault.
- The legal root categories come from [ADR-126](../adr/126-four-type-knowledge-model.md) and `vault-template/.memoria/schemas/folders.yaml`.
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
├── catalog/                 source and entity record projections
│   ├── index.md              generated catalog index
│   ├── sources/
│   └── entities/
├── knowledge/               Work, note, hub, and project Concepts
│   ├── index.md              generated knowledge index
│   ├── works/  notes/  hubs/  projects/
│   └── views/knowledge.base
├── inbox/                   transient attention projections, not Concepts
└── system/                  visible infrastructure
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            read-only system dashboards
    ├── patterns/              shared prompt preamble
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── metrics/               derived metric notes and eval/runs.jsonl
    └── logs/                  audit.jsonl, sessions/
```

The workspace bundle roots are declared in `folders.yaml`, along with the
transient `inbox/` projection root, machine staging roots under `.memoria/staging/`,
and the quarantine root `.memoria/quarantine`. The Linter flags stray root folders.
What the Concept homes mean is in [Document types](document-types.md).

---

## `.memoria/` - the runtime tooling layer

Hidden runtime infrastructure; everything agents and operations need, shipped in
`vault-template/.memoria`:

```text
.memoria/
├── schemas/                 THE single schema source (ADR-126)
│   ├── types/<type>.yaml      per-type Concept schemas
│   ├── folders.yaml           type→folder homes, staging roots, quarantine, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution, classify, hybrid scores)
├── config/                  provider and runtime policy (`providers.yaml`)
├── blobs/                   gitignored provider payloads and staged source content
├── plugins/memoria-policy-gate/   fail-closed write-gate package for optional adapters
├── scripts/                 cron-runner for operator-managed scheduled tasks
├── memoria.sqlite           SQLite working-state DB
├── state/                   runtime state owned by the CLI/engine
├── audit/                   git-trackable audit anchors
├── index/ · staging/ · quarantine/   disposable search/input mirrors and holding areas
├── design-system.md
```

Alpha.15 deliberately does **not** ship hidden operation-package homes, installed
profile packages, lane override packages, or profile tool registries. Operation
manifests live under `memoria_vault.product.capabilities.operations`; operation
code lives in the installed `memoria_vault` package.

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
| `.memoria/data/retraction_watch.csv` | retraction refresh wrapper | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python used by the Memoria CLI/runtime package. |
| `.git/hooks/pre-commit` | installer | The pre-commit hook (once the vault is a git repo). |

---

## Editor configuration

Alpha.15 ships no editor app configuration. Optional editors may keep local
state beside or inside a working copy, but that state is not part of the
standalone template, installer skeleton, request lifecycle, or source-of-truth
layout.

### The Bases view

The shipped `.base` file sits alongside the checked knowledge Concepts:
`knowledge/views/knowledge.base`. It is an optional editor view over the same
files; the CLI/read API remains authoritative. What it shows is in
[Dashboards](dashboards.md#the-bases-views).

---

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `docs_doctor.py`, test drivers — install tooling never deploys into the vault. |
| search index | Generated checked-only BM25 input tree and manifest under `.memoria/index/search/`. |
| OS diagnostic state directory | Redacted support bundles and raw diagnostic captures; see [Diagnostics](diagnostics.md). |

---

## Related

- How `vault-template/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Document types](document-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)
