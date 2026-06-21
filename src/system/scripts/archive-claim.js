/*
 * QuickAdd user script — "Memoria: archive claim note".
 *
 * Marks the ACTIVE claim note archived. Claims live in a review-gated home, so
 * this command is deliberately narrow: active notes/claims/*.md files only.
 */

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;

  const file = app.workspace.getActiveFile();
  if (!file) {
    new Notice("No active note — open the claim note first.", 6000);
    return;
  }
  if (!file.path.startsWith("notes/claims/") || !file.path.endsWith(".md")) {
    new Notice("Not a claim note (" + file.path + ") — only notes under notes/claims/ archive here.", 8000);
    return;
  }

  try {
    await app.fileManager.processFrontMatter(file, (fm) => {
      if ((fm.type || "") !== "claim") {
        throw new Error("Active note is not type: claim.");
      }
      fm.lifecycle = "archived";
      fm.archived = todayIsoDate();
    });
    new Notice("Archived claim note: " + file.basename, 6000);
  } catch (e) {
    new Notice(("Archive claim note failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};
