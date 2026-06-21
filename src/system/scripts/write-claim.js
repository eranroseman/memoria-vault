/*
 * QuickAdd user script — "Memoria: write claim note".
 *
 * Opens the Modal Forms `memoria-claim-capture` form and writes one standalone
 * claim note under notes/claims/. Claim notes are PI-authored review-gated
 * knowledge, so this command only runs from the interactive Obsidian surface.
 */

const FORM_NAME = "memoria-claim-capture";
const CLAIM_FOLDER = "notes/claims/";
const TEMPLATE_PATH = "system/templates/claim.md";
const { appendSimilarityTelemetry, buildSimilarityCallout, preFileSimilarityShadow } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-similarity.js"));
const { normalizeList, slug, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const crypto = require("crypto");
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
    new Notice(("Claim capture form failed: " + (e?.message || e)).slice(0, 250), 10000);
    return;
  }
  if (!result || result.status !== "ok") {
    new Notice("Claim capture cancelled.", 4000);
    return;
  }

  const data = normalizeFormData(result.data || {});
  if (!data.title || !data.claim) {
    new Notice("Claim title and statement are required.", 7000);
    return;
  }
  if (!data.sources.length) {
    new Notice("At least one source is required for a claim note.", 7000);
    return;
  }

  try {
    const created = await writeClaimNote(app, data, cp, crypto);
    await app.workspace.getLeaf(true).openFile(created);
    new Notice("Created claim note: " + created.path, 6000);
  } catch (e) {
    new Notice(("Claim capture failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function writeClaimNote(app, data, cp, crypto) {
  const adapter = app.vault.adapter;
  const path = await uniquePath(adapter, CLAIM_FOLDER + slug(data.title, "claim") + ".md");
  const today = new Date().toISOString().slice(0, 10);
  const similarity = await preFileSimilarityShadow(app, cp, crypto, {
    source: "quickadd.write-claim",
    noteType: "claim",
    path,
    query: data.claim,
    sourcePath: "",
  });
  const template = await adapter.read(TEMPLATE_PATH);
  const rendered = renderClaimTemplate(template, data, today, similarity);
  const created = await app.vault.create(path, rendered);
  try { await appendSimilarityTelemetry(app, similarity); } catch (e) { /* telemetry is shadow-only */ }
  return created;
}

function renderClaimTemplate(template, data, today, similarity) {
  return String(template)
    .replace(/title:\s*"{{VALUE:claim, one sentence}}"/, "title: " + yamlString(data.title))
    .replace(/^maturity:\s*\w+$/m, "maturity: " + data.maturity)
    .replace(/^sources:\s*\[\]$/m, yamlBlockList("sources", data.sources))
    .replace(/^topics:\s*\[\]$/m, yamlInlineList("topics", data.topics))
    .replace(/\{\{DATE:YYYY-MM-DD\}\}/g, today)
    .replace(
      /# Claim\n\n[\s\S]*?\n\n# Evidence/,
      "# Claim\n\n" + data.claim + "\n\n# Evidence"
    )
    .replace(
      /# Evidence\n\n[\s\S]*?\n\n# Connections/,
      "# Evidence\n\n" + evidenceLines(data.sources) + "\n\n" + buildSimilarityCallout(similarity) + "\n\n# Connections"
    )
    .trimEnd() + "\n";
}

function normalizeFormData(data) {
  return {
    title: String(data.title || "").trim(),
    maturity: normalizeMaturity(data.maturity),
    sources: normalizeList(data.sources).map(citekeyFromNoteRef).filter(Boolean),
    topics: normalizeList(data.topics),
    claim: String(data.claim || "").trim(),
  };
}

function normalizeMaturity(value) {
  const maturity = String(value || "seedling").trim();
  return ["seedling", "budding", "evergreen"].includes(maturity) ? maturity : "seedling";
}

function citekeyFromNoteRef(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const noAlias = text.replace(/^\[\[/, "").replace(/\]\]$/, "").split("|", 1)[0];
  const path = noAlias.replace(/\.md$/, "");
  return path.split("/").filter(Boolean).pop() || "";
}

function yamlBlockList(name, values) {
  if (!values.length) return name + ": []";
  return name + ":\n" + values.map((value) => "  - " + yamlString(value)).join("\n");
}

function yamlInlineList(name, values) {
  return name + ": [" + values.map(yamlString).join(", ") + "]";
}

function evidenceLines(sources) {
  return sources.map((source) => "- Source: [[catalog/papers/" + source + "|" + source + "]]").join("\n");
}
