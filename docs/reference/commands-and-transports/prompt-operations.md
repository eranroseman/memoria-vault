---
title: Prompt operations
parent: Commands and transports
nav_order: 11
grand_parent: Reference
---

# Prompt operations

The shipped prompt operations, the CLI worker runner, and the prompt composition
contract.

- Prompt operations are package-owned operation manifests in
  `memoria_vault.product.capabilities.operations`.
- `memoria operation run <pattern-id> --mode test|live` is the core runner: it
  reads checked input refs, selects the manifest-pinned runner branch, records
  request/journal provenance, and stages one unchecked report note.
- To inspect the available pattern actions, see [System actions](system-actions.md).
- For provenance rationale, see [Pattern provenance: borrow, adapt, ignore](../../explanation/rationale/evidence/why-pattern-provenance.md).

---

## The shipped operations

Eight prompt-operation patterns ship as package-owned operation manifests and
are runnable when manifest validation passes. Each file stem is its
`pattern_id`. Deterministic project WRITE operations such as
`write-project-slice`, `compose-project-draft`, `verify-project-draft`, and
`promote-draft-passage` are also packaged capability manifests, but they are
not prompt patterns and are listed through `memoria operation list`.

| Pattern (`id`) | Title | `posture` | `action` | `mode` | `input` | `output_target` |
| --- | --- | --- | --- | --- | --- | --- |
| `analyze-claims` | Analyze claims | peer-reviewer | analyze | both | selection-or-note | `.memoria/staging/notes/` |
| `check-falsifiability` | Check falsifiability | peer-reviewer | check | both | selection-or-note | `.memoria/staging/notes/` |
| `compile-source-digest` | Compile source digest | co-pi | synthesize | knowledge | checked-source | `.memoria/staging/digests/` |
| `compare-and-contrast` | Compare and contrast | librarian | compare | both | two-or-more-notes | `.memoria/staging/notes/` |
| `extract-claim-stubs` | Extract claim stubs | librarian | extract | library | checked Work or digest | `.memoria/staging/notes/` |
| `propose-note-candidates` | Propose note candidates | co-pi | distill | knowledge | checked-digest | `.memoria/staging/notes/` |
| `red-team-argument` | Red-team an argument | peer-reviewer | check | project | draft-or-claim | `.memoria/staging/notes/` |
| `summarize-for-recall` | Summarize for recall | librarian | summarize | both | selection-or-note | `.memoria/staging/notes/` |

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
| `description` | str | Human summary required by the operation schema. |
| `operation_id` | str | Stable operation id; normally matches the file stem. |
| `posture` | str | The voice the run adopts, echoed back as `posture`. |
| `mode` | `library` \| `project` \| `knowledge` \| `both` | Which picker view the operation appears in. |
| `action` | str | The operation verb. |
| `input` | str | Expected input shape; documentation for the caller, not enforced. |
| `output_target` | path | Where the run's product is meant to land; shipped prompt operations stage under `.memoria/staging/notes/` or `.memoria/staging/digests/`. |
| `runner` | map | Required `test` and `live` branches; each branch pins `{provider, model, temperature}` and may include other runner params. |
| `untrusted_fields` | list | Raw user/provider text fields that must be sealed before entering a model prompt. |
| `version` | str | Logged with every run for provenance. |
| `adapted_from` | str (optional) | Upstream provenance of the prompt. |

Package validation rejects missing required fields, undeclared runner branches,
malformed `untrusted_fields`, and retired verdict fields such as `check_status`
or `standing`.

---

## The CLI Runner

`memoria operation run <pattern-id> --mode test|live` loads the checked
operation, accepts `input_text`, `input_ref`, or `input_refs` in
`--payload-json`, and runs through the same SQLite request queue as other
operations. File refs must be checked Concepts under the operation's
`allowed_paths`. The selected mode must resolve to the operation manifest's
declared `runner.test` or `runner.live` branch; the runner cannot choose an
undeclared provider or model.

The result stages one unchecked `note` report under `.memoria/staging/notes/`
with request/event-log rows that point at the checked inputs, model call,
derived output, and note-candidate status. The canonical `notes/...` target is
not materialized or checked until the normal promotion path accepts it.
`model_call` rows include resolved
mode/provider/model/params, a prompt hash, and the hash of the raw model output.
Before staging the report, the runtime neutralizes images/embeds, raw HTML, and
external URLs in that output. The journal hash remains bound to what the model
returned, not the neutralized rendering.

---

## Composition

Every run is prefixed with the shared voice preamble; the packaged operation
manifest remains the runner authority
([the standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). `{{input}}` in
the operation body is replaced with a reference to sealed untrusted data. When
`input_ref` or `input_refs` are supplied, the runner first reads each checked
Concept allowed by the operation policy and joins the referenced text under
per-file headings. Supplying both refs and raw text is allowed; raw text wins as
the sealed substitution text while the checked refs remain attached as evidence.

The product reaches canonical notes only through the normal promotion path. A
run stages an unchecked report, records checked-input provenance in the
request/event log, appends rows for the run/model-call/derived-output events,
and commits those staged writer changes.

---

## Related

- Why runs are provenance-logged: [Pattern provenance: borrow, adapt, ignore](../../explanation/rationale/evidence/why-pattern-provenance.md)
- CLI command boundary: [CLI](cli.md)
- Every action the system performs: [System actions](system-actions.md)
- The planned picker view over the library: [Dashboards](../analysis-and-surfaces/dashboards.md)
