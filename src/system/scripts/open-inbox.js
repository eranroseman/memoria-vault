/*
 * QuickAdd user script - "Memoria: open Inbox".
 *
 * Opens the daily Inbox space in the current pane. Used by generated Inbox-card
 * buttons that should navigate without changing the active card lifecycle.
 */

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const inbox = app.vault.getAbstractFileByPath("spaces/inbox.md");
  if (!inbox) {
    new Notice("Inbox note not found: spaces/inbox.md", 6000);
    return;
  }
  await app.workspace.getLeaf(false).openFile(inbox);
};
