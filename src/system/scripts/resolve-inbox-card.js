/*
 * QuickAdd user script — "Memoria: resolve inbox card".
 *
 * Resolves the ACTIVE inbox card in place: prompts for a verdict, flips the
 * frontmatter `lifecycle:` to the chosen value and stamps `resolved:` with
 * today's date. Pure Obsidian app API (processFrontMatter) — no shelling, so
 * it works identically on every platform.
 */

// Verdict label → lifecycle value written to the card.
const VERDICTS = {
  "current (accept)": "current",
  "retracted (reject)": "retracted",
  "archived": "archived",
};

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;

  const file = app.workspace.getActiveFile();
  if (!file) {
    new Notice("No active note — open the inbox card first.", 6000);
    return;
  }
  if (!file.path.startsWith("inbox/")) {
    new Notice("Not an inbox card (" + file.path + ") — only notes under inbox/ resolve here.", 8000);
    return;
  }

  const labels = Object.keys(VERDICTS);
  const verdict = await params.quickAddApi.suggester(labels, labels);
  if (!verdict) {
    new Notice("No verdict chosen.", 4000);
    return;
  }

  const lifecycle = VERDICTS[verdict];
  const today = new Date().toISOString().slice(0, 10);
  try {
    await app.fileManager.processFrontMatter(file, (fm) => {
      fm.lifecycle = lifecycle;
      fm.resolved = today;
    });
    new Notice("✓ Resolved " + file.basename + " → lifecycle: " + lifecycle + ", resolved: " + today + ".", 6000);
  } catch (e) {
    new Notice(("Resolve failed: " + e.message).slice(0, 250), 10000);
  }
};
