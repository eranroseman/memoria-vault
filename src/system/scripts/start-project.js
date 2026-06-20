/*
 * QuickAdd user script — "Memoria: start project".
 *
 * Opens the Modal Forms `memoria-project-start` form and scaffolds a project
 * workspace under projects/<slug>/ with a project question note, thesis note,
 * and empty code/drafts/exports folders.
 */

const FORM_NAME = "memoria-project-start";
const { exists, normalizeList, slug, yamlString } = require("./quickadd-utils");

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const modalforms = app?.plugins?.plugins?.modalforms?.api;
  if (!modalforms?.openForm) {
    new Notice("Modal Forms API unavailable — enable the modalforms plugin first.", 8000);
    return;
  }

  let result;
  try {
    result = await modalforms.openForm(FORM_NAME);
  } catch (e) {
    new Notice(("Project start form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Project start cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.title || !data.slug || !data.scope_topics.length || !data.inquiry_population || !data.inquiry_outcome) {
    new Notice("Project title, slug, scope topics, population, and outcome are required.", 8000);
    return;
  }

  const thesisTitle = data.output_mode === "thesis"
    ? (await params.quickAddApi.inputPrompt("Provisional thesis, as one sentence:"))?.trim()
    : "";

  try {
    const projectPath = await scaffoldProject(app, data, thesisTitle || "");
    const projectFile = app.vault.getAbstractFileByPath(projectPath);
    if (projectFile) await app.workspace.getLeaf(true).openFile(projectFile);
    new Notice("✓ Project scaffolded: " + projectPath, 8000);
  } catch (e) {
    new Notice(("Project scaffold failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function scaffoldProject(app, data, thesisTitle) {
  const adapter = app.vault.adapter;
  const root = "projects/" + data.slug;
  if (await exists(adapter, root + "/project.md")) {
    throw new Error("project already exists: " + root);
  }
  await ensureFolder(app, root);
  for (const dir of ["code", "drafts", "exports"]) {
    await ensureFolder(app, root + "/" + dir);
    await adapter.write(root + "/" + dir + "/.gitkeep", "");
  }
  const today = new Date().toISOString().slice(0, 10);
  const activeThesis = data.output_mode === "thesis" ? "[[" + root + "/thesis|Thesis]]" : "";
  const projectText = [
    "---",
    "title: " + yamlString(data.title),
    "type: project",
    "lifecycle: current",
    "slug: " + yamlString(data.slug),
    "scope_topics: " + yamlList(data.scope_topics),
    "inquiry:",
    "  population: " + yamlString(data.inquiry_population),
    "  intervention: " + yamlString(data.inquiry_intervention),
    "  comparison: " + yamlString(data.inquiry_comparison),
    "  outcome: " + yamlString(data.inquiry_outcome),
    "finer:",
    "  feasible: " + yamlString(data.finer_feasible),
    "  novel: " + yamlString(data.finer_novel),
    "  relevant: " + yamlString(data.finer_relevant),
    "output_mode: " + yamlString(data.output_mode),
    "question_version: 1",
    "question_log: []",
    "active_thesis: " + yamlString(activeThesis),
    "refutation_sufficiency: false",
    "created: " + today,
    "---",
    "",
    "# Question",
    "",
    data.title,
    "",
    "# Project Gate",
    "",
    "```button",
    "name Refresh Project gate",
    "type command",
    "action QuickAdd: Memoria: refresh project gate",
    "```",
    "",
    "![[project-gate-index]]",
    "",
  ].join("\n");
  await adapter.write(root + "/project.md", projectText);

  const thesisText = [
    "---",
    "title: " + yamlString(thesisTitle || "Provisional thesis for " + data.title),
    "type: thesis",
    "lifecycle: proposed",
    "project: " + yamlString("[[" + root + "/project|" + data.slug + "]]"),
    "sources: []",
    "links:",
    "  supports: []",
    "  contradicts: []",
    "superseded_by: \"\"",
    "refutation_sufficiency: false",
    "created: " + today,
    "---",
    "",
    "# Thesis",
    "",
    thesisTitle || "State the provisional answer here.",
    "",
  ].join("\n");
  await adapter.write(root + "/thesis.md", thesisText);
  return root + "/project.md";
}

function normalizeFormData(data) {
  return {
    title: String(data.title || "").trim(),
    slug: slug(data.slug, "project"),
    scope_topics: normalizeList(data.scope_topics),
    inquiry_population: String(data.inquiry_population || "").trim(),
    inquiry_intervention: String(data.inquiry_intervention || "").trim(),
    inquiry_comparison: String(data.inquiry_comparison || "").trim(),
    inquiry_outcome: String(data.inquiry_outcome || "").trim(),
    finer_feasible: String(data.finer_feasible || "").trim(),
    finer_novel: String(data.finer_novel || "").trim(),
    finer_relevant: String(data.finer_relevant || "").trim(),
    output_mode: ["thesis", "survey"].includes(data.output_mode) ? data.output_mode : "thesis",
  };
}

async function ensureFolder(app, path) {
  const adapter = app.vault.adapter;
  if (await exists(adapter, path)) return;
  await app.vault.createFolder(path);
}

function yamlList(values) {
  return "[" + values.map(yamlString).join(", ") + "]";
}
