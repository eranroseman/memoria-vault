---
title: On-disk layout
parent: Reference
---

# On-disk layout

Where every file lives. The repo ships the vault under **`src/`**; the installer scaffolds the folder skeleton in your chosen runtime vault (default `~/Memoria`) and populates it from `src/` ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). Repo and deployed vault have the same internal shape; the deployed vault additionally grows the runtime-only artifacts listed at the end. The tree itself is fixed by [ADR-47](../adr/47-type-first-category-folders.md): five type-first category folders, with the type → folder map living in [src/.memoria/schemas/folders.yaml](../../src/.memoria/schemas/folders.yaml).

---

## The vault tree

```text
<vault>/
├── home.md                  the homepage (absorbs the daily-health glance)
├── research-focus.md        program memory — the PI's standing steering
├── AGENTS.md                ground rules for any agent in the vault
├── troubleshooting.md       vault-root nav page
├── catalog/                 entity records (given relationships)
│   ├── catalog.base           the Catalog Bases view
│   ├── papers/  people/  organizations/  venues/  datasets/  repositories/
├── notes/                   the PI's knowledge (authored links:)
│   ├── fleeting/  source/  index/
│   ├── claims/                review-gated
│   └── hubs/                  review-gated
├── projects/                project scratch (drafts, code) — Writer/Engineer lanes
├── inbox/                   the action queue — candidate/gap/flag/alert cards
│   └── inbox.base             the Inbox board view
└── system/                  infrastructure (untyped, except patterns/)
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            12 dashboards + claims/sources/fleeting .base files
    ├── patterns/              the pattern library (+ patterns.base, _preamble.md)
    ├── scripts/               QuickAdd capture scripts (capture-from-url/-zotero)
    ├── board/                 board-export card projections
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── metrics/               derived metric notes (lane-*, lint-verdict-*) + eval/runs.jsonl
    └── logs/                  audit.jsonl, capture-intake.jsonl, patterns.jsonl, sessions/
```

The five vault-root categories (`catalog`, `notes`, `projects`, `inbox`, `system`) are the legal top-level set — the Linter flags any stray root folder. The gated and transient prefixes those subfolders carry are declared in `folders.yaml`, not hardcoded; what they mean is in [Note types](note-types.md).

---

## `.memoria/` — the runtime tooling layer

Hidden from Obsidian; everything agents and engines need, shipped in [src/.memoria/](../../src/.memoria):

```text
.memoria/
├── schemas/                 THE single schema source (ADR-49/50)
│   ├── types/<type>.yaml      18 per-type frontmatter schemas
│   ├── folders.yaml           type→folder homes, gated/transient prefixes, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution floor, cluster params)
├── engines/                 the five engines' deterministic cores
│   ├── lib/                   schema.py (loader/validator) + inbox.py (card writer)
│   ├── linter/                detectors.py, precommit_check.py, pre-commit, golden.py
│   ├── ingest/                pipeline.py, ingest_paper.py, resolve_merge.py, extract.py, link.py
│   └── sweeps/                reconcile.py, retraction.py
├── mcp/                     the MCP servers (Layer 5)
│   ├── policy_mcp.py + policy_hook.py     the write gate
│   ├── ingest_mcp.py · cluster_mcp.py · tasks_mcp.py · patterns_mcp.py
│   ├── board_export.py · metrics_aggregate.py    telemetry (cron, not MCP)
│   └── requirements.txt · requirements-cluster.txt
├── profiles/                the five Hermes profile packages
│   └── memoria-{copi,librarian,writer,peer-reviewer,engineer}/
│       ├── SOUL.md · config.yaml · distribution.yaml · skills/
├── lane-overrides/          the five lane ceilings: copi/librarian/writer/peer-reviewer/engineer.yaml
├── plugins/memoria-policy-gate/   the fail-closed write-gate Hermes plugin
├── scripts/                 cron wrappers (sweeps, lint, board-export, retraction refresh)
├── tool-registry.yaml       authoritative per-profile tool allowlist
├── memoria.bib              the bibliographic backbone export
├── design-system.md · project-hints.yaml.example
```

Runtime-only (created in the deployed vault, never shipped):

| Path | Created by | Holds |
| --- | --- | --- |
| `.memoria/golden/` | installer (`golden.py stage`) | The restorable golden copy of every system file + `manifest.json` (SHA-256). |
| `.memoria/data/extracts/` | ingest MCP | Full-text extracts per citekey — outside the Librarian's write lane. |
| `.memoria/data/retraction_watch.csv` | retraction refresh cron | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python the MCP servers run on. |
| `.git/hooks/pre-commit` | installer | The schema commit gate (once the vault is a git repo). |

---

## `.obsidian/` — app configuration

Shipped in [src/.obsidian/](../../src/.obsidian): `app.json`, `appearance.json`, `core-plugins.json`, `community-plugins.json`, `graph.json` (link color-groups), `snippets/`, and per-plugin config under `plugins/` (QuickAdd, agent-client, Local REST API). [src/.obsidian/workspaces.json](../../src/.obsidian/workspaces.json) ships the three saved layouts — **Desk**, **Library**, and **Studio** (see [Obsidian workspaces](obsidian-workspaces.md)).

### The Bases views

The `.base` files sit alongside their data: `catalog/catalog.base`, `inbox/inbox.base`, the `claims`/`sources`/`fleeting` bases in `system/dashboards/`, and `system/patterns/patterns.base` ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). What each view shows is in [Dashboards](dashboards.md#the-bases-views).

---

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `docs-doctor.py`, test drivers — install tooling never deploys into the vault. |
| `~/.hermes/profiles/memoria-*/` | The deployed profile copies (config substituted, `.env` seeded). |
| `~/.hermes/scripts/` | The substituted cron wrappers (`memoria-sweeps.sh`, `memoria-lint.sh`, `memoria-board-export.sh`, …), copied and renamed from the repo's `.memoria/scripts/<job>-cron.sh`. |
| `~/.hermes/.env` | The global secrets file the installer propagates per profile. |

---

## Related

- How `src/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Note types](note-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)
