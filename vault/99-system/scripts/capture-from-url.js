/*
 * QuickAdd user script — "Memoria: capture source from URL".
 *
 * Prompts for a URL and creates an `intake:source` card on the Librarian lane
 * (`hermes kanban create`). The Librarian resolves the URL (DOI / identifiers)
 * during ingest. Mirrors capture-from-zotero.js: the card-create goes through
 * `bash -lc` (wrapped in wsl.exe on Windows) so it reaches hermes in WSL.
 */

module.exports = async (params) => {
  const { Notice } = params.obsidian;
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

  const url = (await params.quickAddApi.inputPrompt("Source URL to capture:"))?.trim();
  if (!url) {
    new Notice("No URL entered.", 4000);
    return;
  }
  if (!/^https?:\/\//i.test(url)) {
    new Notice("That doesn't look like a URL (expected http/https).", 6000);
    return;
  }

  const body =
    "intake:source — captured from URL. Resolve and ingest the source at " + url + " " +
    "using the obsidian-paper-note skill: fetch its metadata (DOI / identifiers), add it to the " +
    "library, create the paper-note under 20-sources/, enrich it, propose the classification, then " +
    "kanban_complete with review_status: requested.";

  new Notice("Capturing " + url + " …", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Ingest source: " + url) +
      " --assignee memoria-librarian --skill obsidian-paper-note --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Captured → intake card created on the Librarian lane.", 6000);
  } catch (e) {
    new Notice(("Capture failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
