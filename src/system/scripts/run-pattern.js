/*
 * QuickAdd user script — "Memoria: run pattern".
 *
 * Suggester over the runnable patterns in system/patterns/ (type: pattern,
 * lifecycle: current — read from Obsidian's metadata cache, no file I/O),
 * then creates a Librarian card instructing a `patterns_run` invocation
 * (ADR-53: the patterns MCP is the single audited runner) with the chosen
 * pattern id and the active note as input_ref. Mirrors delegate-task.js:
 * the card-create goes through `bash -lc` so it reaches the native Hermes CLI.
 */

const ASSIGNEE = "memoria-librarian";
const PATTERNS_DIR = "system/patterns/";
const { fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

  // Runnable patterns: *.md under system/patterns/, not an _ file, frontmatter
  // type: pattern + lifecycle: current (mirrors patterns_mcp.list_patterns).
  const patterns = params.app.vault
    .getMarkdownFiles()
    .filter((f) => f.path.startsWith(PATTERNS_DIR) && !f.name.startsWith("_"))
    .filter((f) => {
      const fm = params.app.metadataCache.getFileCache(f)?.frontmatter || {};
      return fm.type === "pattern" && fm.lifecycle === "current";
    })
    .sort((a, b) => a.basename.localeCompare(b.basename));
  if (!patterns.length) {
    new Notice("No runnable patterns found under " + PATTERNS_DIR, 6000);
    return;
  }

  const display = patterns.map((f) => {
    const fm = params.app.metadataCache.getFileCache(f)?.frontmatter || {};
    return (fm.title || f.basename) + " (" + f.basename + ")";
  });
  const patternId = await params.quickAddApi.suggester(display, patterns.map((f) => f.basename));
  if (!patternId) {
    new Notice("No pattern chosen.", 4000);
    return;
  }

  const active = params.app.workspace.getActiveFile();
  const ref = active ? active.path : "";

  const body =
    "pattern:run — from the palette. Call patterns_run with pattern_id: " + patternId +
    (ref ? " and input_ref: " + ref + " (load that note as the input)" : "") + ". " +
    "Execute the composed prompt, write the result to the returned output_target " +
    "(a dry-run result is reported, not written), then kanban_complete with " +
    "review_status: requested.";
  // Stable per pattern+ref so a double-fire creates one card, not two.
  const idemKey = "quickadd-pattern-" + patternId + "-" + fnv1a(patternId + "\n" + ref);

  new Notice("Queuing pattern " + patternId + "…", 3000);
  try {
    await queueHermesCard(cp, {
      title: "Run pattern: " + patternId + (ref ? " on " + ref : ""),
      assignee: ASSIGNEE,
      idemKey,
      body,
    });
    new Notice("✓ Pattern queued. Watch Inbox > Activity. Needs me changes only if action is needed.", 15000);
  } catch (e) {
    new Notice(("Pattern run failed: " + e.message).slice(0, 250), 10000);
  }
};
