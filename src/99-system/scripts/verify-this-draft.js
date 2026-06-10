/*
 * QuickAdd user script — "Memoria: verify this draft".
 *
 * Creates a Verifier card for the active draft (`hermes kanban create`,
 * assignee memoria-verifier, skill claim-trace). The Verifier runs its checks
 * and writes a verification report under the project's `05-verification/`; it
 * never edits the draft. This is the card-producing lane-trigger pattern: a
 * QuickAdd UserScript that creates a card on the matching lane. Mirrors
 * lint-this-note.js for the WSL call and active-note context.
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
    new Notice("No active note — open the draft to verify first.", 6000);
    return;
  }

  const m = f.path.match(/^40-workbench\/([^/]+)\//);
  if (!m) {
    new Notice("Active note isn't inside a 40-workbench/<project>/ folder.", 7000);
    return;
  }
  const slug = m[1];

  const body =
    "Verify the draft at " + f.path + " for project `" + slug + "`. Run the verification " +
    "sub-checks (citation, claim-trace, duplicate, retraction, paper-note completeness) and " +
    "write a verification report to 40-workbench/" + slug + "/05-verification/. " +
    "Do NOT edit the draft; spawn gap cards for failed claim-traces.";

  new Notice("Verifying " + f.basename + " …", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Verify draft: " + f.basename) +
      " --assignee memoria-verifier --skill claim-trace --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Verification card created on the Verifier lane.", 6000);
  } catch (e) {
    new Notice(("Verify failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
