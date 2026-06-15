/*
 * QuickAdd user script — "Memoria: structured source capture".
 *
 * Opens the Modal Forms `memoria-source-capture` form and writes a schema-shaped
 * `source` note at lifecycle: proposed under notes/sources/. The note itself is
 * staging (not a canonical claim/hub write), and a visible Inbox candidate card
 * is raised so the PI can keep/archive the capture from the normal queue.
 */

const FORM_NAME = "memoria-source-capture";
const SOURCE_FOLDER = "notes/sources/";

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
    new Notice(("Structured source form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Structured source capture cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.title || !data.entity) {
    new Notice("Source title and catalog entity are required.", 7000);
    return;
  }

  try {
    const sourcePath = await writeSourceNote(app, data);
    const cardPath = await writeCandidateCard(app, data, sourcePath);
    new Notice("✓ Structured source staged: " + sourcePath + " · " + cardPath, 8000);
  } catch (e) {
    new Notice(("Structured source capture failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function writeSourceNote(app, data) {
  const adapter = app.vault.adapter;
  const path = await uniquePath(adapter, SOURCE_FOLDER + slug(data.title) + ".md");
  const today = new Date().toISOString().slice(0, 10);
  const summary = data.summary || "Your-words summary of the source — what it claims, on what evidence.";
  const frontmatter = [
    "---",
    "title: " + yamlString(data.title),
    "type: source",
    "lifecycle: proposed",
    "entity: " + yamlString(normalizeEntity(data.entity)),
    "source_type: " + yamlString(data.source_type || "paper"),
    "research_area: " + yamlList(data.research_area),
    "methodology: " + yamlList(data.methodology),
    "links: {}",
    "created: " + today,
    "---",
    "",
  ].join("\n");
  const body = [
    "# In my words",
    "",
    summary,
    "",
    "# Worth distilling",
    "",
    "```button",
    "name Create linked claim",
    "type command",
    "action QuickAdd: Memoria: create linked claim note",
    "```",
    "",
    "Candidate claims to extract — each becomes an atomic claim note when you distill.",
    "",
    "# Tensions",
    "",
    "Where it disagrees with what the vault already holds.",
    "",
  ].join("\n");
  await adapter.write(path, frontmatter + body);
  return path;
}

async function writeCandidateCard(app, data, sourcePath) {
  const adapter = app.vault.adapter;
  const title = "Review structured source: " + data.title;
  const action = "Review staged source note " + sourcePath;
  const argumentFor = "The PI completed the structured source capture form with schema-valid metadata.";
  const argumentAgainst = "The source has not yet been read or enriched, so relevance and quality still need review.";
  const whatTippedIt = "Structured PI input is enough to stage the source note and queue a lightweight keep/archive decision.";
  const path = await uniquePath(adapter, "inbox/candidate-structured-source-" + slug(data.title) + ".md");
  const today = new Date().toISOString().slice(0, 10);
  const frontmatter = [
    "---",
    "title: " + yamlString(title),
    "type: candidate",
    "lifecycle: proposed",
    "action: " + yamlString(action),
    "argument_for: " + yamlString(argumentFor),
    "argument_against: " + yamlString(argumentAgainst),
    "what_tipped_it: " + yamlString(whatTippedIt),
    "certainty: likely",
    "target: " + yamlString(sourcePath),
    "raised_by: modalforms",
    "loudness: notice",
    "created: " + today,
    "---",
    "",
  ].join("\n");
  const body = [
    "# Action",
    "",
    action,
    "",
    "# For",
    "",
    argumentFor,
    "",
    "# Against",
    "",
    argumentAgainst,
    "",
    "# What tipped it",
    "",
    whatTippedIt,
    "",
  ].join("\n");
  await adapter.write(path, frontmatter + body);
  return path;
}

function normalizeFormData(data) {
  return {
    title: String(data.title || "").trim(),
    entity: String(data.entity || "").trim(),
    source_type: String(data.source_type || "paper").trim(),
    research_area: normalizeList(data.research_area),
    methodology: normalizeList(data.methodology),
    summary: String(data.summary || "").trim(),
  };
}

function normalizeList(value) {
  if (Array.isArray(value)) return value.map((v) => String(v).trim()).filter(Boolean);
  if (typeof value === "string" && value.trim()) return value.split(",").map((v) => v.trim()).filter(Boolean);
  return [];
}

function normalizeEntity(entity) {
  const trimmed = String(entity).trim();
  if (/^\[\[.*\]\]$/.test(trimmed)) return trimmed;
  return "[[" + trimmed.replace(/^\[\[|\]\]$/g, "") + "]]";
}

async function uniquePath(adapter, firstPath) {
  const dot = firstPath.lastIndexOf(".");
  const base = dot === -1 ? firstPath : firstPath.slice(0, dot);
  const ext = dot === -1 ? "" : firstPath.slice(dot);
  let path = firstPath;
  for (let i = 2; await exists(adapter, path); i += 1) {
    path = base + "-" + i + ext;
  }
  return path;
}

async function exists(adapter, path) {
  if (typeof adapter.exists === "function") return adapter.exists(path);
  try {
    await adapter.read(path);
    return true;
  } catch (e) {
    return false;
  }
}

function slug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "source";
}

function yamlString(s) {
  return "\"" + String(s).replace(/\\/g, "\\\\").replace(/"/g, "\\\"") + "\"";
}

function yamlList(values) {
  return "[" + values.map(yamlString).join(", ") + "]";
}
