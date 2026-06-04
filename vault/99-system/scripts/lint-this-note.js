/*
 * QuickAdd user script — "Memoria: lint this note".
 *
 * Creates a Linter card for the active note (`hermes kanban create`, assignee
 * memoria-linter). The Linter runs its checks and reports findings on the card;
 * it does not modify the note. Mirrors capture-from-zotero.js for the WSL call.
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
    new Notice("No active note to lint — open a note first.", 5000);
    return;
  }

  const body =
    "Lint the note at " + f.path + " — run the structural checks (schema, frontmatter, wikilinks). " +
    "Report findings as a card comment; do NOT modify the note.";

  new Notice("Linting " + f.basename + " …", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Lint: " + f.basename) +
      " --assignee memoria-linter --created-by quickadd --body " + shq(body)
    );
    new Notice("✓ Lint card created on the Linter lane.", 6000);
  } catch (e) {
    new Notice(("Lint failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
