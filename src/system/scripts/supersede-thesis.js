/*
 * QuickAdd user script — "Memoria: supersede thesis".
 *
 * Mark-don't-invalidate pivot: create a proposed replacement thesis, point the
 * old thesis at it with `superseded_by`, update the project active thesis, and
 * raise an alert card for lazy re-confirmation of the old argument graph.
 */

const { slug, uniquePath, yamlString } = require("./quickadd-utils");

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const active = app?.workspace?.getActiveFile?.();
  if (!active || !active.path.startsWith("projects/")) {
    new Notice("Open the thesis note under projects/<slug>/ before superseding.", 8000);
    return;
  }
  const oldText = await app.vault.read(active);
  if (!/^type:\s*thesis$/m.test(oldText)) {
    new Notice("Active note is not a thesis note.", 8000);
    return;
  }

  const title = (await params.quickAddApi.inputPrompt("Replacement thesis, as one sentence:"))?.trim();
  if (!title) {
    new Notice("No replacement thesis entered.", 4000);
    return;
  }

  const today = new Date().toISOString().slice(0, 10);
  const root = active.path.split("/").slice(0, 2).join("/");
  const adapter = app.vault.adapter;
  const newPath = await uniquePath(adapter, root + "/thesis-" + slug(title, "thesis") + ".md");
  const projectPath = root + "/project.md";
  const newLink = "[[" + newPath.replace(/\.md$/, "") + "|replacement thesis]]";

  const newText = [
    "---",
    "title: " + yamlString(title),
    "type: thesis",
    "lifecycle: proposed",
    "project: " + yamlString("[[" + projectPath.replace(/\.md$/, "") + "]]"),
    "sources: []",
    "links:",
    "  supports: []",
    "  contradicts: []",
    "superseded_by: \"\"",
    "supersedes: " + yamlString("[[" + active.path.replace(/\.md$/, "") + "]]"),
    "refutation_sufficiency: false",
    "created: " + today,
    "---",
    "",
    "# Thesis",
    "",
    title,
    "",
  ].join("\n");
  await adapter.write(newPath, newText);
  await app.vault.modify(active, setFrontmatterField(oldText, "superseded_by", yamlString(newLink)));
  const projectFile = app.vault.getAbstractFileByPath(projectPath);
  if (projectFile) {
    const projectText = await app.vault.read(projectFile);
    await app.vault.modify(projectFile, setFrontmatterField(projectText, "active_thesis", yamlString(newLink)));
  }
  const cardPath = await writePivotAlert(adapter, active.path, newPath, today);
  const created = app.vault.getAbstractFileByPath(newPath);
  if (created) await app.workspace.getLeaf(true).openFile(created);
  new Notice("✓ Thesis superseded; re-confirmation alert raised: " + cardPath, 8000);
};

async function writePivotAlert(adapter, oldPath, newPath, today) {
  const path = await uniquePath(adapter, "inbox/alert-thesis-pivot-" + slug(newPath, "thesis") + ".md");
  const text = [
    "---",
    "title: " + yamlString("Re-confirm argument graph after thesis pivot"),
    "type: alert",
    "lifecycle: proposed",
    "finding: " + yamlString("The active thesis changed from " + oldPath + " to " + newPath + "."),
    "action: " + yamlString("Refresh the Project gate and re-confirm on-path/high-impact relations lazily."),
    "argument_for: " + yamlString("Pivoting re-roots impact and saturation; stale edges must not stay load-bearing silently."),
    "argument_against: " + yamlString("The old graph is preserved for audit and should be re-confirmed only as work touches it."),
    "what_tipped_it: " + yamlString("The PI intentionally superseded the thesis."),
    "certainty: confident",
    "loudness: alert",
    "target: " + yamlString(newPath),
    "created: " + today,
    "---",
    "",
    "# Action",
    "",
    "Refresh the Project gate, then re-confirm the old on-path/high-impact relations as the project continues.",
    "",
  ].join("\n");
  await adapter.write(path, text);
  return path;
}

function setFrontmatterField(text, key, renderedValue) {
  const re = new RegExp("^" + key + ":.*$", "m");
  if (re.test(text)) return text.replace(re, key + ": " + renderedValue);
  return text.replace(/^---\n/, "---\n" + key + ": " + renderedValue + "\n");
}
