/*
 * QuickAdd user script — "Memoria: extract claims".
 *
 * Direct palette access to the extract lane (#203): defaults to the active
 * note when it is a source (under catalog/papers/ or notes/sources/),
 * otherwise prompts for a source note path or citekey, then creates a
 * correctly-addressed card on the Librarian (`hermes kanban create
 * --skill extract-stub-claim`). Mirrors delegate-task.js: the card-create
 * goes through `bash -lc` so it reaches the native Hermes CLI.
 */

const LANE = "extract";
const ASSIGNEE = "memoria-librarian";
const SKILL = "extract-stub-claim";
const SOURCE_PREFIXES = ["catalog/papers/", "notes/sources/"];
const { fnv1a, run, shq } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

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
    await run(cp,
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
