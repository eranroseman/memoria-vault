/*
 * QuickAdd user script — "Memoria: scope this project".
 *
 * Creates a Mapper scope card for the active project (`hermes kanban create`,
 * assignee memoria-mapper, skill scope-project). The Mapper writes a
 * `corpus-map.md` under the project's `01-map/`. This is the card-producing
 * lane-trigger pattern: a QuickAdd UserScript that creates a card on the
 * matching lane. Mirrors lint-this-note.js for the WSL call and active-note
 * context.
 */

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const cp = require("child_process");
  const onWindows = process.platform === "win32";

  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = onWindows ? "wsl.exe" : "bash";
      const args = onWindows ? ["bash", "-lc", sh] : ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

  const f = app.workspace.getActiveFile();
  if (!f) {
    new Notice("No active note — open the project's README (or any note in it) first.", 6000);
    return;
  }

  // Derive the project from the active note's path: 40-workbench/<slug>/…
  const m = f.path.match(/^40-workbench\/([^/]+)\//);
  if (!m) {
    new Notice("Active note isn't inside a 40-workbench/<project>/ folder.", 7000);
    return;
  }
  const slug = m[1];

  const body =
    "Scope the writing project `" + slug + "`. Run the scope-project skill: search the vault " +
    "for claim notes and source notes relevant to the project, then write a corpus map to " +
    "40-workbench/" + slug + "/01-map/corpus-map.md summarizing what's present and what's missing.";

  new Notice("Scoping " + slug + " …", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Scope project: " + slug) +
      " --assignee memoria-mapper --skill scope-project --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Scope card created on the Mapper lane.", 6000);
  } catch (e) {
    new Notice(("Scope failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
