---
title: Fix broken frontmatter
parent: Troubleshooting
nav_order: 3
---


# Fix broken frontmatter

**Symptom:** a note disappears from Dataview queries, or Obsidian's Properties panel shows a YAML parse error.

- The Obsidian Properties panel shows a YAML parse error on a note
- The note does not appear in Dataview queries that should include it
- The Linter operation reports a schema or YAML finding on this note

**Diagnosis:** the note's frontmatter contains malformed YAML, so the parser skips the whole block. Run the Linter operation to confirm and pinpoint the bad line.

**Fix:** edit the raw file outside Obsidian, correct the malformed line, and re-check.

## Detect

Run the Linter operation — report-only, zero-LLM — to confirm and identify the specific error ([Run the Linter](../operate/run-the-linter.md)):

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

Common YAML errors:

| Error | Example |
| --- | --- |
| Unclosed string | `title: "Unterminated title` |
| List indentation error | `methods:` followed by `- field-study` at wrong indent |
| Missing closing `---` delimiter | Frontmatter block never ends |
| Colon in value without quoting | `title: A Study of AI: Methods` (colon in title) |
| Tab character instead of spaces | YAML requires spaces, not tabs |

## Fix

**1. Open the raw file in an editor outside Obsidian.**

Obsidian masks the raw YAML in Properties view. Open the file in VS Code or Notepad++ to see exactly what's in the frontmatter block:

```powershell
code "catalog\papers\<citekey>.md"
```

**2. Locate and fix the malformed line.**

The Linter's output names the specific line or field. Common fixes:

- Wrap strings containing colons, brackets, or special characters in double quotes: `title: "A Study of AI: Methods"`
- Fix list indentation — each item should be two spaces in, with a hyphen: `- field-study`
- Ensure the frontmatter ends with a closing `---` on its own line
- Replace any tab characters with two spaces

**3. Save and verify in Obsidian.**

After saving the fix, Obsidian should show no error in the Properties panel. The note should appear in Dataview queries within a few seconds (Dataview re-indexes on file change).

## Verify

In Obsidian, run this Dataview query in a new note to confirm the repaired note is visible:

```dataview
FROM "catalog/papers"
WHERE file.name = "<citekey>"
```

The note should appear. Then confirm with the Linter operation:

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

No YAML or schema findings reported for this note.

## If the fix doesn't hold

If Obsidian re-introduces the error after saving, a plugin or Obsidian's Properties panel is auto-formatting the YAML. Check which plugins have "format on save" behavior and disable it for this file type. The frontend `obsidian-linter` plugin is the likely cause — it must be uninstalled, not merely excluded from folders; see [Set up Obsidian](../setup/set-up-obsidian.md).

## Related

- Why the frontend Obsidian Linter is incompatible: [Set up Obsidian](../setup/set-up-obsidian.md)
- Frontmatter schema reference: [Frontmatter fields](../../reference/frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- Related YAML-corruption pitfalls: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)
