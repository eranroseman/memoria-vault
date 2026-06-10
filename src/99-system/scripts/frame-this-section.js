/*
 * QuickAdd user script — "Memoria: frame this section".
 *
 * Creates a Writer framing card for the active draft/section (`hermes kanban
 * create`, assignee memoria-writer, skill counter-outline). The Writer produces
 * competing outlines under the project's `02-framing/`. This is the
 * card-producing lane-trigger pattern: a QuickAdd UserScript that creates a
 * card on the matching lane. Mirrors lint-this-note.js for the WSL call and
 * active-note context.
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
    new Notice("No active note — open the section/draft to frame first.", 6000);
    return;
  }

  const m = f.path.match(/^40-workbench\/([^/]+)\//);
  if (!m) {
    new Notice("Active note isn't inside a 40-workbench/<project>/ folder.", 7000);
    return;
  }
  const slug = m[1];

  const body =
    "Frame the section at " + f.path + " for project `" + slug + "`. Run the counter-outline " +
    "skill: propose 2–3 competing outlines and write them under " +
    "40-workbench/" + slug + "/02-framing/. Do NOT modify the source note.";

  new Notice("Framing " + f.basename + " …", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Frame section: " + f.basename) +
      " --assignee memoria-writer --skill counter-outline --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Framing card created on the Writer lane.", 6000);
  } catch (e) {
    new Notice(("Frame failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
