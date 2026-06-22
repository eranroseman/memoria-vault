/*
 * QuickAdd user script - "Memoria: remove sample vault".
 *
 * Archives only loaded live notes that are explicitly labeled sample: true.
 * The bundled copy under .memoria/samples is left intact.
 */

const LIVE_PREFIXES = ["catalog/", "notes/"];

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const today = new Date().toISOString().slice(0, 10);
  const sampleFiles = app.vault.getMarkdownFiles().filter((file) =>
    LIVE_PREFIXES.some((prefix) => file.path.startsWith(prefix)),
  );

  try {
    let archived = 0;
    let alreadyArchived = 0;
    for (const file of sampleFiles) {
      const text = await app.vault.read(file);
      if (!hasSampleTrue(text)) continue;
      await app.fileManager.processFrontMatter(file, (fm) => {
        if (fm.lifecycle === "archived") {
          alreadyArchived += 1;
          return;
        }
        fm.lifecycle = "archived";
        fm.archived = today;
        archived += 1;
      });
    }

    if (!archived && !alreadyArchived) {
      new Notice("No loaded sample notes found.", 6000);
      return;
    }
    new Notice(
      "Removed sample vault: " + archived + " notes archived, " + alreadyArchived + " already archived.",
      8000,
    );
  } catch (e) {
    new Notice(("Remove sample vault failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

function hasSampleTrue(text) {
  const match = text.match(/^---\n([\s\S]*?)\n---/);
  return Boolean(match && /^sample:\s*true\s*$/m.test(match[1]));
}
