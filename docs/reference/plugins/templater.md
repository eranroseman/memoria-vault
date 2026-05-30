---
topic: plugins
---

# templater-obsidian

> Renamed to [templater-obsidian.md](templater-obsidian.md). This file is kept for link stability.

Templater is the templating layer Memoria uses for safe-and-unambiguous frontmatter fixes (see [linter.md](../../explanation/profiles/linter.md#implementing-safe-and-unambiguous-fixes-via-templater)) and for capture commands invoked via [quickadd](quickadd.md).

Load-bearing settings:

- `templates_folder: "00-meta/03-templates"` — must match the standard templates location in [vault/README.md](../../explanation/vault/README.md). Memoria uses numbered subfolders consistently throughout the vault (`00-meta/01-dashboards`, `00-meta/02-logs`, `00-meta/03-templates`, `00-meta/04-reference`); diverging just for the templates folder breaks the convention. Note: research-wiki uses `00-meta/templates` because research-wiki's schema doesn't number `00-meta`'s children — different vault, different convention.
- `trigger_on_file_creation: false` — **Memoria default is off**, not on. Setting this to `true` causes Templater to fire on every newly created file, including files agents create through the policy MCP. Since agents already populate frontmatter through their own templates (e.g., the Librarian uses [obsidian-citation-plugin](obsidian-citation-plugin.md)'s `literatureNoteContentTemplate`), auto-triggering Templater on top of agent writes either races with or overwrites the agent's frontmatter. Keep it off; humans invoke templates explicitly via the command palette (`Cmd-P → Templater: Insert template`) on the rare files they create by hand.
- `enable_system_commands: false` — keep system commands off unless there's a specific need; the Memoria Linter's `safe-and-unambiguous` Templater scripts don't need them.

Inline `data.json`:

```json
{
  "templates_folder": "00-meta/03-templates",
  "auto_jump_to_cursor": true,
  "enable_system_commands": false,
  "trigger_on_file_creation": false,
  "enable_folder_templates": false,
  "syntax_highlighting": true,
  "enabled_templates_hotkeys": [],
  "startup_templates": []
}
```
