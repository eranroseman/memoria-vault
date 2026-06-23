/*
 * QuickAdd user script — "Memoria: delegate task".
 *
 * Prompts for a lane and a goal, then creates a card on that lane's agent
 * (`hermes kanban create`) — the palette twin of the Co-PI's
 * `delegate_route_task`. The lane → profile mapping mirrors LANE_PROFILE in
 * `.memoria/mcp/tasks_mcp.py`. Mirrors capture-from-url.js: the card-create
 * goes through `bash -lc` so it reaches the native Hermes CLI.
 */

// Lane → assignee profile (keep in sync with LANE_PROFILE in tasks_mcp.py).
const LANES = {
  catalog: "memoria-librarian",
  extract: "memoria-librarian",
  link: "memoria-librarian",
  map: "memoria-librarian",
  draft: "memoria-writer",
  verify: "memoria-peer-reviewer",
  code: "memoria-engineer",
};

// Lane → PI-facing picker label. Keep profile ids internal; the picker should
// describe the work, not expose implementation names.
const LANE_LABELS = {
  catalog: "Catalog sources",
  extract: "Extract claims",
  link: "Link claims",
  map: "Map the corpus",
  draft: "Draft prose",
  verify: "Verify work",
  code: "Coordinate code handoff",
};
const { fnv1a, queueHermesCard } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");

  const laneNames = Object.keys(LANES);
  const lane = await params.quickAddApi.suggester(
    laneNames.map((l) => LANE_LABELS[l]),
    laneNames
  );
  if (!lane) {
    new Notice("No lane chosen.", 4000);
    return;
  }

  const goal = (await params.quickAddApi.inputPrompt("Goal for " + LANE_LABELS[lane] + ":"))?.trim();
  if (!goal) {
    new Notice("No goal entered.", 4000);
    return;
  }

  const assignee = LANES[lane];
  const body =
    "delegate:" + lane + " — delegated from the palette. " + goal + " " +
    "When done, kanban_complete with review_status: requested.";
  // Stable per lane+goal so a double-fire creates one card, not two.
  const idemKey = "quickadd-delegate-" + lane + "-" + fnv1a(lane + "\n" + goal);

  new Notice("Delegating to the " + lane + " lane…", 3000);
  try {
    await queueHermesCard(cp, { title: goal, assignee, idemKey, body });
    new Notice("✓ Delegated → " + LANE_LABELS[lane] + " card created.", 6000);
  } catch (e) {
    new Notice(("Delegation failed: " + e.message).slice(0, 250), 10000);
  }
};
