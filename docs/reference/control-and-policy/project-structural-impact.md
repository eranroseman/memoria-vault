---
title: Project structural impact
parent: Control and policy
nav_order: 4
grand_parent: Reference
---

# Project structural impact

`memoria_vault.runtime.subsystems.processing.project.structural_impact` computes the thesis-rooted argument graph for one Project and writes a generated Project gate index note. It is deterministic operation code, not a Hermes chat skill.

## Command

```bash
python3 -m memoria_vault.runtime.subsystems.processing.project.structural_impact --vault <vault> --project <project-slug>
python3 -m memoria_vault.runtime.subsystems.processing.project.structural_impact --vault <vault> --project <project-slug> --dry-run --json
```

| Option | Contract |
| --- | --- |
| `--vault <vault>` | Runtime vault root. Defaults to the current directory when omitted. |
| `--project <project-slug>` | Project selector. When empty, the operation resolves the active project from the vault scan. |
| `--dry-run` | Computes the payload without writing the generated note. |
| `--json` | Prints the full result payload instead of only `updated:` / `unchanged:` and the output path. |

## Inputs

The operation scans markdown notes, resolves the selected Project and active Thesis, then follows authored `links.supports` and `links.contradicts` relationships. Scope terms and relation values come from the same note frontmatter fields documented in [Frontmatter fields](../data-model/frontmatter.md).

## Output note

The generated note is written next to the Project note as `project-gate-index.md`. Its frontmatter includes:

| Field | Meaning |
| --- | --- |
| `generated_by` | Always `memoria-structural-impact`. |
| `project` | Resolved Project path/identifier. |
| `active_thesis` | Thesis at the root of the argument graph. |
| `computed_at` | UTC timestamp for the last material payload change. |
| `stale` | Whether the generated analysis is stale relative to available project evidence. |
| `argument_stage` | Derived project argument readiness stage. |
| `evidence_saturation` | Derived saturation value for the scoped argument graph. |
| `displayed_confidence` | Confidence value shown to the PI. |
| `relation_count` | Count of graph relations considered. |
| `open_high_impact_gaps` | Count of open high-impact gaps. |
| `gap_findings` | Count of confident gap findings. |
| `advisories` | Count of advisory findings. |

The body contains three tables: graph nodes, gap findings, and advisories. It also embeds the full machine payload between `<!-- memoria-structural-impact:json -->` and `<!-- /memoria-structural-impact:json -->` markers.

## Write behavior

The renderer compares the new payload to the previous embedded JSON after removing `computed_at`. If the stable payload is unchanged, the note is not rewritten and the prior `computed_at` is preserved. If the stable payload changes and `--dry-run` is not set, the operation rewrites the generated note.

## Gap taxonomy

The payload separates confident gap kinds from advisory gap kinds. Confident gaps are counted in `gap_findings`; advisory gaps are shown separately so dashboards can surface them without treating them as blocking structural defects.

## Related

- Project workflow guide: [Analyze a project argument](../../how-to-guides/project/analyze-a-project-argument.md)
- Project fields: [Frontmatter fields](../data-model/frontmatter.md)
- Operation inventory: [Operations](../commands-and-transports/operations.md)
