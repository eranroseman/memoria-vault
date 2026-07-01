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
├── _nav.md                  the navigation rail — pinned in the left pane, owns space-switching
├── steering.md        program memory — the PI's standing steering
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
├── capabilities/            operation, skill, MCP, and workflow Concepts
│   ├── index.md              generated capabilities index
│   ├── capabilities.base
│   ├── operations/  skills/  mcp/  workflows/
├── inbox/                   transient attention projections, not Concepts
└── system/                  visible infrastructure
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            read-only system dashboards
    ├── patterns/              shared prompt preamble
    ├── scripts/               QuickAdd capture scripts (capture-from-url/-zotero)
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── metrics/               derived metric notes (lane-*, lint-verdict-*) + eval/runs.jsonl
    └── logs/                  audit.jsonl, capture-intake.jsonl, patterns.jsonl, sessions/
```

The three bundle roots (`catalog`, `knowledge`, `capabilities`) are declared in
`folders.yaml`, along with the transient `inbox/` projection root, machine staging
roots under `.memoria/staging/`, and the quarantine root `.memoria/quarantine`.
The Linter flags stray root folders.
What the Concept homes mean is in [Document types](document-types.md).

---

## `.memoria/` — the runtime tooling layer

Hidden from Obsidian; everything agents and operations need, shipped in `vault-template/.memoria`:

```text
.memoria/
├── schemas/                 THE single schema source (ADR-119)
│   ├── types/<type>.yaml      per-type Concept schemas
│   ├── folders.yaml           type→folder homes, staging roots, quarantine, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution, classify, hybrid scores, cluster params)
├── operations/              the deterministic operation cores
│   ├── lib/                   schema.py (loader/validator) + inbox.py (card writer) + loudness.py (alert/block routing)
│   ├── processing/ingest/     runner.py, ingest_paper.py, resolve_merge.py, extract.py, link.py
│   ├── integrity/linter/      detectors.py, hub_handoff.py, precommit_check.py, pre-commit, golden_restore.py
│   ├── integrity/retraction/  retraction.py
│   ├── cleanup/               reconcile.py
│   └── telemetry/eval/        eval_dispatch.py, eval_score.py
├── mcp/                     the MCP servers (Layer 5)
│   ├── policy_mcp.py + policy_server.py + policy_hook.py     the write gate
│   ├── ingest_mcp.py · cluster_mcp.py · tasks_mcp.py · patterns_mcp.py
│   ├── board_export.py · metrics_aggregate.py    telemetry (cron, not MCP)
│   └── requirements.txt · requirements-cluster.txt
├── profiles/                the five Hermes profile packages
│   └── memoria-{copi,librarian,writer,peer-reviewer,engineer}/
│       ├── SOUL.md · config.yaml · distribution.yaml · skills/
├── lane-overrides/          the five lane ceilings: copi/librarian/writer/peer-reviewer/engineer.yaml
├── enrichment/             provider policy for catalog enrichment (`providers.yaml`)
├── blobs/                  gitignored provider payloads and staged source content
├── plugins/memoria-policy-gate/   the fail-closed write-gate Hermes plugin
├── scripts/                 cron wrappers (worker, sweeps, lint, board-export, retraction refresh)
├── tool-registry.yaml       authoritative per-profile tool allowlist
├── state/                   SQLite working-state DB (`memoria.sqlite`)
├── audit/                   git-trackable audit anchors
├── index/ · staging/ · quarantine/   disposable search/input mirrors and holding areas
├── design-system.md · project-hints.yaml.example
```

The policy gate's stable deployed entrypoint stays in `.memoria/mcp/`, while its
behavior-preserving decision/audit/engine modules live in the installed
`memoria_vault.runtime.policy` package.

## `.githooks/` — source hooks

Shipped in `vault-template/.githooks`: canonical git hooks that the installer copies into the runtime vault's `.git/hooks/` after the user initializes the vault repository. `post-commit` enqueues Peer-reviewer verify cards for committed Markdown drafts under `knowledge/projects/`.

Runtime-only (created in the deployed vault, never shipped):

| Path | Created by | Holds |
| --- | --- | --- |
| `.memoria/golden/` | installer (`golden_restore.py stage`) | The restorable golden copy of every system file + `manifest.json` (SHA-256). |
| `.memoria/data/extracts/` | ingest MCP | Full-text extracts per citekey — outside the Librarian's write lane. |
| `.memoria/data/retraction_watch.csv` | retraction refresh cron | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python the MCP servers run on. |
| `.git/hooks/pre-commit` | installer | The pre-commit hook (once the vault is a git repo). |
| `.git/hooks/post-commit` | installer | The verify-on-commit trigger copied from `.githooks/post-commit`. |

---

## `.obsidian/` — app configuration

| Config area | Files | Purpose |
| --- | --- | --- |
| App/core settings | `app.json`, `appearance.json`, `core-plugins.json`, `community-plugins.json`, `graph.json` | Starter appearance, enabled plugins, and graph color groups. |
| CSS snippets | `snippets/memoria-link-colors.css`, `snippets/memoria-property-badges.css` | Vault-local visual conventions. |
| Plugin config | `plugins/` | QuickAdd, Commander, Modal Forms, agent-client, Local REST API, Buttons, Dataview, Citation, Callout Manager, Obsidian Git, Memoria Inspector, and Portals. |
| Reset workspace | `workspaces.json` | The **Memoria** layout: `home.md` in the main pane and pinned `_nav.md` rail on the left. |
| Space switching | `_nav.md` plus `spaces/*.md` | Rail links to Library, Knowledge, Project, Inbox, and Maintenance; see [Obsidian workspaces](obsidian-workspaces.md). |

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
| `%LOCALAPPDATA%\hermes\profiles\memoria-*` (Windows) / `~/.hermes/profiles/memoria-*` (Linux/WSL2) | The deployed profile copies (config substituted, `.env` seeded). |
| `%LOCALAPPDATA%\hermes\scripts\` (Windows) / `~/.hermes/scripts/` (Linux/WSL2) | The substituted cron wrappers (`memoria-worker.sh`, `memoria-sweeps.sh`, `memoria-lint.sh`, `memoria-board-export.sh`, …), copied and renamed from the repo's `.memoria/scripts/<job>-cron.sh`. |
| `%LOCALAPPDATA%\hermes\.env` (Windows) / `~/.hermes/.env` (Linux/WSL2) | The shared secrets file the installer propagates per profile. |

---

## Related

- How `vault-template/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Document types](document-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)
