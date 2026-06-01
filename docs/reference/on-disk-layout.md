# On-disk layout

Where every file lives across the two filesystem roots: the starter vault (versioned, distributable) and `.memoria/` (tooling layer). For the design rationale see [explanation/architecture/](../explanation/architecture/).

**Implementation note.** Items marked `# pending` are designed but not yet present in the v0.1 starter vault. Items marked `# deferred` are planned for a future version. See [implementation-status.md](../../project-files/operations/implementation-status.md) for build state.

---

## Repo root and vault root

There are two roots. The **repo** is the install unit — cloned anywhere; the bootstrap
copies `vault/` to your chosen **runtime vault** folder (default `~/Memoria`, deliberately
off OneDrive). Both folder names are free; the internal shapes are fixed. The install
scripts live at the **repo root**, not inside the vault.

```text
memoria-vault/                       # repo root — the install unit (clone anywhere)
├── README.md                       # clone and install instructions
├── install.sh                      # bootstrap installer (Ubuntu/Debian + WSL2)
├── install.ps1                     # thin Windows launcher (gates WSL2, runs install.sh)
├── docs/                           # engineering spec (NOT copied to the runtime vault)
├── project-files/                  # decisions, proposals, operations
│
└── vault/                          # the Obsidian vault — the runtime artifact
    ├── 00-meta/                    # vault skeleton — human-visible in Obsidian
    ├── 10-inbox/                   # capture zone
    ├── 20-sources/                 # ingested sources
    ├── 30-synthesis/               # human-owned canonical knowledge
    ├── 40-workbench/               # project scratch
    ├── 50-deliverables/            # terminal outputs
    ├── 90-assets/                  # extracted figures, supplementary
    ├── 95-archive/                 # superseded notes
    │
    ├── .obsidian/                  # Obsidian config (hidden by Obsidian)
    └── .memoria/                   # Memoria tooling (hidden by Obsidian)
```

---

## Vault folders

| Folder | Purpose | Primary writer |
| --- | --- | --- |
| `00-meta/` | Vault governance: dashboards, logs, templates, reference notes, eval, metrics | Human / Linter (logs only) |
| `10-inbox/` | Capture zone: fleeting notes, answer drafts, discovery candidates | Human / Librarian / Writer |
| `20-sources/` | Ingested sources: papers, items, entities | Librarian |
| `30-synthesis/` | Canonical knowledge: claims, reference notes, MOCs | Human |
| `40-workbench/` | Project scratch: maps, framing, canvas, drafts, verification, code | Multiple profiles (own subfolders) |
| `50-deliverables/` | Terminal outputs: manuscripts, presentations, media, releases | Human / Coder (export task) |
| `90-assets/` | Extracted figures, PDFs stay in Zotero | Librarian (Marker extracts) |
| `95-archive/` | Superseded notes; never deleted | Human |

### `00-meta/` subtree

```text
00-meta/
├── 01-dashboards/
│   ├── index.md                    # dashboard entry point (opens Daily Health)
│   ├── audit-log.md
│   ├── board-state.md
│   ├── contradictions.md
│   ├── discuss-queue.md
│   ├── drift-watch.md
│   ├── fleet-health.md
│   ├── loose-ends.md
│   ├── open-questions.md
│   ├── reading-pipeline.md
│   └── weekly-review.md
├── 02-logs/
│   ├── audit.jsonl                 # pending (created by policy MCP at first run)
│   ├── sessions/                   # per-session logs from Linter
│   ├── board-state.jsonl           # pending
│   ├── lint-findings.jsonl         # pending
│   └── cron-history.jsonl          # pending
├── 03-templates/                   # 15 note templates (see note-types.md)
├── 04-reference/                   # 10 human-facing reference notes (shipped)
├── 05-eval/                        # vault eval gold tasks — ships empty (.keep)
├── 07-skills/                      # skill-governance registry — ships empty (.keep); deferred
├── 08-metrics/                     # fleet + eval metrics — ships empty (.keep); deferred
├── board/                          # markdown board export — ships empty (.keep); pending
├── index.md                        # vault landing page (pinned in sidebar)
├── research-directions.md          # Librarian session-start input
└── system-status.md                # runtime health snapshot
```

### `10-inbox/` subtree

```text
10-inbox/
├── 01-fleeting/                    # raw captures (human)
├── 02-answers/                     # answer drafts awaiting review (Writer)
└── 03-candidates/                  # discovery leads + gap candidates (Librarian, Verifier)
```

### `20-sources/` subtree

```text
20-sources/
├── 01-papers/                      # one note per citable paper
└── 02-items/                       # tools, repos, packages, datasets, standards, software
└── 03-entities/
    ├── 01-people/
    ├── 02-organizations/
    └── 03-venues/
```

### `30-synthesis/` subtree

```text
30-synthesis/
├── 01-claims/                      # claim notes (human-owned, review-gated)
├── 02-reference/                   # reference notes (review-gated)
└── 03-moc/                         # Maps of Content (review-gated)
```

### `40-workbench/<project>/` subtree

One folder per project. All subfolders ship as `.keep` placeholders.

```text
40-workbench/<project>/
├── 01-map/
│   ├── corpus-map.md               # Mapper writes
│   ├── gap-report.md               # Mapper writes
│   ├── comparative-briefs/         # Mapper writes
│   └── cluster-maps/               # Mapper writes
├── 02-framing/                     # Writer (counter-outline)
├── 03-canvas/                      # Human (canvas notes)
├── 04-drafts/                      # Human / Writer (draft notes)
├── 05-verification/                # Verifier writes
└── 06-code/                        # Coder writes
```

### `50-deliverables/` subtree

```text
50-deliverables/
├── 01-manuscripts/
├── 02-presentations/
├── 03-media/
└── 04-releases/
```

---

## `.obsidian/` layout

```text
.obsidian/
├── plugins/
│   ├── agent-client/
│   │   └── data.json.example       # per-human setup required
│   ├── callout-manager/
│   │   └── data.json.TODO          # callout styling not yet configured
│   ├── dataview/
│   ├── obsidian-citation-plugin/
│   │   └── data.json               # points at .memoria/library.bib
│   ├── obsidian-git/
│   ├── obsidian-homepage/
│   ├── obsidian-local-rest-api/
│   │   └── data.json.example       # contains secrets — gitignored
│   ├── quickadd/
│   └── templater-obsidian/
└── snippets/
    └── memoria-link-colors.css     # supercharged-links color rules
```

**`.gitignore` rule for secrets:**

```text
vault/.obsidian/plugins/obsidian-local-rest-api/data.json
```

---

## `.memoria/` layout

```text
.memoria/
├── profiles/
│   ├── memoria-librarian/
│   │   ├── SOUL.md                 # shipped
│   │   ├── config.yaml             # shipped (model routing + policy-gate hooks)
│   │   ├── mcp.json                # shipped (policy + obsidian servers)
│   │   ├── distribution.yaml       # shipped (manifest + env_requires)
│   │   ├── .env.EXAMPLE            # generated by `hermes profile install` from env_requires
│   │   ├── cron/
│   │   │   └── .keep               # empty placeholder
│   │   └── skills/
│   │       └── .keep               # empty placeholder; K-Dense installed here
│   ├── memoria-mapper/
│   │   ├── SOUL.md
│   │   ├── cron/
│   │   │   └── scheduled.yaml      # shipped (actual task definitions)
│   │   └── skills/ (.keep)
│   ├── memoria-socratic/   (SOUL.md + cron/.keep + skills/.keep)
│   ├── memoria-writer/     (SOUL.md + cron/.keep + skills/.keep)
│   ├── memoria-verifier/   (SOUL.md + cron/.keep + skills/.keep)
│   ├── memoria-coder/      (SOUL.md + cron/.keep + skills/.keep)
│   └── memoria-linter/
│       ├── SOUL.md
│       ├── detectors.py            # shipped (8 structural detectors)
│       ├── M-detectors.md          # shipped
│       ├── cron/
│       │   └── scheduled.yaml      # shipped (actual task definitions)
│       └── skills/ (.keep)
├── lane-overrides/
│   ├── librarian.yaml              # shipped
│   ├── mapper.yaml                 # shipped
│   ├── socratic.yaml               # shipped
│   ├── writer.yaml                 # shipped
│   ├── verifier.yaml               # shipped
│   ├── coder.yaml                  # shipped
│   └── linter.yaml                 # shipped
├── mcp/
│   ├── policy_mcp.py               # shipped (policy write-gate MCP server)
│   ├── policy_hook.py              # shipped (pre/post_tool_call gate; routes obsidian writes through policy)
│   ├── board_export.py             # shipped (board → 00-meta/board/ + board-state.jsonl)
│   ├── metrics_aggregate.py        # shipped (board+audit → 08-metrics/ trust-score notes)
│   └── requirements.txt            # shipped (mcp, PyYAML)
│       # tasks_mcp.py — deferred, not needed (native Hermes kanban tools cover it)
├── csl/
│   └── .keep                       # shipped: placeholder for CSL citation style files
├── library.bib                     # pending: user-generated by Better BibTeX auto-export
├── project-hints.yaml.example      # shipped
└── tool-registry.yaml              # shipped (per-profile tool allowlist)
```

---

## Vault skeleton: human-facing notes

Notes in `00-meta/` that ship with the starter vault for human reference.

| Note | Purpose | Maintained by |
| --- | --- | --- |
| `00-meta/index.md` | Vault landing page. Pinned in sidebar. Links to system status, dashboards, lane views, key files. | Human (rarely changes) |
| `00-meta/research-directions.md` | Current research priorities, open questions, synthesis gaps, papers to prioritize. Librarian reads this at session start. | Human (refresh weekly) |
| `00-meta/system-status.md` | Runtime health snapshot: Hermes API running, MCPs up, plugin enabled, profiles available. Distinct from `board-state` (which tracks work in flight). | Human (occasional refresh) |
| `00-meta/04-reference/getting-started.md` | First-time setup checklist — 5 steps from clone to first ingest. | Human (rarely changes) |
| `00-meta/04-reference/system-map.md` | High-level architecture summary in plain language. Vault-resident companion to `docs/explanation/architecture/`. | Human (sync with design changes) |
| `00-meta/04-reference/agent-roles.md` | Plain-language one-paragraph summary of each Hermes profile. Mirrors each `SOUL.md`. | Human (sync with profile changes) |
| `00-meta/04-reference/profile-policies.md` | Plain-language who-can-write-where summary. Tracks the lane-override YAML files. | Human (sync with lane-override changes) |
| `00-meta/04-reference/schema-reference.md` | Canonical list of every frontmatter field, type, and allowed values. Source of truth for templates and the Linter. | Human + Linter (flags drift) |
| `00-meta/04-reference/dataview-cheatsheet.md` | Reference patterns for dashboard queries — TABLE / LIST / TASK / FROM / WHERE / SORT / FLATTEN / LIMIT examples. | Human (rarely changes) |
| `00-meta/04-reference/performance-checklist.md` | Dashboard performance discipline for Dataview query authors. | Human (rarely changes) |
| `00-meta/04-reference/safe-mode.md` | The three core workflows (ingest, review, export) with minimal commands and fallbacks for when Hermes or ACP is down. | Human (rarely changes) |
| `00-meta/04-reference/obsidian-config.md` | Plugin inventory and load-bearing settings the human should not change. Mirrors `docs/reference/obsidian-plugins.md`. | Human (sync with plugin changes) |
| `00-meta/04-reference/design-system.md` | Canonical visual-style source: palette, typography, spacing, layout, motion, voice. Drives CSS snippet generators and Pandoc export configs. | Human (edits define the brand) |

The Linter's `skeleton-drift` detector flags notes whose `updated` timestamp lags the corresponding design file.

---

## File naming conventions

| Artifact | Convention | Example |
| --- | --- | --- |
| Note files | `kebab-case.md` | `receptivity-detection-timing.md` |
| Paper notes | Citekey as filename | `mamykina2010sense.md` |
| Template files | `<type>.md` | `claim.md`, `paper.md` |
| Dashboard files | `kebab-case.md` | `weekly-review.md` |
| Lane-override files | `<short-name>.yaml` | `librarian.yaml` |
| Profile dirs | `memoria-<name>/` | `memoria-librarian/` |
| Log files | `kebab-case.jsonl` | `audit.jsonl` |

**Constraint:** No spaces in vault file names. Hermes path handling and shell scripts do not support them.
