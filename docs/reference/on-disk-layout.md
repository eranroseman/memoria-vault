---
topic: architecture
---

# On-disk layout reference

> [!warning] Scaffold vs. Complete Install
> This layout shows the target on-disk structure. Several items marked below are not yet present in the v0.1 starter vault. Items annotated `# v0.2` or `# deferred` are planned but not yet created.

The annotated directory trees below show *where each thing lives* across the two filesystem locations: the starter vault (versioned, distributable) and the user's Hermes runtime (per-user). For *why* the layout is shaped this way — the source-vs-runtime relationship, the installer flow, and the version-control boundary — see [the on-disk-layout explanation](../explanation/architecture/on-disk-layout.md).

## Starter vault (versioned, distributable)

The **vault root folder is human-defined**: the human clones the distribution into any folder name and can move it anywhere. Only the *contents* of the root — the `00-meta/`, `.obsidian/`, `.memoria/` shape — are fixed. See [vault/README.md](../explanation/vault/README.md#folder-structure) for the full folder taxonomy and per-folder role table.

```text
<vault-root>/                           # any folder name; human picks at clone time
├── README.md                           # human-facing: clone, run install
├── install.ps1                         # Windows installer
├── install.sh                          # macOS/Linux — v0.2
│
├── 00-meta/                            # vault skeleton (human-visible in Obsidian)
│   ├── 01-dashboards/                  # 11 shipped dashboards (Daily Health as index.md, board-state, contradictions, drift-watch, audit-log, …; skill-lifecycle deferred)
│   ├── 02-logs/                        # audit.jsonl, board-state.jsonl, lint-findings.jsonl, cron-history.jsonl
│   ├── 03-templates/                   # 15 note templates (claim-note, paper-note, …)
│   ├── 04-reference/                   # human-facing reference notes (design-system, schema-reference, …)
│   ├── 05-eval/                        # vault-eval gold tasks (per-workflow gold sets) — ADR-23 (ships empty: .keep)
│   ├── 07-skills/                      # skill-governance registry — ships empty (.keep); overlay deferred
│   ├── 08-metrics/                     # fleet + eval metrics (telemetry rollups, eval/ run results) — ships empty (.keep); metrics aggregator deferred (Phase 6, not yet built)
│   ├── board/                          # markdown board export — ships empty (.keep); Phase-4 export deferred
│   ├── index.md                        # vault landing page (pinned in sidebar)
│   ├── research-directions.md          # Librarian's session-start input
│   └── system-status.md                # runtime health snapshot
├── 10-inbox/
│   ├── 01-fleeting/                    # raw captures
│   ├── 02-answers/                   # answer drafts awaiting review
│   └── 03-candidates/                  # discovery leads and screening queue
├── 20-sources/
│   ├── 01-papers/                     # one note per citable paper (specialized item)
│   ├── 02-items/                       # tools, repos, packages, products, standards, datasets, software
│   └── 03-entities/                    # 01-people / 02-organizations / 03-venues
├── 30-synthesis/
│   ├── 01-claims/                   # claim notes — human-owned
│   ├── 02-reference/                        # reference notes
│   └── 03-moc/                         # Maps of Content
├── 40-workbench/
│   └── <project>/                      # one folder per project: 01-map/ 02-framing/ 03-canvas/ 04-drafts/ 05-verification/ 06-code/
├── 50-deliverables/
│   ├── 01-manuscripts/                 # papers, articles, preprints
│   ├── 02-presentations/               # slides, talks, posters
│   ├── 03-media/                       # figures, infographics, web
│   └── 04-releases/                    # datasets, models, code, supplementary
├── 90-assets/                          # Marker extracts, figures, supplementary materials (PDFs stay in Zotero)
├── 95-archive/                         # superseded notes
│
├── .obsidian/                          # Obsidian config (auto-hidden by Obsidian)
│   ├── plugins/
│   │   ├── obsidian-linter/data.json   # post-v0.1 (reference-only per ADR-24; not installed)
│   │   ├── obsidian-citation-plugin/data.json
│   │   ├── agent-client/data.json.example
│   │   ├── obsidian-local-rest-api/data.json.example
│   │   └── callout-manager/data.json.TODO
│   └── snippets/
│       └── memoria-link-colors.css
│
└── .memoria/                           # Memoria tooling (dot-prefix: auto-hidden by Obsidian)
    ├── profiles/                       # the seven Hermes profile directories, hand-authored
    │   ├── memoria-librarian/
    │   │   ├── SOUL.md                 # the actual system prompt
    │   │   ├── config.yaml             # model, commands, tool filters
    │   │   ├── mcp.json                # MCP server connections (with {{VAULT_PATH}} placeholders)
    │   │   ├── cron/                   # scheduled tasks for this profile
    │   │   ├── skills/                 # profile-bundled skills
    │   │   ├── .env.EXAMPLE            # required env vars, commented out
    │   │   └── distribution.yaml       # name, version
    │   ├── memoria-mapper/
    │   ├── memoria-socratic/
    │   ├── memoria-writer/
    │   ├── memoria-verifier/
    │   ├── memoria-coder/
    │   └── memoria-linter/             # also holds M-detectors.md alongside SOUL.md
    ├── profile-memory/                 # learned MEMORY.md/USER.md, junctioned into ~/.hermes (opt-in multi-machine sync) — created on first multi-machine sync opt-in
    │   └── memoria-<name>/
    ├── mcp/                            # Memoria-specific MCP servers (Python)
    │   ├── policy_mcp.py               # shipped — write-gate; `--self-test` + `--decide`
    │   ├── tasks_mcp.py               # not yet authored (Phase 4 — fronts Hermes Kanban)
    │   └── requirements.txt            # shipped — mcp + PyYAML
    ├── lane-overrides/                 # 7 YAML files (one per lane); all ship — the policy MCP that reads them is v0.2
    │   ├── librarian.yaml
    │   ├── mapper.yaml
    │   ├── socratic.yaml
    │   ├── writer.yaml
    │   ├── verifier.yaml
    │   ├── coder.yaml
    │   └── linter.yaml
    ├── csl/                            # Pandoc citation style files
    ├── library.bib                     # Zotero BibTeX export
    └── tool-registry.yaml              # machine-read tool config
```

Engineering documentation (architecture, workflows, decisions (ADRs), profile design summaries, dashboards, roadmap, and topic-distributed reference material) lives in the **`docs/` folder of this repo** — a sibling of the vault, not a separate repository. It is the engineering spec; the runtime vault doesn't need it to function. Because either folder can be cloned on its own, a cross-folder reference uses a GitHub URL rather than a relative path.

## Runtime install (per-user, not in repo)

The installer copies the seven profile directories from `.memoria/profiles/` to Hermes's standard location at `~/.hermes/profiles/` (or `%USERPROFILE%\.hermes\profiles\` on Windows; both honor `HERMES_HOME` to override). Profiles are prefixed `memoria-` to keep them separable from other agents on the same machine.

```text
~/.hermes/profiles/
├── memoria-librarian/                 # copied from .memoria/profiles/memoria-librarian/
│   ├── SOUL.md                         # author-owned, overwritten on every install
│   ├── config.yaml                     # author-owned, overwritten on every install
│   ├── mcp.json                        # author-owned, {{VAULT_PATH}} substituted with real path
│   ├── cron/
│   ├── skills/
│   ├── .env.EXAMPLE                    # author-owned, overwritten on every install
│   ├── .env                            # user-owned, preserved across installs
│   └── distribution.yaml
├── memoria-mapper/
├── memoria-socratic/
├── memoria-writer/
├── memoria-verifier/
├── memoria-coder/
└── memoria-linter/
```

Per-profile structure follows the [Hermes profile-distribution shape](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions) — `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/` — so Memoria profiles are compatible with `hermes profile list` and the standard `hermes -p memoria-librarian chat` invocation surface.

## Related

- Vault folder taxonomy: [vault/README.md](../explanation/vault/README.md)
- Lane-override YAML format: [profiles/README.md lane-override files](../explanation/profiles/README.md#lane-override-files)
