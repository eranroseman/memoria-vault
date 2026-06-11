/*
 * QuickAdd user script — "Memoria: verify a draft".
 *
 * Direct palette access to the verify lane (#203): defaults to the active
 * note when it is a draft (under projects/), otherwise prompts for the draft
 * path, then creates a correctly-addressed card on the Peer-reviewer
 * (`hermes kanban create --skill verify-check-citation`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` (wrapped in
 * wsl.exe on Windows) so it reaches hermes in WSL.
 */

const LANE = "verify";
const ASSIGNEE = "memoria-peer-reviewer";
const SKILL = "verify-check-citation";
const DRAFT_PREFIX = "projects/";

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

  // The active note is the draft when it lives under projects/.
  const active = params.app.workspace.getActiveFile();
  let ref = active && active.path.startsWith(DRAFT_PREFIX) ? active.path : "";
  if (!ref) {
    ref = (await params.quickAddApi.inputPrompt("Draft path to verify:"))?.trim();
  }
  if (!ref) {
    new Notice("No draft given.", 4000);
    return;
  }

  const body =
    "delegate:" + LANE + " — from the palette. Verify the draft " + ref + ". " +
    "Use the " + SKILL + " skill: trace every substantive claim back to its claim note or " +
    "citekey, report traced and untraced claims, then kanban_complete with " +
    "review_status: requested.";
  // Stable per draft so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref);

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Verify draft: " + ref) +
      " --assignee " + ASSIGNEE + " --skill " + SKILL + " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Verify delegation failed: " + e.message).slice(0, 250), 10000);
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
