
# How to fix broken frontmatter

Repair a YAML parse error that prevents a note from appearing in Dataview queries or triggers an error in Obsidian's Properties panel.

## Symptom

- The Obsidian Properties panel shows a YAML parse error on a note
- The note does not appear in Dataview queries that should include it
- `/lint --dry-run` reports "YAML structure issue" on this note

## Detect

Run the Linter to confirm and identify the specific error:

```bash
hermes -p memoria-linter chat -s lint
/lint --source <citekey> --dry-run
```

Common YAML errors:

| Error | Example |
| --- | --- |
| Unclosed string | `title: "Unterminated title` |
| List indentation error | `methods:` followed by `  - field-study` at wrong indent |
| Missing closing `---` delimiter | Frontmatter block never ends |
| Colon in value without quoting | `title: A Study of AI: Methods` (colon in title) |
| Tab character instead of spaces | YAML requires spaces, not tabs |

## Fix

**1. Open the raw file in an editor outside Obsidian.**

Obsidian masks the raw YAML in Properties view. Open the file in VS Code or Notepad++ to see exactly what's in the frontmatter block:

```powershell
code "vault\20-sources\01-papers\<citekey>.md"
```

**2. Locate and fix the malformed line.**

The Linter's output names the specific line or field. Common fixes:

- Wrap strings containing colons, brackets, or special characters in double quotes: `title: "A Study of AI: Methods"`
- Fix list indentation — each item should be two spaces in, with a hyphen: `  - field-study`
- Ensure the frontmatter ends with a closing `---` on its own line
- Replace any tab characters with two spaces

**3. Save and verify in Obsidian.**

After saving the fix, Obsidian should show no error in the Properties panel. The note should appear in Dataview queries within a few seconds (Dataview re-indexes on file change).

## Verify

In Obsidian, run this Dataview query in a new note to confirm the repaired note is visible:

```dataview
FROM "20-sources/01-papers"
WHERE file.name = "<citekey>"
```

The note should appear. Then confirm with the Linter:

```bash
hermes -p memoria-linter chat -s lint
/lint --source <citekey> --dry-run
```

No YAML errors reported for this note.

## If the fix doesn't hold

If Obsidian re-introduces the error after saving, a plugin or Obsidian's Properties panel is auto-formatting the YAML. Check which plugins have "format on save" behavior and disable it for this file type. The frontend Obsidian Linter plugin is the most common culprit — it is incompatible with Memoria and should be uninstalled (see [ADR-12](../../../project-files/decisions/12-obsidian-linter-reference-only.md)), not merely excluded from folders.

## Related

- Why the frontend Obsidian Linter is incompatible: [set-up-obsidian.md § Step 7](../setup/set-up-obsidian.md)
- Frontmatter schema reference: [frontmatter.md](../../reference/frontmatter.md)
- Full failure-modes catalog: [failure-modes.md](../../reference/failure-modes.md)
- Related YAML-corruption pitfalls: [common-pitfalls.md](../../explanation/knowledge/common-pitfalls.md)
