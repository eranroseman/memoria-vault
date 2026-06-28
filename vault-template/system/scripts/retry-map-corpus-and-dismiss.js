/*
 * QuickAdd user script - "Memoria: retry map corpus and dismiss".
 *
 * Retries Map corpus from an open Inbox ticket, then archives that ticket and
 * returns the pane to Inbox after the queue request succeeds.
 */

const path = require("path");

module.exports = async (params) => {
  const basePath = globalThis.app.vault.adapter.getBasePath();
  const mapCorpus = require(path.join(basePath, "system/scripts/map-corpus.js"));
  const resolver = require(path.join(basePath, "system/scripts/resolve-inbox-card.js"));

  const queued = await mapCorpus(params);
  if (!queued) return;
  await resolver.entry(params, { Outcome: "Dismiss" });
};
