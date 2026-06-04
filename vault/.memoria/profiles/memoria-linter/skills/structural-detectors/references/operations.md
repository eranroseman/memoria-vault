# Operations: safe fixes and log rotation

The Linter's two write-side procedures. Both stay inside the granted auto-fix classes
(`safe-and-unambiguous`, `authorized-targeted`) defined in `SOUL.md`; everything else is
report-only. When in doubt, dry-run.

## Implementing safe-and-unambiguous fixes via Templater

For in-vault structural repairs, prefer a Templater script over a Hermes-side write whenever
the fix is local to a single note. This runs inside Obsidian, uses
`app.fileManager.processFrontMatter()` (which races safely with Obsidian's save cycle), and
stays inside the safe-and-unambiguous class by construction.

```javascript
<%*
// Normalize frontmatter on the active note. Safe-and-unambiguous only.
tp.hooks.on_all_templates_executed(async () => {
  const file = app.workspace.getActiveFile();
  if (!file) return;

  await app.fileManager.processFrontMatter(file, (fm) => {
    // Fill required keys without overwriting existing values.
    if (!fm.type) fm.type = "note";
    if (!fm.created) fm.created = tp.date.now("YYYY-MM-DDTHH:mm:ssZ");

    // Touch updated on every run.
    fm.updated = tp.date.now("YYYY-MM-DDTHH:mm:ssZ");

    // Coerce tags to a deduplicated list. Coerce, never invent.
    if (typeof fm.tags === "string") fm.tags = [fm.tags];
    if (Array.isArray(fm.tags)) fm.tags = [...new Set(fm.tags)];
  });
});
%>
```

Rules for what this script may do:

- **Add missing keys with defaults.** Only keys defined as required in the authoritative schema.
- **Coerce types.** String → list when the schema expects a list. Never the reverse (don't collapse lists).
- **Deduplicate list values.** Tags, aliases, links.
- **Touch `updated`.**

Rules for what it must not do:

- **Never overwrite a non-empty value.** That's a schema/content change — `Report only`.
- **Never set `type` if one is already present.** That's also `Report only`.
- **Never delete keys.** Removal is `authorized-targeted` at best.

This script is the implementation of the safe-and-unambiguous row in the auto-fix table. The
`authorized-targeted` row (e.g., "fix dangling backlinks under `20-sources/03-entities/01-people/`")
needs scoped, one-off scripts written per request — there's no general template.

## Log rotation

You own rotation of operational logs under `99-system/logs/`. The policy MCP audit log grows
append-only and must not be allowed to balloon.

| Log | Cadence | Rotation target |
| --- | --- | --- |
| `audit.jsonl` (policy MCP decisions) | Weekly | `99-system/logs/archive/audit-YYYY-WW.jsonl` |
| Lint reports | On creation, no rotation | Stay in `99-system/logs/` until archived per-project |

Procedure for `audit.jsonl`:

1. At the start of each ISO week, rename the current `audit.jsonl` to `99-system/logs/archive/audit-YYYY-WW.jsonl` (where `YYYY-WW` is the previous ISO week).
2. Create a new empty `audit.jsonl`.
3. Append one bootstrap event marking the rotation, so the file is never zero-byte.

This action is classed as **`authorized-targeted`** in the auto-fix table — scoped, explicit,
and reversible — so the policy MCP allows it without escalation. The rotation event itself is
logged to the new `audit.jsonl`, which makes the rotation visible in the audit-log dashboard.
