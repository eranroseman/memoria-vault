/*
 * QuickAdd user script -- "Memoria: capture note".
 *
 * Opens the Modal Forms `memoria-note-capture` form and writes one unchecked
 * note Concept under knowledge/notes/. The worker/check loop owns promotion.
 */

const FORM_NAME = "memoria-note-capture";
const NOTE_FOLDER = "knowledge/notes/";
const TEMPLATE_PATH = "system/templates/note.md";
const { exists, slug, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const modalforms = app?.plugins?.plugins?.modalforms?.api;
  if (!modalforms?.openForm) {
    new Notice("Modal Forms API unavailable; enable the modalforms plugin first.", 8000);
    return;
  }

  let result;
  try {
    result = await modalforms.openForm(FORM_NAME);
  } catch (e) {
    new Notice(("Note capture form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Note capture cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.body) {
    new Notice("Note text is required.", 6000);
    return;
  }

  try {
    const path = await writeNote(app, data);
    new Notice("Note captured: " + path, 6000);
  } catch (e) {
    new Notice(("Note capture failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function writeNote(app, data) {
  const adapter = app.vault.adapter;
  await ensureFolder(adapter, NOTE_FOLDER.replace(/\/$/, ""));
  const title = data.title || firstLineTitle(data.body);
  const path = await uniquePath(adapter, NOTE_FOLDER + slug(title, "note") + ".md");
  const template = await adapter.read(TEMPLATE_PATH);
  await adapter.write(path, renderNoteTemplate(template, title, data.description, data.body));
  return path;
}

function renderNoteTemplate(template, title, description, body) {
  return String(template)
    .replace(/["']\{\{VALUE:note title\}\}["']/g, yamlString(title))
    .replace(/\{\{VALUE:note title\}\}/g, yamlString(title))
    .replace(/["']\{\{VALUE:note description\}\}["']/g, yamlString(description || title))
    .replace(/\{\{VALUE:note description\}\}/g, yamlString(description || title))
    .replace(/\{\{VALUE:note body\}\}/g, body.trim())
    .trimEnd() + "\n";
}

function normalizeFormData(data) {
  return {
    title: String(data.title || "").trim(),
    description: String(data.description || "").trim(),
    body: String(data.body || "").trim(),
  };
}

function firstLineTitle(body) {
  const first = String(body).split(/\r?\n/).map((line) => line.trim()).find(Boolean) || "Note";
  return first.length <= 80 ? first : first.slice(0, 77) + "...";
}

async function ensureFolder(adapter, folder) {
  const parts = folder.split("/");
  let current = "";
  for (const part of parts) {
    current = current ? current + "/" + part : part;
    if (!(await exists(adapter, current))) await adapter.mkdir(current);
  }
}
