# Consistency-audit brief

Standing scope for `consistency-audit` runs against this repository. The skill
is cross-repo and holds the method.
This file holds what is specific to Memoria: the surfaces worth naming, the
concerns that recur here, and the things a generic audit would waste effort on.

The skill reads this file itself at scope time; there is nothing to pass when
invoking it.

Nothing here overrides the skill. In particular its Iron Law stands: no finding
reaches the report until you have tried to refute it.

## Do not re-audit what a checker already owns

`scripts/verify` runs these every commit; this repo's one gate is what the skill
calls a *checker*. Candidates in their territory are its job, and repeating them
by hand produces noise that looks like signal:

| Gate | Owns |
| --- | --- |
| `doc_link_targets` | link targets resolve, stay in `docs/`, anchors exist, no absolute paths |
| `doc_cited_paths` | inline-code `src/`, `scripts/`, `tests/`, `docs/` citations exist |
| `schema_doc_drift` | reference docs match the live type schemas |
| `doc_claims_gate` | CLI claims in docs match the parser |
| `checked_terminology_gate` | `checked` used with a meaning the glossary reserves |
| `mermaid-parse` | diagram fences parse at the pinned mermaid version |
| `cspell`, `vale`, `markdownlint` | spelling, terminology casing, structure |

If the audit finds a *class* these miss, the deliverable is a *checker spec* —
propose the gate, do not propose a recurring manual sweep.

## Standing concerns

**Third-party claims.** Verify every claim about Obsidian, Zotero, MCP hosts,
and the packaged Obsidian adapter against the integration's own reference page,
and against the adapter source where one is cited. These drift without any
commit here, because upstream moves on its own. (There is no "Hermes" component
in this repository; do not go looking for one.)

**Vault design conformance.** Read the packaged workspace seed —
`src/memoria_vault/product/workspace_seed/` — against
`docs/reference/system/on-disk-layout.md` and the `docs/reference/data-model/`
pages. Every deviation cites the doc that defines the shape. Audit the **seed**,
not `test-vault/`: that directory is gitignored and reconstructible, so a
candidate there describes a build artifact and dies at the next rebuild.

**External links.** For each external URL in published docs, classify it
`essential` (a real source, a spec, a cited work) or `internalize` (content
that should be a Memoria page, or a link that has become decoration). Link rot
is out of scope — nothing here can check reachability offline.

**Docs-to-vault references.** The gates verify links *resolve*. This is the
judgment half: places where published docs describe seed content without linking
to it, and places where a link points at the wrong authority — a page rather
than the schema that decides, or the seed rather than the reference that
documents it. Unpublished targets take a GitHub blob URL, per CONTRIBUTING.

## Scope defaults

Audit `docs/` (published), `src/memoria_vault/product/workspace_seed/`, the
`docs/agents/` configuration pages, and every Markdown file at the repository
root — `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CODE_OF_CONDUCT.md`,
`CONTEXT.md`, `CONTRIBUTING.md`, `README.md`, `SECURITY.md`.

Excluded unless asked, each for a stated reason:

- `design-history/` — frozen by design; a stale claim there is an accurate
  record of what was true then, not drift.
- `docs/superpowers/` — working records, point-in-time. Thirty rotted code
  citations live here and are not defects; they record where code used to be.
- `test-vault/` — gitignored build artifact.
- Everything else tracked — `src/` outside the seed, `tests/`, `scripts/`,
  `packages/`, `.github/`, and the root config files. These are code and
  configuration: read them freely as *evidence* for a finding, but they are not
  audited as prose surfaces. A contradiction inside them belongs to a code
  review.

## Where a *record* deliverable goes

The skill's *record* deliverable wants the reason written down in the home that
owns that class of ruling. Here:

| Class | Home | Machine form |
| --- | --- | --- |
| Term meaning or usage | `docs/reference/data-model/glossary.md` | `.vale/styles/config/vocabularies/Memoria/` (same PR, per `.vale.ini`) |
| Load-bearing code exception | comment or docstring at the site | the test that breaks if you "fix" it |
| Architectural decision | `docs/adr/` | — |
| Anything backlog-shaped | a GitHub issue | — |

Never a second ledger: no audit-exceptions file, and never a second glossary.
