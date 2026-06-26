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
const IDEMPOTENCY_WINDOW_MS = 10 * 60 * 1000;
const { fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

  let scope =
    (await params.quickAddApi.inputPrompt(
      "Scope (folder or hub note — optional, Enter for the whole corpus):"
    ))?.trim() || "";
  // ponytail: Buttons/QuickAdd can pass "\" for empty input; real scopes are paths or topics.
  if (/^\\+$/.test(scope)) scope = "";

  const body =
    "delegate:" + LANE + " — from the palette. Map the corpus" +
    (scope ? " scoped to " + scope : "") + ". " +
    "Use the " + SKILL + " skill: cluster the notes, surface dense and thin areas, stage the " +
    "report through the normal proposal path, then kanban_complete with review_status: requested. " +
    "If the corpus is too small, kanban_block with the current and required source counts instead.";
  // Window-scoped so repeated clicks collapse, but stale blocked cards do not suppress retries.
  const retryWindow = Math.floor(Date.now() / IDEMPOTENCY_WINDOW_MS);
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(scope || "whole-corpus") + "-" + retryWindow;

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await queueHermesCard(cp, {
      title: "Map corpus" + (scope ? ": " + scope : ""),
      assignee: ASSIGNEE,
      skill: SKILL,
      idemKey,
      body,
      lane: LANE,
    });
    new Notice("Map corpus queued. Watch Inbox > Activity. Needs me changes only if action is needed.", 15000);
    return true;
  } catch (e) {
    new Notice(("Map delegation failed: " + e.message).slice(0, 250), 15000);
    return false;
  }
};
