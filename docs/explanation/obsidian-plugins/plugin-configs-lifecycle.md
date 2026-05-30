---
topic: plugins
---

# Plugin config lifecycle

How Memoria's Obsidian plugin `data.json` files are shipped, kept in sync with the design, and audited for drift. The actual config files live in the starter vault at `.obsidian/plugins/<plugin>/` — this is a governance doc, not a folder of configs. The per-plugin reference for what each setting means lives alongside this file (e.g., [agent-client.md](../../reference/plugins/agent-client.md), [obsidian-citation-plugin.md](../../reference/plugins/obsidian-citation-plugin.md)).

## Where configs live

Under direct profile management, the plugin configs ship **inside the starter vault**:

```text
memoria-vault/
└── .obsidian/
    └── plugins/
        ├── obsidian-citation-plugin/data.json
        ├── agent-client/data.json.example
        ├── obsidian-local-rest-api/data.json.example
        └── callout-manager/data.json.TODO
```

When the human clones the starter vault and opens it in Obsidian, the plugins read these files directly. There is no "template directory" the human copies from — the file at `data.json` *is* the authoritative config. The exceptions are `.example` and `.TODO` files, described below.

## The three suffix conventions

The filename suffix is the contract. Each one signals a different relationship to the human's working file.

| Suffix | Shipped state | Human action | `plugin-config-drift` detection |
|---|---|---|---|
| `data.json` | Authoritative; ready to use as-is | None — Obsidian reads it directly | Strict: working tree vs git HEAD must match (human-state extras allowed) |
| `data.json.example` | Template; contains placeholders (`{{HOME}}`, `REPLACE_ON_FIRST_LAUNCH`) or generated secrets | Copy to `data.json` (gitignored), fill in machine-specific values, restart Obsidian | Partial: non-placeholder keys in working `data.json` must match the `.example` |
| `data.json.TODO` | Not yet authored; schema unverified | None — wait for the schema to be settled and the file renamed | Skipped entirely |

## What ships and why

| Plugin | Ships | Why this suffix |
|---|---|---|
| `obsidian-citation-plugin` | `data.json` | The `literatureNoteContentTemplate` embeds Memoria's paper-note frontmatter, `_proposed_classification`, and `_enrichment` blocks. Changes here are schema migrations. |
| `agent-client` | `data.json.example` | Configures four ACP profiles in the picker, all with `autoAllowPermissions: false`. The `command` paths inside each agent entry use `{{HOME}}` placeholders the human must replace with their absolute paths. |
| `obsidian-local-rest-api` | `data.json.example` | The real `data.json` contains generated secrets (enumerated in [obsidian-local-rest-api](../../reference/plugins/obsidian-local-rest-api.md)) and must be gitignored; the plugin regenerates them on first launch. The `.example` documents the non-secret shape. |
| `callout-manager` | `data.json.TODO` | Plugin's `data.json` schema hasn't been verified against an installed version yet. The `.TODO` documents intent (three callout types: `[!brief]`, `[!suggestions]`, `[!verification]`) but doesn't commit to a schema. |

## What doesn't ship and why

| Plugin | Why no config ships |
|---|---|
| `dataview` | Only three load-bearing settings (`enableJs`, `refreshEnabled`, `refreshInterval`). Prose suffices; configure via the UI. |
| `templater-obsidian` | Three top-level settings. Prose suffices for the core toggle set; user scripts under `00-meta/03-templates/scripts/` *do* matter to Memoria (the Memoria Linter's safe-and-unambiguous Templater script lives there — see [the Memoria Linter design summary](../profiles/linter.md)) but those are vault content, not plugin config. |
| `obsidian-git` | Settings vary by [deployment option](../../project/roadmap/deployment-options.md). Shipping one config would force the human to remember which one matches their setup. |
| `obsidian-kanban` | No Memoria-specific configuration; default settings work. |
| `smart-connections` | Treated as a parallel peer to Memoria, not a wired component. [Mapper](../profiles/mapper.md) does rule-based, reviewable corpus work; Smart Connections does statistical, opaque similarity. Complementary but Memoria's design depends on neither. |
| [`omnisearch`](omnisearch.md) | Indexing depth and excluded folders are workflow-personal, not design-standard. [Librarian](../profiles/librarian.md) doesn't depend on it (search calls go through Hermes tools, not the Obsidian plugin). |
| `pdf-plus` | Settings are human-preference (highlight colors, link format). |
| `supercharged-links` | Style snippet ships at `.obsidian/snippets/memoria-link-colors.css`; the plugin's own `data.json` just points at the snippet. |
| `commander` | Pure human preference (which commands to expose). |

## When to update a shipped config

A shipped config (in `memoria-vault/.obsidian/plugins/<plugin>/`) needs to be updated when **either**:

1. **A Memoria design change shifts the standard settings.** Examples: the `_enrichment` block schema changes → `obsidian-citation-plugin/data.json`'s `literatureNoteContentTemplate` must change.
2. **The underlying plugin's `data.json` schema migrates.** A settings key gets renamed, removed, or replaced. When a plugin upgrade is accepted, diff a freshly-saved `data.json` from a clean install against the committed version and reconcile differences explicitly.

Update path: edit the file in `memoria-vault/.obsidian/plugins/<plugin>/`, commit. The next `git pull` propagates the change to anyone using the starter vault.

## `plugin-config-drift` enforcement mechanism

The [Memoria Linter's plugin-config-drift detector](../profiles/linter.md) (full procedure in the Memoria Linter's `M-detectors.md` runtime reference) audits drift between the human's **working tree** version of `.obsidian/plugins/<plugin>/data.json` and the version at **git HEAD**. Under direct profile management there is no separate "template" location to compare against — the committed file *is* the template.

Procedure:

1. For each `.obsidian/plugins/<plugin>/data.json` (or `.example` / `.TODO` variant), read the working-tree contents.
2. Read the same file as committed at git HEAD (`git show HEAD:.obsidian/plugins/<plugin>/data.json`).
3. Compare per the suffix's enforcement level (see table above).
4. Ignore human-extra keys that are present in working but not in HEAD (`savedSessions`, `lastUsedModels`, plugin-generated runtime state).
5. Report each remaining drift with the plugin, the key, and the expected vs actual value.

### Missing-working-file cases

Two cases where the working file is absent rather than drifted; `plugin-config-drift` must report them distinctly so they don't get conflated with real drift:

- **`data.json` committed at HEAD, no working file in the human's tree.** Reported as `missing working config` — the human deleted the file (or never extracted it from the clone). Severity MEDIUM, same as drift.
- **`data.json.example` committed at HEAD, no working `data.json` in the human's tree.** Reported as `first-time setup pending` — the human cloned the vault but hasn't yet copied the example to `data.json` and filled in placeholders. Severity **LOW** (it's a setup gap, not drift). Reported once per plugin, not repeatedly. The dashboard query for active `plugin-config-drift` findings de-prioritizes these so they don't crowd the human's attention on a fresh install.

The full per-case procedural detail (Case A canonical, Case B templated, Case C first-time setup, Case D unverified `.TODO`) lives in the Memoria Linter's `M-detectors.md` runtime reference.

Enforcement per shipped file:

| File | Enforcement specifics |
|---|---|
| `obsidian-citation-plugin/data.json` | Strict. Full `literatureNoteContentTemplate` checked — drift means the paper-note schema has shifted. |
| `obsidian-local-rest-api/data.json.example` | Partial. `enableInsecureServer`, `port`, `insecurePort` enforced. `apiKey`, `crypto.*` excluded as placeholders. |
| `agent-client/data.json.example` | Partial. `defaultAgentId`, `autoAllowPermissions`, `autoMentionActiveNote`, `chatViewLocation` enforced. `command` paths excluded (contain `{{HOME}}`). `savedSessions`, `lastUsedModels` excluded as runtime state. |
| `callout-manager/data.json.TODO` | Skipped until the schema is verified and the file is renamed (drop the `.TODO`). |

## Severity and the `autoAllowPermissions` escalation

`plugin-config-drift` is **MEDIUM** severity by default — drift here doesn't break the system, but means the human's Obsidian behavior may differ from the design's expectation. A `plugin-config-drift` finding alone produces a `REVIEW` verdict band, not `FAIL`.

The one documented escalation: if `plugin-config-drift` finds that `agent-client.autoAllowPermissions` has drifted from `false` to `true`, the severity is **HIGH**. That setting bypasses the per-tool-call approval gate ACP relies on, which composes with the policy MCP to keep human-in-the-loop. Silently turning it off undermines a security invariant; the Memoria Linter treats it as a verdict-band-failing finding.

## Remediation

The detector never auto-fixes. Two paths the human chooses between:

- **The drift is unintentional.** Revert the working file to git HEAD: `git restore .obsidian/plugins/<plugin>/data.json`. Restart Obsidian. The plugin loads the authoritative config.
- **The drift is deliberate.** Stage and commit: `git add .obsidian/plugins/<plugin>/data.json && git commit -m "update <plugin> config: <reason>"`. HEAD now reflects the new authoritative setting; the next lint pass is clean.

The detector's contract: it reports the *fact* of drift, not which side is right. That decision is the human's. The `.example` variant has the same remediation paths applied to the working `data.json` derived from the example — either copy the example again (revert) or update the `.example` to reflect the new authoritative shape (commit).

## Plugins removed from lifecycle enforcement

Removed from lifecycle enforcement post-ADR-24: see [ADR-24](../../project/decisions/24-obsidian-linter-reference-only.md).
