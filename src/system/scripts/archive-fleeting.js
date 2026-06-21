/*
 * QuickAdd user script — "Memoria: archive fleeting note".
 *
 * Marks the ACTIVE fleeting note done by setting lifecycle: archived. Fleeting
 * notes are raw to-do captures, so archiving is the lightweight "handled" state.
 */

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;

  const file = app.workspace.getActiveFile();
  if (!file) {
    new Notice("No active note — open the fleeting note first.", 6000);
    return;
  }
  if (!file.path.startsWith("notes/fleeting/") || !file.path.endsWith(".md")) {
    new Notice("Not a fleeting note (" + file.path + ") — only notes under notes/fleeting/ archive here.", 8000);
    return;
  }

  try {
    await app.fileManager.processFrontMatter(file, (fm) => {
      if ((fm.type || "") !== "fleeting") {
        throw new Error("Active note is not type: fleeting.");
      }
      fm.lifecycle = "archived";
      fm.archived = todayIsoDate();
    });
    new Notice("Archived fleeting note: " + file.basename, 6000);
  } catch (e) {
    new Notice(("Archive fleeting note failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};
