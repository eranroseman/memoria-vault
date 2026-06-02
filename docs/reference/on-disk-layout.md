---
title: On-disk layout
parent: Reference
---

# On-disk layout

Where every file lives across the two filesystem roots: the starter vault (versioned, distributable) and `.memoria/` (tooling layer). For the design rationale see [explanation/architecture/](../explanation/architecture/).

**Implementation note.** Items marked `# pending` are designed but not yet present in the v0.1 starter vault. Items marked `# deferred` are planned for a future version. See [Implementation status](../../project-files/plans/implementation-status.md) for build state.

---

## Repo root and vault root

There are two roots. The **repo** is the install unit — cloned anywhere; the bootstrap
copies `vault/` to your chosen **runtime vault** folder (default `~/Memoria`, deliberately
off OneDrive). Both folder names are free; the internal shapes are fixed. The install
scripts live in **`scripts/`**, not inside the vault.

```text
memoria-vault/                       # repo root — the install unit (clone anywhere)
├── README.md                       # clone and install instructions
├── scripts/                        # installer and maintenance scripts
│   ├── install.sh                  # bootstrap installer (Ubuntu/Debian + WSL2)
│   ├── install.ps1                 # thin Windows launcher (gates WSL2, runs install.sh)
│   └── PSScriptAnalyzerSettings.psd1  # PSScriptAnalyzer lint config
├── docs/                           # engineering spec (NOT copied to the runtime vault)
├── project-files/                  # decisions, proposals, operations
│
└── vault/                          # the Obsidian vault — the runtime artifact
    ├── home.md                     # vault front door (obsidian-homepage opens it on launch)
    ├── research-directions.md      # Librarian session-start input (human-edited)
    ├── troubleshooting.md          # offline-fallback help (kept in-vault by design)
    ├── 00-meta/                    # the human's read surface: dashboards
    ├── 10-inbox/                   # capture zone
    ├── 20-sources/                 # ingested sources
    ├── 30-synthesis/               # human-owned canonical knowledge
    ├── 40-workbench/               # project scratch
    ├── 50-deliverables/            # terminal outputs
    ├── 90-assets/                  # extracted figures, supplementary
    ├── 95-archive/                 # superseded notes
    ├── 99-system/                  # machine-consumed/generated (Obsidian-visible): logs, board, metrics, eval, skills, templates
    │
    ├── .obsidian/                  # Obsidian config (hidden by Obsidian)
    └── .memoria/                   # Memoria tooling (hidden by Obsidian)
```

---

## Vault folders

| Folder | Purpose | Primary writer |
| --- | --- | --- |
| `00-meta/` | The human's read surface: dashboards | Human (reads) |
| `10-inbox/` | Capture zone: fleeting notes, answer drafts, discovery candidates | Human / Librarian / Writer |
| `20-sources/` | Ingested sources: papers, items, entities | Librarian |
| `30-synthesis/` | Canonical knowledge: claims, reference notes, MOCs | Human |
| `40-workbench/` | Project scratch: maps, framing, canvas, drafts, verification, code | Multiple profiles (own subfolders) |
| `50-deliverables/` | Terminal outputs: manuscripts, presentations, media, releases | Human / Coder (export task) |
| `90-assets/` | Extracted figures, PDFs stay in Zotero | Librarian (Marker extracts) |
| `95-archive/` | Superseded notes; never deleted | Human |
| `99-system/` | Machine-consumed/generated, Obsidian-visible: logs, board export, metrics, eval, skills, templates | Linter / board_export / metrics_aggregate / QuickAdd |

### `00-meta/` subtree

```text
00-meta/
└── 01-dashboards/
    ├── daily-health.md             # the Daily Health dashboard
    ├── audit-log.md
    ├── board-state.md
    ├── contradictions.md
    ├── discuss-queue.md
    ├── drift-watch.md
    ├── fleet-health.md
    ├── loose-ends.md
    ├── open-questions.md
    ├── reading-pipeline.md
    └── weekly-review.md
# (human-facing notes — home, research-directions, troubleshooting — sit at the vault root;
#  the former 04-reference notes live on the website; templates + machine-generated
#  logs/board/metrics/eval/skills moved to 99-system/ — see below)
```

### `99-system/` subtree

Machine-consumed and -generated data — read by QuickAdd (`templates/`) and Dataview/exporters (`logs/`, `board/`, `metrics/`). It must be Obsidian-visible (QuickAdd resolves paths through the vault index and Dataview can't query dotfolders, so none of it can live in `.memoria/`), yet the human never opens it directly — hence its own root bucket, last in the tree, rather than mixed into the human-read `00-meta/`. Subfolders are unnumbered.

```text
99-system/
├── logs/                           # see reference/telemetry.md for every schema
│   ├── audit.jsonl                 # pending (created by policy MCP at first run)
│   ├── sessions/                   # per-session logs from Linter
│   ├── board-state.jsonl           # pending (board_export.py — per-lane queue snapshot)
│   ├── board-transitions.jsonl     # pending (board_export.py — card status/review changes)
│   ├── disposition.jsonl           # pending (board_export.py — accept : edit : reject, un-backfillable)
│   ├── cost.jsonl                  # pending (board_export.py — API spend + tokens per card)
│   ├── lint-findings.jsonl         # pending
│   └── cron-history.jsonl          # pending
├── board/                          # markdown board export — ships empty (.keep); pending
├── metrics/                        # fleet + eval metrics — ships empty (.keep); deferred
├── eval/                           # vault eval gold tasks — ships empty (.keep)
├── skills/                         # skill-governance registry — ships empty (.keep); deferred
└── templates/                      # 16 note templates + screening-protocol (QuickAdd instantiates these)
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
│   │   └── data.json               # points at .memoria/memoria.bib
│   ├── obsidian-git/
│   ├── homepage/                  # obsidian-homepage plugin (id: homepage); data.json opens home.md
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
│   │       └── obsidian-paper-note/  # authored skill (shared skills are global: ~/.hermes/skills/)
│   ├── memoria-mapper/
│   │   ├── SOUL.md
│   │   ├── cron/
│   │   │   └── scheduled.yaml      # shipped (actual task definitions)
│   │   └── skills/ (.keep)
│   ├── memoria-socratic/   (SOUL.md + cron/.keep + skills/.keep)
│   ├── memoria-writer/     (SOUL.md + cron/.keep + skills/.keep)
│   ├── memoria-verifier/   (SOUL.md + cron/.keep + skills/retraction-check/)
│   ├── memoria-coder/      (SOUL.md + cron/.keep + skills/.keep)
│   └── memoria-linter/
│       ├── SOUL.md
│       ├── detectors.py            # shipped (9 deterministic stdlib checks; 3 are structural detectors)
│       ├── structural-detectors.md # shipped
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
│   ├── board_export.py             # shipped (board → 99-system/board/ + board-state/transitions/disposition/cost.jsonl)
│   ├── metrics_aggregate.py        # shipped (board+audit → 99-system/metrics/ trust-score notes)
│   └── requirements.txt            # shipped (mcp, PyYAML)
│       # tasks_mcp.py — deferred, not needed (native Hermes kanban tools cover it)
├── csl/
│   └── .keep                       # shipped: placeholder for CSL citation style files
├── memoria.bib                     # pending: user-generated by Better BibTeX auto-export
├── project-hints.yaml.example      # shipped
└── tool-registry.yaml              # shipped (per-profile tool allowlist)
```

---

## Vault skeleton: human-facing notes

Notes that ship with the starter vault for human reference — three at the vault root (the human's cockpit), plus a few in `00-meta/` and `.memoria/`.

| Note | Purpose | Maintained by |
| --- | --- | --- |
| `home.md` | Vault-root front door, opened on launch by obsidian-homepage. One status glance, then links to dashboards, the in-vault help note, common operations, and the website. | Human (rarely changes) |
| `research-directions.md` | Current research priorities, open questions, synthesis gaps, papers to prioritize. Librarian reads this at session start. | Human (refresh weekly) |
| `troubleshooting.md` | Verify the plumbing, the three core workflows (ingest, review, export) with minimal commands and fallbacks, and recovery — for when Hermes or ACP is down. Folds in the former `system-status` health snapshot. Kept in-vault at the root — needed precisely when offline/down. | Human (rarely changes) |
| `99-system/templates/screening-protocol.md` | Fill-in PRISMA / ASReview screening protocol template — used only in systematic-review mode (ADR-16/19). | Human (per review) |
| `.memoria/design-system.md` | Canonical visual-style tokens: palette, typography, spacing, layout, motion, voice. Read by the CSS-snippet generators and Pandoc export (machine config). | Human (edits define the brand) |

The other former `00-meta/04-reference/` notes — getting-started, system-map, agent-roles, profile-policies, obsidian-config, dataview-cheatsheet, performance-checklist, vocabulary-example — now live **only on the [website](https://eranroseman.github.io/memoria-vault/)** (the vault is not a place for product reference docs); the vault links out to them.

The Linter's `skeleton-drift` detector flags notes whose `updated` timestamp lags the corresponding design file.

---

## File naming conventions

| Artifact | Convention | Example |
| --- | --- | --- |
| Note files | `kebab-case.md` | `receptivity-detection-timing.md` |
| Paper notes | Citekey as filename | `mamykina2010sense.md` |
| Template files | `<type>.md` | `claim-note.md`, `paper-note.md` |
| Dashboard files | `kebab-case.md` | `weekly-review.md` |
| Lane-override files | `<short-name>.yaml` | `librarian.yaml` |
| Profile dirs | `memoria-<name>/` | `memoria-librarian/` |
| Log files | `kebab-case.jsonl` | `audit.jsonl` |

**Constraint:** No spaces in vault file names. Hermes path handling and shell scripts do not support them.
