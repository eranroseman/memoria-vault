---
title: Frontmatter fields
parent: Reference data model
nav_order: 1
grand_parent: Reference
---

# Frontmatter fields

The frontmatter contract for every typed document. The single source is
`.memoria/schemas/`: per-document-type field schemas in
`src/memoria_vault/product/workspace_seed/.memoria/schemas/types`, the
type-to-folder map in
`src/memoria_vault/product/workspace_seed/.memoria/schemas/folders.yaml`.
The shared loader/validator is
`src/memoria_vault/runtime/subsystems/lib/schema.py`; the linter, pre-commit
hook, and package-seed tests all read it.

Per-type schemas currently exist for `code-artifact`, `digest`, `fulltext`,
`hub`, `note`, and `project`.

## The field-kind grammar

Each type schema declares `required:` and `optional:` maps of `field: kind`,
plus an `enums:` block and optionally `required_any:`, `required_when:`, and
`forbidden:`. The kinds:

| Kind | Accepts |
| --- | --- |
| `str` | a string |
| `int` | an integer (not a bool) |
| `bool` | a boolean |
| `date` | a YAML date or an ISO-8601 date string |
| `list` | a YAML sequence |
| `map` | a YAML mapping |
| `links` | a YAML mapping from `supports`, `contradicts`, or `extends` to target lists |
| `ulid` | a valid ULID string |
| `literal:<value>` | exactly that value; for example, `type: literal:note` |
| `enum:<name>` | one of the values the schema's `enums.<name>` lists |

Unknown extra fields are accepted during the alpha migration. Schema-declared
fields still enforce the required meaning contract, and `forbidden:` fields are
rejected even though other unknown extras are allowed. A schema example
(`types/note.yaml`):

```yaml
type: note
category: notes
enums:
  mode: [claim, question, definition, work]
  question_status: [open, resolved]
  certainty: [reported, contested, unknown, hypothesized]
  item_type: [paper, dataset, repository, web-page, report]
required:
  type: literal:note
  id: ulid
  title: str
  tags: list
  links: links
optional:
  aliases: list
  annotation_ref: map
  archived: bool
  claim_text: str
  description: str
  extraction_confidence: str
  item_type: enum:item_type
  mode: enum:mode
  question_status: enum:question_status
  quote: str
  work_id: str
  temporal_scope: str
  tense: str
  topics: list
  qualifier: str
  certainty: enum:certainty
  superseded: bool
  reading: str
  anchors: list
  todo: list
  x: map
required_when:
  claim_text:
    field: mode
    equals: claim
  question_status:
    field: mode
    equals: question
  work_id:
    field: mode
    equals: work
forbidden: [citations, evidence_set, citekey, project]
```

### Note modes and conditional fields

`mode` is optional. When present, its value and extra requirement come directly
from `types/note.yaml`:

| `mode` | Conditional requirement |
| --- | --- |
| `claim` | `claim_text` must be present. |
| `question` | `question_status` must be `open` or `resolved`. |
| `definition` | No additional field is required. |
| `work` | `work_id` must be present as a string. |

These are the only mode-specific required fields. Other optional note fields
retain their declared kind regardless of mode.

## Creation forms

Templates and optional form adapters are entry points, not schema authority. The
Concept schemas above remain the validator contract. Forms may collect values
that are not frontmatter fields. The writer maps those values into the body or
structured frontmatter before validation. Free-text values from forms,
templates, or agent-proposed note candidates (the `propose-note-candidates`
worker operation) pass through content-security masking
(`neutralize_untrusted_markdown`, `src/memoria_vault/runtime/content_security.py`)
as the writer maps them in, so untrusted or agent-controlled text cannot pose
as trusted Markdown.

## Display order and grouping

The schema validates field presence and kind; display order is a shipped-vault
convention. Templates and deterministic emitters put fields in this order:

1. Human identity: `title` or `name`.
2. Schema identity: `type`, then `id` where the bundle requires it.
3. Human summary and pointer fields: `description`.
4. Type-specific state and references.
5. Relations and classification: `links`, `tags`, and type-specific maps.

## Verdict state is not frontmatter

`check_status` lives in `.memoria/memoria.sqlite`, worker requests, and read API
responses. It is not written to Concept frontmatter. Writers reject retired
frontmatter verdict fields so a forged file field cannot grant a checked verdict.

## Links and catalog resources

Documents use `work_id` to point at the SQLite catalog Work row. Backing
resource URLs and external identifiers live in `.memoria/memoria.sqlite` and
the generated `bibliography.bib` projection, not in human note frontmatter.
`links` is the required relation field for Concepts. It is a map from
`supports`, `contradicts`, or `extends` to lists of local Concept targets.

Draft write-back reuses the existing note `work_id` field for provenance when
a promoted draft passage is tied to a catalog Work. It does not add a
draft-origin or maturity frontmatter field; draft-origin remains request/journal
provenance plus DB `check_status: unchecked`.

Evidence sets for composed drafts are not frontmatter. They live as inline
`%%ev: ...%%` markers in draft body text with derived rows in SQLite; see
[Evidence sets](../control-and-policy/evidence-sets.md).
`citations` is not Concept frontmatter either; bibliography completeness is
checked against the generated `bibliography.bib`.

## Other universal fields

| Field | Kind | Notes |
| --- | --- | --- |
| `type` | `literal:` | Pins the note to its schema. Set at creation; never changed. |
| `id` | `ulid` for `note`, `hub`, and `project`; `str` for `code-artifact`, `digest`, and `fulltext` | Required on every typed document. Digest and fulltext use their source `work_id`; code-artifact uses its artifact id. |
| `title` | `str` | Human-readable Concept title. |
| `links` | `links` | Required by most Concept types (see each type's schema for exact requirements), even when empty. |
| `description` | `str` | Optional human-readable summary where the type supports it. |
| `tags` | `list` | Required local classification list, even when empty. |

## Enforcement

| Where | What |
| --- | --- |
| Pre-commit hook | Every staged `.md` Concept must pass its type schema. |
| Scheduled linter check | The `schema-check` and `frontmatter-link` detectors monitor between commits. |
| Exemptions | Most `system/` infrastructure and vault-root navigation pages are untyped and exempt. |

## Related

- The type roster and folder homes (per-type field detail lives in the schema
  directory, not either page): [Document types](document-types.md)
- The controlled classification values: [Vocabulary](vocabulary.md)
- What validates this contract: [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md)
- Where the schema files live: [On-disk layout](../system/on-disk-layout.md)
