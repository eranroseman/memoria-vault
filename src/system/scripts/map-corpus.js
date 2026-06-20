/*
 * QuickAdd user script — "Memoria: map corpus".
 *
 * Direct palette access to the map lane (#203): prompts for an optional scope
 * (a folder or hub note — Enter maps the whole corpus) and creates a
 * correctly-addressed card on the Librarian (`hermes kanban create
 * --skill map-cluster-corpus`). Mirrors delegate-task.js: the card-create
 * goes through `bash -lc` so it reaches the native Hermes CLI.
 */

const LANE = "map";
const ASSIGNEE = "memoria-librarian";
const SKILL = "map-cluster-corpus";
const { fnv1a, run, shq } = require("./quickadd-utils");

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

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
    await run(cp,
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
