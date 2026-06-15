/*
 * QuickAdd user script — "Memoria: extract claims".
 *
 * Direct palette access to the extract lane (#203): defaults to the active
 * note when it is a source (under catalog/papers/ or notes/sources/),
 * otherwise prompts for a source note path or citekey, then creates a
 * correctly-addressed card on the Librarian (`hermes kanban create
 * --skill extract-stub-claim`). Mirrors delegate-task.js: the card-create
 * goes through `bash -lc` (wrapped in wsl.exe on Windows) so it reaches
 * hermes in WSL.
 */

const LANE = "extract";
const ASSIGNEE = "memoria-librarian";
const SKILL = "extract-stub-claim";
const SOURCE_PREFIXES = ["catalog/papers/", "notes/sources/"];

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

  // The active note is the source when it lives in a source folder.
  const active = params.app.workspace.getActiveFile();
  let ref = active && SOURCE_PREFIXES.some((p) => active.path.startsWith(p)) ? active.path : "";
  if (!ref) {
    ref = (await params.quickAddApi.inputPrompt("Source note path or citekey to extract claims from:"))?.trim();
  }
  if (!ref) {
    new Notice("No source given.", 4000);
    return;
  }

  const body =
    "delegate:" + LANE + " — from the palette. Extract claim stubs from the source " + ref + ". " +
    "Use the " + SKILL + " skill, stage the stubs through the normal proposal path, then " +
    "kanban_complete with review_status: requested.";
  // Stable per source so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref);

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Extract claims: " + ref) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Extract delegation failed: " + e.message).slice(0, 250), 10000);
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
