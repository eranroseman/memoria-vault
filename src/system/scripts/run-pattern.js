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

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = "bash";
      const args = ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

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
    await run(
      "hermes kanban create " + shq("Run pattern: " + patternId + (ref ? " on " + ref : "")) +
      " --assignee " + ASSIGNEE + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Card created on the Librarian lane (" + patternId + ").", 6000);
  } catch (e) {
    new Notice(("Pattern run failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

// FNV-1a 32-bit hash, hex — small and dependency-free.
function fnv1a(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}
