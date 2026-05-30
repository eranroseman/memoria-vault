---
topic: profiles
---

# Profile commands (reference)

The Core commands column in the [Lane permissions matrix](profile-matrices.md#lane-permissions-matrix) lists the verbs each profile uses; per-profile skill and tool surfaces are documented in the same matrix and in the per-profile design summaries in this folder (`librarian.md`, `mapper.md`, etc.). Beyond the core verbs, this is the full operational command catalog with dry-run defaults and owner profiles. Many of these are also described inline in [workflows/README.md](../how-to/workflows/README.md).

| Command | Purpose | Primary profile | Dry-run? |
| --- | --- | --- | --- |
| `ingest` | Create the right note type in the right folder with enrichment. | Librarian | No (creates notes) |
| `find` | Forward / backward citation search or concept-driven search. | Librarian | No (writes candidates) |
| `enrich` | Re-run API enrichment on existing notes. | Librarian | No |
| `classify` | Re-propose `_proposed_classification` when a note still needs review. | Librarian | No |
| `obsidian-paper-note` | Full ingest pipeline including PDF extraction (via Marker). | Librarian | No |
| `export prior-labels` | Export vault papers as ASReview priors for pre-ingest screening. | Librarian | N/A |
| `scope-project` | Map the corpus for a project: cluster density, recency distribution, source diversity, gap analysis. Writes `corpus-map.md` to the project's `01-map/` folder. | Mapper | No (writes to project scratch only) |
| `gap-report` | Identify thin-coverage topics adjacent to a project brief; surfaces where the corpus is weak so the human can direct further reading. | Mapper | No |
| `cluster-map` | Render a density / recency map for an arbitrary topic across the corpus. | Mapper | No |
| `comparative-brief` | When a new source enters the queue, generate a brief comparing it against existing claims — overlap, contradiction, new constructs. Drives the inline `[!brief]` callout. | Mapper | No |
| `socratic-processing` | Question-only conversation about a paper note. No writes. | Socratic | N/A (read-only profile) |
| `lens-reading` | Read a note or cluster through a named theoretical lens. Parameterized by lens name. | Socratic | N/A (read-only profile) |
| `query` | Deterministic vault search — standalone retrieval (Librarian) or the pre-draft search step (Writer). | Librarian, Writer | No |
| `draft` | Search the vault and produce an answer note for human review. | Writer | No |
| `promote` | Propose promotion of a claim note to a reference note. Handoff only — Writer cannot move it; the human approves. | Writer | N/A (handoff) |
| `cite-check` | Verify citations in drafts before export — every citekey resolves to a real paper note. | Verifier | Yes (default) |
| `find-duplicates` | Identify semantically similar claim notes for merge review. Retrospective; runs monthly. | Verifier | Yes; never auto-merges |
| `similarity-check` | Point-of-action check: before a new claim note is filed, surface the top 3 most-similar existing notes. Flag at threshold ~0.8; never block. | Verifier | Yes; informational, never auto-merges |
| `retraction-check` | Scan paper notes against Zotero retraction alerts and CrossRef. | Verifier | Yes (default) |
| `code` | Scaffold a `code-note` handoff for the external coding agent. | Coder | No (writes code-note to project scratch) |
| `commit` | Commit one logical change per call — per-task commits, no mega-commits. | Coder | No |
| `revert` | Revert a prior Coder commit; keeps revert scope small. | Coder | No |
| `workspace` | Set up the VS Code workspace boundary (vault read-only, code zone writable) for the external coding agent. | Coder | N/A |
| `scaffold` | Generate the `code-note` skeleton from the template. | Coder | No |
| `lint` | Structural health check across the vault. Writer may invoke it in dry-run on a draft before handoff. | Linter | Yes (default) |
| `schema-check` | Verify frontmatter against the authoritative schema. | Linter | Yes |
| `schema-migrate` | Propose schema changes between versions. **Always dry-run first.** | Linter | Yes (always required first) |
| `graph-analyze` | Knowledge graph health: orphans, hubs, clusters, link density. | Linter | Yes |
| `health-report` | Roll structural findings up into the verdict band (PASS / REVIEW / FAIL). | Linter | Yes |
| `session-log` | Write per-session log file to `00-meta/02-logs/`. | Linter | N/A |
| `dry-run` | Run any Linter check in report-only mode (the default for most checks). | Linter | Yes (by definition) |
| `report` | Emit the findings report without applying a fix. | Linter | Yes (by definition) |

Rule: any command that writes to review-gated folders (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) or runs a migration must default to dry-run. `schema-migrate` in particular must never be run without reviewing the diff first.

## Related

- [profiles/README.md](../explanation/profiles/README.md) — profile overview and the Lane permissions matrix
- [workflows/README.md](../how-to/workflows/README.md) — workflows that orchestrate these commands
