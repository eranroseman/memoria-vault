---
title: On-disk layout
parent: Reference
---

# On-disk layout

Where every file lives. The repo ships the vault under **`src/`**; the installer scaffolds the folder skeleton in your chosen runtime vault (default `~/Memoria`) and populates it from `src/` ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). Repo and deployed vault have the same internal shape; the deployed vault additionally grows the runtime-only artifacts listed at the end. The tree itself is fixed by [ADR-47](../adr/47-type-first-category-folders.md): six legal vault-root categories, with the type → folder map living in `src/.memoria/schemas/folders.yaml`. `.memoria/` is never opened by the PI; if a workflow tells the PI to open a `.memoria/...` path, that workflow is wrong.

---

## The vault tree

```text
<vault>/
├── home.md                  first-run welcome note (fresh-vault launch screen)
├── _nav.md                  the navigation rail — pinned in the left pane, owns space-switching
├── research-focus.md        program memory — the PI's standing steering
├── AGENTS.md                ground rules for any agent in the vault
├── troubleshooting.md       vault-root nav page
├── catalog/                 entity records (given relationships)
│   ├── catalog.base           the Catalog Bases view
│   ├── papers/  people/  organizations/  venues/  datasets/  repositories/
├── notes/                   the PI's knowledge (authored links:)
│   ├── fleeting/  sources/  indexes/
│   ├── claims/                review-gated
│   └── hubs/                  review-gated
├── projects/                project records, theses, drafts, code, exports
│   └── _template/             starter project scaffold copied by the Project on-ramp
├── inbox/                   the action queue — candidate/gap/flag/alert/work-prompt cards
│   └── inbox.base             the Inbox board view
├── spaces/                  space dashboards + Inbox queue + Maintenance collection
└── system/                  infrastructure plus typed system homes
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            13 support dashboards + claims/sources/fleeting/project-gate .base files
    ├── patterns/              the pattern library (+ patterns.base, _preamble.md)
    ├── scripts/               QuickAdd capture scripts (capture-from-url/-zotero)
    ├── board/                 board-export card projections
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── worklists/             Bases-backed batch screening rows (worklist-item notes)
    ├── metrics/               derived metric notes (lane-*, lint-verdict-*) + eval/runs.jsonl
    └── logs/                  audit.jsonl, capture-intake.jsonl, patterns.jsonl, sessions/
```

The six vault-root categories (`catalog`, `notes`, `projects`, `inbox`, `spaces`, `system`) are the legal top-level set — the Linter flags any stray root folder. The gated and transient prefixes those subfolders carry are declared in `folders.yaml`, not hardcoded; what they mean is in [Note types](note-types.md).

---

## `.memoria/` — the runtime tooling layer

Hidden from Obsidian; everything agents and operations need, shipped in `src/.memoria`:

```text
.memoria/
├── schemas/                 THE single schema source (ADR-49/50)
│   ├── types/<type>.yaml      26 per-type frontmatter schemas
│   ├── folders.yaml           type→folder homes, gated/transient prefixes, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution, classify, hybrid scores, cluster params)
├── operations/              the deterministic operation cores
│   ├── lib/                   schema.py (loader/validator) + inbox.py (card writer) + loudness.py (alert/block routing)
│   ├── processing/ingest/     runner.py, ingest_paper.py, resolve_merge.py, extract.py, link.py
│   ├── integrity/linter/      detectors.py, hub_handoff.py, precommit_check.py, pre-commit, golden_restore.py
│   ├── integrity/retraction/  retraction.py
│   ├── cleanup/               reconcile.py, archive_inbox.py
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
├── samples/                 optional bundled tutorial corpora, loaded by QuickAdd commands
│   └── mediterranean-diet/    hidden source for Memoria: load sample vault
├── plugins/memoria-policy-gate/   the fail-closed write-gate Hermes plugin
├── scripts/                 cron wrappers (sweeps, lint, board-export, retraction refresh)
├── tool-registry.yaml       authoritative per-profile tool allowlist
├── memoria.bib              the bibliographic backbone export
├── design-system.md · project-hints.yaml.example
```

The policy gate's stable deployed entrypoint stays in `.memoria/mcp/`, while its
behavior-preserving decision/audit/engine modules live in the installed
`memoria.runtime.policy` package.

## `.githooks/` — source hooks

Shipped in `src/.githooks`: canonical git hooks that the installer copies into the runtime vault's `.git/hooks/` after the user initializes the vault repository. `post-commit` enqueues Peer-reviewer verify cards for committed Markdown drafts under `projects/`.

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

Shipped in `src/.obsidian`: `app.json`, `appearance.json` (starter snippet toggles), `core-plugins.json`, `community-plugins.json`, `graph.json` (link color-groups), `snippets/` (`memoria-link-colors.css`, `memoria-property-badges.css`), and per-plugin config under `plugins/` (QuickAdd, Commander, Modal Forms, agent-client, Local REST API, Buttons, Dataview, Templater, Citation, Callout Manager, Obsidian Git, Portals). `src/.obsidian/workspaces.json` ships one reset layout named **Memoria** that seeds `src/home.md` on a fresh vault; space switching is handled by the `src/_nav.md` navigation rail over the space dashboards `src/spaces/library.md`, `src/spaces/knowledge.md`, and `src/spaces/project.md`, with the Inbox queue at `src/spaces/inbox.md` and Maintenance collection at `src/spaces/maintenance.md` (see [Obsidian workspaces](obsidian-workspaces.md)).

### The Bases views

The `.base` files sit alongside their data: `catalog/catalog.base`, `inbox/inbox.base`, `notes/hubs/hubs.base`, `projects/projects.base`, `system/board/board.base`, the `claims`/`sources`/`fleeting`/`project-gate` bases in `system/dashboards/`, `system/patterns/patterns.base`, and `system/worklists/worklists.base` ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). What each view shows is in [Dashboards](dashboards.md#the-bases-views).

---

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `docs_doctor.py`, test drivers — install tooling never deploys into the vault. |
| `%LOCALAPPDATA%\hermes\profiles\memoria-*` (Windows) / `~/.hermes/profiles/memoria-*` (Linux/WSL2) | The deployed profile copies (config substituted, `.env` seeded). |
| `%LOCALAPPDATA%\hermes\scripts\` (Windows) / `~/.hermes/scripts/` (Linux/WSL2) | The substituted cron wrappers (`memoria-sweeps.sh`, `memoria-lint.sh`, `memoria-board-export.sh`, …), copied and renamed from the repo's `.memoria/scripts/<job>-cron.sh`. |
| `%LOCALAPPDATA%\hermes\.env` (Windows) / `~/.hermes/.env` (Linux/WSL2) | The shared secrets file the installer propagates per profile. |

---

## Related

- How `src/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Note types](note-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)
