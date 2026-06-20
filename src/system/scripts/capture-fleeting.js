/*
 * QuickAdd user script — "Memoria: capture fleeting".
 *
 * Opens the Modal Forms `memoria-fleeting-capture` form and writes a clean
 * fleeting note under notes/fleeting/. Capture should be frictionless: the
 * note is queued for later triage and does not steal focus by opening itself.
 */

const FORM_NAME = "memoria-fleeting-capture";
const FLEETING_FOLDER = "notes/fleeting/";
const { exists, slug, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

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
    new Notice(("Fleeting capture form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Fleeting capture cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.body) {
    new Notice("Capture text is required.", 6000);
    return;
  }

  try {
    const path = await writeFleetingNote(app, data);
    new Notice("Fleeting note captured: " + path, 6000);
  } catch (e) {
    new Notice(("Fleeting capture failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function writeFleetingNote(app, data) {
  const adapter = app.vault.adapter;
  await ensureFolder(adapter, FLEETING_FOLDER.replace(/\/$/, ""));
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const stamp = date + "-" + String(now.getHours()).padStart(2, "0") + String(now.getMinutes()).padStart(2, "0") + String(now.getSeconds()).padStart(2, "0");
  const title = data.title || firstLineTitle(data.body);
  const path = await uniquePath(adapter, FLEETING_FOLDER + stamp + "-" + slug(title, "fleeting") + ".md");
  const frontmatter = [
    "---",
    "title: " + yamlString(title),
    "type: fleeting",
    "lifecycle: proposed",
    "origin: human",
    "created: " + date,
    "---",
    "",
  ].join("\n");
  await adapter.write(path, frontmatter + data.body.trim() + "\n");
  return path;
}

function normalizeFormData(data) {
  return {
    title: String(data.title || "").trim(),
    body: String(data.body || "").trim(),
  };
}

function firstLineTitle(body) {
  const first = String(body).split(/\r?\n/).map((line) => line.trim()).find(Boolean) || "Fleeting capture";
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
