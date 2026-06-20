---
title: Pattern library
parent: Reference
---

# Pattern library

The shipped runnable patterns, the pattern-note schema, and the `patterns_list` / `patterns_run` contract. Patterns are *data* — markdown prompt-transformations in `system/patterns/` — and the patterns MCP (`src/.memoria/mcp/patterns_mcp.py`) is the single audited chokepoint that runs them ([ADR-53](../adr/53-pattern-library.md)). The runner never writes content: it composes a prompt and hands it back through the gated path the calling agent already uses. To invoke one from Obsidian, see [Run a pattern](../how-to-guides/knowledge/run-a-pattern.md); for why provenance is recorded, see [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md).

---

## The shipped patterns

Seven patterns ship at `lifecycle: current` (runnable). Each is one file under `system/patterns/`; the file `stem` is its `pattern_id`.

| Pattern (`id`) | Title | `posture` | `action` | `mode` | `input` | `output_target` |
| --- | --- | --- | --- | --- | --- | --- |
| `analyze-claims` | Analyze claims | peer-reviewer | analyze | both | selection-or-note | `projects/` |
| `check-falsifiability` | Check falsifiability | peer-reviewer | check | both | selection-or-note | `projects/` |
| `compare-and-contrast` | Compare and contrast | librarian | compare | both | two-or-more-notes | `projects/` |
| `extract-claim-stubs` | Extract claim stubs | librarian | extract | library | source-note | `notes/fleeting/` |
| `red-team-argument` | Red-team an argument | peer-reviewer | check | project | draft-or-claim | `projects/` |
| `summarize-for-recall` | Summarize for recall | librarian | summarize | both | selection-or-note | `notes/fleeting/` |
| `surface-tensions` | Surface tensions | librarian | link | library | note-set | `projects/` |

`mode` filters the picker: `library` patterns are for ongoing reading, `project` patterns for a writing project, `both` for either. The set is authored directly — the files *are* the instances, there is no template — and staged into the golden copy like the other system files ([Installer (bootstrap)](installer.md)).

---

## The pattern-note schema

Every pattern file is YAML frontmatter followed by a single `# Pattern` body. The body is the prompt; `{{input}}` is the one substitution token.

| Field | Kind | Meaning |
| --- | --- | --- |
| `title` | str | Display name in the picker. |
| `type` | `literal:pattern` | Identifies the note as a pattern; non-patterns are skipped. |
| `lifecycle` | `proposed → current → archived` | Only `current` patterns are runnable; `run` on a non-current pattern errors `pattern-not-current`. |
| `posture` | enum | The voice the run adopts (`librarian` / `peer-reviewer`) — echoed back to the caller as `posture`. |
| `mode` | `library` \| `project` \| `both` | Which picker view the pattern appears in. |
| `action` | str | The verb (`analyze` / `check` / `compare` / `extract` / `summarize` / `link`). |
| `input` | str | The expected input shape (`selection-or-note`, `source-note`, `note-set`, …) — documentation for the caller, not enforced. |
| `output_target` | path | Where the run's product is meant to land. An empty or review-gated target forces dry-run (below). |
| `model_hint` | str (optional) | A suggested model tier, passed through as `model_hint`; empty means caller's default. |
| `version` | str | Logged with every run for provenance. |
| `adapted_from` | str (optional) | Upstream provenance of the prompt (e.g. `fabric/analyze_claims`). |
| `created` | date | — |

The schema is enforced by the Linter and the pre-commit hook, the same machinery that guards every other system note.

---

## The runner

The MCP exposes two tools. Both are read-only; neither writes a vault note.

### `patterns_list(mode="")`

Returns the runnable (`lifecycle: current`) patterns, optionally filtered by `mode` (`library` / `project`; `both`-mode patterns always match). Each row is `{id, title, mode, action, posture, output_target}`. Files whose name starts with `_` (the preamble) are skipped.

### `patterns_run(pattern_id, input_text="", input_ref="")`

Loads the pattern by id, composes the prompt, enforces the gated-zone rule, logs provenance, and returns the prompt for the calling agent to execute and write through its normal gated path.

| Return field | Meaning |
| --- | --- |
| `run_id` | 8-char id correlating the return value with its provenance line. |
| `pattern` | The `pattern_id` that ran. |
| `prompt` | The composed prompt: `preamble` + `---` + pattern body with `{{input}}` substituted. |
| `output_target` | The pattern's staging target (empty when dry-run). |
| `dry_run` | `true` when the target is missing or review-gated — the run produces a prompt but no sanctioned write target. |
| `posture` | The pattern's posture, for the caller's voice. |
| `model_hint` | The pattern's `model_hint`, or `null`. |
| `note` | Present only on dry-run: explains the target was missing or gated. |
| `provenance_logged` | Present (and `false`) only when the provenance append failed — the prompt still returns, but the run left no audit line (also warned on stderr). |

An unknown id returns `{"error": "unknown-pattern", "available": [...]}`; a non-current pattern returns `{"error": "pattern-not-current"}`.

---

## Composition: preamble + pattern + input

Every run is prefixed with the shared voice preamble at `system/patterns/_preamble.md` ([ADR-53](../adr/53-pattern-library.md)). It is non-negotiable regardless of the pattern, and encodes four rules: output is raw material for the PI to rewrite; propose, never assert; cite, don't fabricate (a missing source is a visible `[no source]`, never invented); and stay inside the provided input. `{{input}}` in the pattern body is replaced with `input_text`; when only an `input_ref` is supplied (e.g. the active note path), the token becomes `[see <input_ref>]` and the executing agent reads that reference itself.

---

## Gated-target dry-run

A pattern is a *proposal* tool — propose-not-dispose holds. `patterns_run` refuses to hand back a sanctioned write target inside a review-gated zone: when `output_target` is empty, or starts with a gated prefix (read from `.memoria/schemas/folders.yaml` `gated_prefixes`, falling back to the policy core's `REVIEW_GATED_PREFIXES`), the run degrades to `dry_run: true` and the Linter flags the pattern file. The shipped patterns target only staging homes (`projects/` scratch and `notes/fleeting/`), so they run live; a pattern pointed at `notes/claims/` or `catalog/` would dry-run by design. The product still reaches canonical notes only through the normal human gate.

---

## Provenance

Every run appends one JSONL line to `system/logs/patterns.jsonl` before the prompt is returned — the audit trail that makes pattern output traceable.

```json
{"timestamp": "2026-06-01T14:23:01Z", "run_id": "a1b2c3d4", "pattern": "analyze-claims", "version": "1.0", "input_ref": "notes/sources/vaswani2017.md", "input_chars": 0, "output_target": "projects/", "dry_run": false}
```

| Field | Meaning |
| --- | --- |
| `timestamp` | ISO-8601 UTC, `Z`-suffixed (the [Telemetry & logs](telemetry.md) convention). |
| `run_id` | Correlates with the `run_id` in the tool return value. |
| `pattern` / `version` | Which pattern and pattern version ran. |
| `input_ref` | The reference passed in (a note path), or empty when raw text was supplied. |
| `input_chars` | Length of the supplied `input_text` (0 when only a reference was passed). |
| `output_target` | The staging target the run resolved to. |
| `dry_run` | Whether the run was a dry-run (missing/gated target). |

A failed provenance write does not abort the run — the prompt is the product — but the return value carries `provenance_logged: false` and a stderr warning so the operator knows the run left no line.

---

## Related

- Running a pattern from Obsidian: [Run a pattern](../how-to-guides/knowledge/run-a-pattern.md)
- Why runs are provenance-logged: [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md)
- The palette commands that invoke the runner: [Obsidian command palette](obsidian-command-palette.md)
- Every action the system performs: [System actions](system-actions.md)
- The picker view over the library: [Dashboards](dashboards.md)
