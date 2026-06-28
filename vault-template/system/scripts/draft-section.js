/*
 * QuickAdd user script — "Memoria: draft section".
 *
 * Direct palette access to the draft lane (#203): prompts for the goal (what
 * to draft, or an outline ref) and creates a correctly-addressed card on the
 * Writer (`hermes kanban create --skill draft-write-section`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` so it reaches the
 * native Hermes CLI.
 */

const LANE = "draft";
const ASSIGNEE = "memoria-writer";
const SKILL = "draft-write-section";
const { fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

  const goal = (await params.quickAddApi.inputPrompt(
    "Section to draft (goal or outline ref):"
  ))?.trim();
  if (!goal) {
    new Notice("No goal entered.", 4000);
    return;
  }

  const body =
    "delegate:" + LANE + " — from the palette. Draft a section: " + goal + " " +
    "Use the " + SKILL + " skill, bind citations to claim notes, stage the draft through the " +
    "normal proposal path, then kanban_complete with review_status: requested.";
  // Stable per goal so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(goal);

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await queueHermesCard(cp, {
      title: "Draft section: " + goal,
      assignee: ASSIGNEE,
      skill: SKILL,
      idemKey,
      body,
      lane: LANE,
    });
    new Notice("✓ Draft queued. Watch Inbox > Activity. Needs me changes only if action is needed.", 15000);
  } catch (e) {
    new Notice(("Draft delegation failed: " + e.message).slice(0, 250), 10000);
  }
};
