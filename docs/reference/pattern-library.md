---
title: Pattern library
parent: Agents and control
grand_parent: Reference
---

# Pattern library

The shipped prompt operations, the CLI worker runner, and the compatibility
`patterns_list` / `patterns_run` contract.

- Prompt operations are checked `operation` Concepts in `capabilities/operations/`.
- `memoria operation run <pattern-id>` is the core runner: it reads checked input
  refs, records request/journal provenance, and stages one unchecked report note.
- The patterns MCP (`vault-template/.memoria/mcp/patterns_mcp.py`) remains a
  compatibility prompt composer ([ADR-53](../adr/53-pattern-library.md)).
- To inspect the available pattern actions, see [System actions](system-actions.md).
- For provenance rationale, see [Pattern provenance: borrow, adapt, ignore](../design/why-pattern-provenance.md).

---

## The shipped operations

Nine prompt operations ship at `check_status: checked` and are runnable. Each
is one file under `capabilities/operations/`; the file stem is its `pattern_id`.

| Pattern (`id`) | Title | `posture` | `action` | `mode` | `input` | `output_target` |
| --- | --- | --- | --- | --- | --- | --- |
| `analyze-claims` | Analyze claims | peer-reviewer | analyze | both | selection-or-note | `.memoria/staging/knowledge/` |
| `check-falsifiability` | Check falsifiability | peer-reviewer | check | both | selection-or-note | `.memoria/staging/knowledge/` |
| `compile-source-digest` | Compile source digest | co-pi | synthesize | knowledge | checked-source | `.memoria/staging/knowledge/` |
| `compare-and-contrast` | Compare and contrast | librarian | compare | both | two-or-more-notes | `.memoria/staging/knowledge/` |
| `extract-claim-stubs` | Extract claim stubs | librarian | extract | library | source-note | `.memoria/staging/knowledge/` |
| `propose-note-candidates` | Propose note candidates | co-pi | distill | knowledge | checked-digest | `.memoria/staging/knowledge/` |
| `red-team-argument` | Red-team an argument | peer-reviewer | check | project | draft-or-claim | `.memoria/staging/knowledge/` |
| `summarize-for-recall` | Summarize for recall | librarian | summarize | both | selection-or-note | `.memoria/staging/knowledge/` |
| `surface-tensions` | Surface tensions | librarian | link | library | note-set | `.memoria/staging/knowledge/` |

`mode` filters the picker: `library` operations are for ongoing reading,
`project` operations for a writing project, `knowledge` operations for the
digest-to-note loop, and `both` for library or project use.

---

## The prompt-operation shape

Every prompt operation file is YAML frontmatter followed by a single `# Pattern` body.
The body is the prompt; `{{input}}` is the one substitution token.

| Field | Kind | Meaning |
| --- | --- | --- |
| `title` | str | Display name in the picker. |
| `type` | `literal:operation` | Identifies the Concept as an operation. |
| `check_status` | `unchecked` / `checked` / `quarantined` | Only `checked` operations are runnable. |
| `description` | str | Human summary required by the operation schema. |
| `operation_id` | str | Stable operation id; normally matches the file stem. |
| `posture` | str | The voice the run adopts, echoed back as `posture`. |
| `mode` | `library` \| `project` \| `knowledge` \| `both` | Which picker view the operation appears in. |
| `action` | str | The operation verb. |
| `input` | str | Expected input shape; documentation for the caller, not enforced. |
| `output_target` | path | Where the run's product is meant to land. Missing or gated targets force dry-run. |
| `model_hint` | str (optional) | Suggested model tier; empty means caller default. |
| `version` | str | Logged with every run for provenance. |
| `adapted_from` | str (optional) | Upstream provenance of the prompt. |

The schema is enforced by the same Linter and pre-commit machinery that guards
other Concept files.

---

## The CLI Runner

`memoria operation run <pattern-id>` loads the checked operation, accepts
`input_text`, `input_ref`, or `input_refs` in `--payload-json`, and runs through
the same SQLite request queue as other operations. File refs must be checked
Concepts under the operation's `allowed_paths`.

The result stages one unchecked `note` report under `.memoria/staging/knowledge/`
with `status: candidate`, an `evidence_set` pointing at the checked inputs, and
request/journal rows for the run, model call, and derived output. The canonical
`knowledge/notes/...` target is not materialized or checked until the normal
promotion path accepts it.

## Compatibility MCP Runner

The MCP exposes two compatibility tools. Both are read-only; neither writes a
vault note.

### `patterns_list(mode="")`

Returns checked operations, optionally filtered by `mode` (`library` / `project`
/ `knowledge`; `both`-mode operations always match). Each row is `{id, title,
mode, action, posture, output_target}`.

### `patterns_run(pattern_id, input_text="", input_ref="")`

Loads the operation by id, composes the prompt, enforces the gated-zone rule,
logs provenance, and returns the prompt for the calling agent to execute through
its normal write path.

| Return field | Meaning |
| --- | --- |
| `run_id` | 8-char id correlating the return value with its provenance line. |
| `pattern` | The `pattern_id` that ran. |
| `prompt` | The composed prompt: `preamble` + `---` + operation body with `{{input}}` substituted. |
| `output_target` | The operation's staging target, empty when dry-run. |
| `dry_run` | `true` when the target is missing or review-gated. |
| `posture` | The operation's posture, for the caller's voice. |
| `model_hint` | The operation's `model_hint`, or `null`. |
| `note` | Present only on dry-run. |
| `provenance_logged` | Present and `false` only when the provenance append failed. |

An unknown id returns `{"error": "unknown-pattern", "available": [...]}`. A
non-checked operation returns `{"error": "operation-not-checked"}`.

---

## Composition

Every run is prefixed with the shared voice preamble at
`system/patterns/_preamble.md` ([ADR-53](../adr/53-pattern-library.md)).
`{{input}}` in the operation body is replaced with `input_text`; when only an
`input_ref` is supplied, the token becomes `[see <input_ref>]`.

---

## Gated-target dry-run

A prompt operation is a proposal tool: propose, never dispose.

| `output_target` | Result |
| --- | --- |
| Empty | `dry_run: true`; no sanctioned write target. |
| Review-gated prefix from `folders.yaml` | `dry_run: true`; the Linter flags the operation file. |
| Staging home such as `.memoria/staging/knowledge/` | Live run; caller still writes through its normal path. |
| Canonical target such as `knowledge/notes/` | Dry-run by design. |

The product reaches canonical notes only through the normal promotion path.

---

## Compatibility MCP Provenance

Every compatibility MCP run appends one JSONL line to
`system/logs/patterns.jsonl` before the prompt is returned.

```json
{"timestamp": "2026-06-01T14:23:01Z", "run_id": "a1b2c3d4", "pattern": "analyze-claims", "version": "1.0", "input_ref": "knowledge/notes/example.md", "input_chars": 0, "output_target": ".memoria/staging/knowledge/", "dry_run": false}
```

| Field | Meaning |
| --- | --- |
| `timestamp` | ISO-8601 UTC, `Z`-suffixed. |
| `run_id` | Correlates with the `run_id` in the tool return value. |
| `pattern` / `version` | Which operation and version ran. |
| `input_ref` | The reference passed in, or empty when raw text was supplied. |
| `input_chars` | Length of the supplied `input_text`. |
| `output_target` | The staging target the run resolved to. |
| `dry_run` | Whether the run was a dry-run. |

A failed provenance write does not abort the run; the return value carries
`provenance_logged: false` and the runner warns on stderr.

---

## Related

- Why runs are provenance-logged: [Pattern provenance: borrow, adapt, ignore](../design/why-pattern-provenance.md)
- The palette commands that invoke the runner: [Obsidian command palette](obsidian-command-palette.md)
- Every action the system performs: [System actions](system-actions.md)
- The picker view over the library: [Dashboards](dashboards.md)
