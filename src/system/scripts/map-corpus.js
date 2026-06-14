/*
 * QuickAdd user script — "Memoria: map corpus".
 *
 * Direct palette access to the map lane (#203): prompts for an optional scope
 * (a folder or hub note — Enter maps the whole corpus) and creates a
 * correctly-addressed card on the Librarian (`hermes kanban create
 * --skill map-cluster-corpus`). Mirrors delegate-task.js: the card-create
 * goes through `bash -lc` (wrapped in wsl.exe on Windows) so it reaches
 * hermes in WSL.
 */

const LANE = "map";
const ASSIGNEE = "memoria-librarian";
const SKILL = "map-cluster-corpus";

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

  const scope =
    (await params.quickAddApi.inputPrompt(
      "Scope (folder or hub note — optional, Enter for the whole corpus):"
    ))?.trim() || "";

  const body =
    "delegate:" + LANE + " — from the palette. Map the corpus" +
    (scope ? " scoped to " + scope : "") + ". " +
    "Use the " + SKILL + " skill: cluster the notes, surface dense and thin areas, stage the " +
    "report through the normal proposal path, then kanban_complete with review_status: requested.";
  // Stable per scope so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(scope || "whole-corpus");

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Map the corpus" + (scope ? ": " + scope : "")) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Map delegation failed: " + e.message).slice(0, 250), 10000);
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
