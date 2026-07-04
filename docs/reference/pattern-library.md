---
title: Pattern library
parent: Agents and control
grand_parent: Reference
---

# Pattern library

The shipped prompt operations, the CLI worker runner, and the prompt composition
contract.

- Prompt operations are checked packaged operation manifests in
  `memoria_vault.product.capabilities.operations`.
- `memoria operation run <pattern-id> --mode test|live` is the core runner: it
  reads checked input refs, selects the manifest-pinned runner branch, records
  request/journal provenance, and stages one unchecked report note.
- To inspect the available pattern actions, see [System actions](system-actions.md).
- For provenance rationale, see [Pattern provenance: borrow, adapt, ignore](../design/why-pattern-provenance.md).

---

## The shipped operations

Eight prompt operations ship as checked packaged operation manifests and are
runnable. Each file stem is its `pattern_id`.

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
| `output_target` | path | Where the run's product is meant to land; shipped prompt operations stage under `.memoria/staging/knowledge/`. |
| `runner` | map | Required `test` and `live` branches; each branch pins `{provider, model, temperature}` and may include other runner params. |
| `version` | str | Logged with every run for provenance. |
| `adapted_from` | str (optional) | Upstream provenance of the prompt. |

The schema is enforced by the same Linter and pre-commit machinery that guards
other Concept files.

---

## The CLI Runner

`memoria operation run <pattern-id> --mode test|live` loads the checked
operation, accepts `input_text`, `input_ref`, or `input_refs` in
`--payload-json`, and runs through the same SQLite request queue as other
operations. File refs must be checked Concepts under the operation's
`allowed_paths`. The selected mode must resolve to the operation manifest's
declared `runner.test` or `runner.live` branch; the runner cannot choose an
undeclared provider or model.

The result stages one unchecked `note` report under `.memoria/staging/knowledge/`
with an `evidence_set` pointing at the checked inputs and request/journal rows
for the run, model call, derived output, and note-candidate status. The canonical
`knowledge/notes/...` target is not materialized or checked until the normal
promotion path accepts it. `model_call` rows include resolved
mode/provider/model/params and a prompt hash.

---

## Composition

Every run is prefixed with the shared voice preamble at
`system/patterns/_preamble.md`; the packaged operation manifest remains the
runner authority ([ADR-125](../adr/125-standalone-cli-engine-architecture.md)).
`{{input}}` in the operation body is replaced with `input_text`; when
`input_ref` or `input_refs` are supplied, the runner first reads each checked
Concept allowed by the operation policy and joins the referenced text under
per-file headings. Supplying both refs and raw text is allowed; raw text wins as
the substitution text while the checked refs remain attached as evidence.

The product reaches canonical notes only through the normal promotion path. A
run stages an unchecked report, records the checked inputs in the report
`evidence_set`, appends journal rows for the run/model-call/derived-output
events, and commits those staged writer changes.

---

## Related

- Why runs are provenance-logged: [Pattern provenance: borrow, adapt, ignore](../design/why-pattern-provenance.md)
- CLI command boundary: [Obsidian command palette](obsidian-command-palette.md)
- Every action the system performs: [System actions](system-actions.md)
- The picker view over the library: [Dashboards](dashboards.md)
