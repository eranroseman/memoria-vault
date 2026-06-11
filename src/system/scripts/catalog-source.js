/*
 * QuickAdd user script — "Memoria: catalog a source".
 *
 * Direct palette access to the catalog lane (#203): prompts for a citekey or
 * URL (plus an optional goal) and creates a correctly-addressed card on the
 * Librarian (`hermes kanban create --skill catalog-enrich-record`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` (wrapped in
 * wsl.exe on Windows) so it reaches hermes in WSL.
 */

const LANE = "catalog";
const ASSIGNEE = "memoria-librarian";
const SKILL = "catalog-enrich-record";

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

  const ref = (await params.quickAddApi.inputPrompt("Citekey or URL of the source to catalog:"))?.trim();
  if (!ref) {
    new Notice("No citekey or URL entered.", 4000);
    return;
  }
  const goal = (await params.quickAddApi.inputPrompt("Goal (optional — Enter to skip):"))?.trim() || "";

  const body =
    "delegate:" + LANE + " — from the palette. Catalog the source " + ref + ". " +
    (goal ? goal + " " : "") +
    "Use the " + SKILL + " skill: fetch its metadata (DOI / identifiers), add it to the " +
    "library, create or enrich the paper entity under catalog/papers/, propose the " +
    "classification, then kanban_complete with review_status: requested.";
  // Stable per ref+goal so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref + "\n" + goal);

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Catalog source: " + ref) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Catalog delegation failed: " + e.message).slice(0, 250), 10000);
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
