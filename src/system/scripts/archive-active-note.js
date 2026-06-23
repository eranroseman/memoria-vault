/*
 * QuickAdd user script — archive the active note by configured type/folder.
 */

const { archiveActiveNote } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

const SPECS = {
  claim: { type: "claim", folder: "notes/claims/", label: "claim" },
  fleeting: { type: "fleeting", folder: "notes/fleeting/", label: "fleeting" },
};

async function entry(params, settings = {}) {
  const { Notice } = params.obsidian;
  const spec = SPECS[String(settings.Type || "").toLowerCase()];
  if (!spec) {
    new Notice("Unknown archive target: " + (settings.Type || "missing"), 8000);
    return;
  }
  await archiveActiveNote(params, spec);
}

module.exports = {
  entry,
  settings: {
    name: "Memoria: archive active note",
    author: "Memoria",
    options: {
      Type: {
        type: "text",
        defaultValue: "fleeting",
        placeholder: "fleeting | claim",
      },
    },
  },
};
