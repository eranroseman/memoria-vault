/*
 * QuickAdd user script — "Memoria: start project".
 *
 * Opens the Modal Forms `memoria-project-start` form and scaffolds a project workspace under
 * projects/<slug>/ with a project question note, thesis note, and empty code/drafts/exports folders.
 */

const FORM_NAME = "memoria-project-start";
const { exists, normalizeList, slug, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

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
    result = await modalforms.openForm(FORM_NAME, { values: { output_mode: "thesis" } });
  } catch (e) {
    new Notice(("Project start form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Project start cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.title) {
    new Notice("Project title is required.", 8000);
    return;
  }
  if (data.output_mode === "thesis" && !data.provisional_thesis) {
    new Notice("Provisional thesis is required for thesis-mode projects.", 8000);
    return;
  }

  try {
    const projectPath = await scaffoldProject(app, data);
    const projectFile = app.vault.getAbstractFileByPath(projectPath);
    if (projectFile) await app.workspace.getLeaf(true).openFile(projectFile);
    new Notice("✓ Project scaffolded: " + projectPath, 8000);
  } catch (e) {
    new Notice(("Project scaffold failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function scaffoldProject(app, data) {
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
    "  interesting: " + yamlString(data.finer_interesting),
    "  novel: " + yamlString(data.finer_novel),
    "  ethical: " + yamlString(data.finer_ethical),
    "  relevant: " + yamlString(data.finer_relevant),
    "output_mode: " + yamlString(data.output_mode),
    "question_version: 1",
    "question_log: []",
    "active_thesis: " + yamlString(activeThesis),
    "refutation_sufficiency: false",
    "created: " + today,
    "---",
    "",
    "# " + data.title,
    "",
    "Project · " + (data.output_mode === "thesis" ? "Thesis mode" : "Survey mode") + (activeThesis ? " · " + activeThesis : ""),
    "",
    "## Project gate",
    "",
    "> [!brief] Cold start",
    "> No readiness data yet. Map the corpus, relate claims to the active thesis with `supports` / `contradicts`, then refresh the gate.",
    ">",
    "> [[project-gate-index|Readiness details]]",
    "",
    "```button",
    "name Map corpus",
    "type command",
    "action QuickAdd: Memoria: map corpus",
    "```",
    "",
    "```button",
    "name Refresh gate",
    "type command",
    "action QuickAdd: Memoria: refresh project gate",
    "```",
    "",
  ].join("\n");
  await adapter.write(root + "/project.md", projectText);

  // Placeholder gate index so the project page's embed isn't blank before the
  // first deterministic refresh. The structural-impact Operation overwrites this
  // whole file; it has no JSON payload block, so it reads as "no previous".
  const gateText = [
    "---",
    "title: " + yamlString("Project gate index: " + data.slug),
    "generated_by: memoria-start-project",
    "project: " + yamlString(root + "/project.md"),
    "active_thesis: " + yamlString(activeThesis),
    "argument_stage: cold-start",
    "evidence_saturation: unknown",
    "relation_count: 0",
    "open_high_impact_gaps: 0",
    "stale: true",
    "---",
    "",
    "# Project gate index: " + data.slug,
    "",
    "> [!brief] Cold start — no readiness data yet.",
    "> Relate claims to this project's thesis with `supports` / `contradicts` links, then run **Memoria: refresh project gate** from the project page to populate maturity, evidence saturation, and open gaps.",
    "",
  ].join("\n");
  await adapter.write(root + "/project-gate-index.md", gateText);

  const thesisText = [
    "---",
    "title: " + yamlString(data.provisional_thesis || "Provisional thesis for " + data.title),
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
    data.provisional_thesis || "State the provisional answer here.",
    "",
  ].join("\n");
  await adapter.write(root + "/thesis.md", thesisText);
  return root + "/project.md";
}

function normalizeFormData(data) {
  const outputMode = ["thesis", "survey"].includes(data.output_mode) ? data.output_mode : "thesis";
  const provisionalThesis =
    outputMode === "thesis" ? String(data.provisional_thesis || "").trim() : "";
  return {
    title: String(data.title || "").trim(),
    slug: slug(data.slug || data.title, "project"),
    scope_topics: normalizeList(data.scope_topics),
    inquiry_population: String(data.inquiry_population || "").trim(),
    inquiry_intervention: String(data.inquiry_intervention || "").trim(),
    inquiry_comparison: String(data.inquiry_comparison || "").trim(),
    inquiry_outcome: String(data.inquiry_outcome || "").trim(),
    finer_feasible: String(data.finer_feasible || "").trim(),
    finer_interesting: String(data.finer_interesting || "").trim(),
    finer_novel: String(data.finer_novel || "").trim(),
    finer_ethical: String(data.finer_ethical || "").trim(),
    finer_relevant: String(data.finer_relevant || "").trim(),
    output_mode: outputMode,
    provisional_thesis: provisionalThesis,
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
