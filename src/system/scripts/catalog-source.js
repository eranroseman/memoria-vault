/*
 * QuickAdd user script — "Memoria: catalog source".
 *
 * Direct palette access to the catalog lane (#203): prompts for a citekey or
 * URL (plus an optional goal) and creates a correctly-addressed card on the
 * Librarian (`hermes kanban create --skill catalog-enrich-record`). Mirrors
 * delegate-task.js: the card-create goes through `bash -lc` so it reaches the
 * native Hermes CLI.
 */

const LANE = "catalog";
const ASSIGNEE = "memoria-librarian";
const SKILL = "catalog-enrich-record";
const { fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

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
    "library, create or enrich the paper entity under catalog/papers/, create the " +
    "proposed source-note stub under notes/sources/ for the PI to fill, propose the " +
    "classification, then kanban_complete with review_status: requested.";
  // Stable per ref+goal so a double-fire creates one card, not two.
  const idemKey = "quickadd-" + LANE + "-" + fnv1a(ref + "\n" + goal);

  new Notice("Delegating to the " + LANE + " lane…", 3000);
  try {
    await queueHermesCard(cp, {
      title: "Catalog source: " + ref,
      assignee: ASSIGNEE,
      skill: SKILL,
      idemKey,
      body,
      lane: LANE,
    });
    new Notice("✓ Card created on the " + LANE + " lane (" + ASSIGNEE + ").", 6000);
  } catch (e) {
    new Notice(("Catalog delegation failed: " + e.message).slice(0, 250), 10000);
  }
};
