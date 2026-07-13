---
title: Worklists
parent: Control and policy
nav_order: 5
grand_parent: Reference
---

# Worklists

`memoria_vault.runtime.subsystems.lib.worklists` turns a high-cardinality
report into one file-backed batch review surface. The operation writes many
`projection: worklist-item` rows and raises exactly one aggregate Inbox
`attention_kind: work-prompt` projection for the PI.

## Command

```bash
python3 -m memoria_vault.runtime.subsystems.lib.worklists emit --vault <vault> --report report.json --title "Batch title"
```

| Option | Contract |
| --- | --- |
| `emit` | The only CLI subcommand. |
| `--vault <vault>` | Runtime vault root. Required. |
| `--report <file>` | JSON report containing `items` or `rows`. Required. |
| `--title <text>` | Overrides the report title. Optional. |
| `--workflow <name>` | Default group/category for rows without `group` or `category`; defaults to `screen`. |

## Report JSON

The report must contain either `items` or `rows` as a list. Each row may be an object or a scalar. Scalar rows are converted to `{"title": <value>, "item_ref": <value>}`.

| Report field | Use |
| --- | --- |
| `title` | Batch title when `--title` is omitted. |
| `source_report` | Source path recorded on emitted item notes and in the Inbox prompt. |
| `worklist` / `worklist_id` | Stable worklist slug input. If absent, the title is slugged. |
| `items` / `rows` | Row list. |

Row objects may include `title` or `name`, `item_ref` or `target` or `path` or `citekey` or `url` or `id`, `group` or `category`, `decision`, `rank`, `reason`, `evidence`, and `source_report`.

`decision` defaults to `proposed` and must be one of `proposed`, `include`, `exclude`, `maybe`, or `archived`.

Report-derived titles, reasons, and aggregate-prompt prose are untrusted display
text. Apply neutralizes image/embed syntax, raw HTML, and external URLs in those
fields. Structural references such as `item_ref` and `source_report` retain
their original values; the item view renders `item_ref` as code and makes
URL-bearing display prose non-clickable.

## Outputs

| Path | Shape |
| --- | --- |
| `system/worklists/<worklist>/<rank-title>.md` | One `projection: worklist-item` row per report row. |
| `inbox/work-prompt-*.md` | One `projection: attention`, `attention_kind: work-prompt` review prompt with `raised_by: worklists` and a `target` pointing at the generated worklist folder. |

The aggregate prompt uses a `worklist-<slug>` dedupe key. Re-running the same report rewrites the item notes and does not create a second prompt when the deduped prompt already exists.

## Related

- Worklist fields: [Frontmatter fields](../data-model/frontmatter.md)
- Current Concept types: [Document types](../data-model/document-types.md)
- Operation inventory: [Operations](../commands-and-transports/operations.md)
