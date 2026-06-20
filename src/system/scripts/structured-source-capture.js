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
    const sourcePath = await writeSourceNote(app, data, cp, crypto);
    const cardPath = await writeCandidateCard(app, data, sourcePath);
    new Notice("✓ Structured source staged: " + sourcePath + " · " + cardPath, 8000);
  } catch (e) {
    new Notice(("Structured source capture failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

async function writeSourceNote(app, data, cp, crypto) {
  const adapter = app.vault.adapter;
  const path = await uniquePath(adapter, SOURCE_FOLDER + slug(data.title) + ".md");
  const today = new Date().toISOString().slice(0, 10);
  const summary = data.summary || "Your-words summary of the source — what it claims, on what evidence.";
  const similarity = await preFileSimilarityShadow(app, cp, crypto, {
    noteType: "source",
    path,
    query: data.title + "\n" + summary,
    sourcePath: "",
  });
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
    buildSimilarityCallout(similarity),
    "",
  ].join("\n");
  await adapter.write(path, frontmatter + body);
  try { await appendSimilarityTelemetry(app, similarity); } catch (e) { /* telemetry is shadow-only */ }
  return path;
}

const SIMILARITY_LOG = "system/logs/pre-file-similarity.jsonl";
const SIMILARITY_SCOPES = ["notes/claims/", "notes/sources/"];

async function preFileSimilarityShadow(app, cp, crypto, request) {
  const basePath = vaultBasePath(app);
  const row = {
    timestamp: nowIso(),
    event: "pre_file_similarity_shadow",
    source: "quickadd.structured-source-capture",
    note_type: request.noteType,
    path: request.path,
    source_path: request.sourcePath || "",
    query_sha256: sha256(crypto, request.query),
    query_chars: String(request.query || "").length,
    status: "unavailable",
    warning: "",
    neighbours: [],
  };
  if (!basePath) {
    row.warning = "vault-base-path-unavailable";
    return row;
  }
  try {
    const raw = await run(cp,
      "cd " + shq(basePath) + " && qmd search --format json --full-path -n 12 " + shq(request.query));
    row.status = "ok";
    row.neighbours = normalizeQmdResults(raw, basePath)
      .filter((item) => SIMILARITY_SCOPES.some((prefix) => item.path.startsWith(prefix)))
      .filter((item) => item.path !== request.path)
      .slice(0, 3);
    if (!row.neighbours.length) {
      row.warning = "no-scoped-neighbours";
    }
  } catch (e) {
    row.warning = "qmd-search-failed";
    row.error = String(e.message || e).slice(0, 160);
  }
  return row;
}

function buildSimilarityCallout(row) {
  const lines = [
    "> [!similarity]- Pre-file similarity shadow",
    "> Report-only qmd neighbour check; no block, auto-merge, or calibrated threshold.",
  ];
  if (row.warning) {
    lines.push("> Warning: " + row.warning + ". If this looks wrong, rebuild the qmd index.");
  }
  if (!row.neighbours.length) {
    lines.push("> - No claim/source neighbours returned.");
    return lines.join("\n");
  }
  for (const item of row.neighbours) {
    const stem = item.path.replace(/\.md$/, "");
    const label = stem.split("/").pop();
    const score = item.score === null ? "" : " — score " + Number(item.score).toFixed(3);
    lines.push("> - [[" + stem + "|" + label + "]]" + score);
  }
  return lines.join("\n");
}

async function appendSimilarityTelemetry(app, row) {
  await ensureFolder(app, "system/logs");
  const line = JSON.stringify(row) + "\n";
  const adapter = app.vault.adapter;
  let prev = "";
  try { prev = await adapter.read(SIMILARITY_LOG); } catch (e) { /* first row */ }
  await adapter.write(SIMILARITY_LOG, prev + line);
}

async function ensureFolder(app, folder) {
  const adapter = app.vault.adapter;
  const parts = folder.split("/");
  let cur = "";
  for (const part of parts) {
    cur = cur ? cur + "/" + part : part;
    if (!(await exists(adapter, cur))) {
      await app.vault.createFolder(cur);
    }
  }
}

function normalizeQmdResults(raw, basePath) {
  let data;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    return [];
  }
  const items = Array.isArray(data) ? data : (data.results || data.items || data.matches || []);
  if (!Array.isArray(items)) return [];
  return items.map((item) => {
    const rawPath = String(item.path || item.file || item.filename || item.uri || "");
    return {
      path: relativeVaultPath(rawPath, basePath),
      score: numericScore(item),
    };
  }).filter((item) => item.path);
}

function relativeVaultPath(path, basePath) {
  let p = String(path || "").replace(/^file:\/\//, "");
  if (p.startsWith("./")) p = p.slice(2);
  const base = String(basePath).replace(/\/+$/, "") + "/";
  if (p.startsWith(base)) p = p.slice(base.length);
  return p.replace(/\\/g, "/");
}

function numericScore(item) {
  for (const key of ["score", "similarity", "rrf_score", "bm25_score"]) {
    const n = Number(item[key]);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function vaultBasePath(app) {
  const adapter = app?.vault?.adapter;
  if (typeof adapter?.getBasePath === "function") return adapter.getBasePath();
  return adapter?.basePath || "";
}

function run(cp, sh) {
  return new Promise((resolve, reject) => {
    cp.execFile("bash", ["-lc", sh], { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(String(stderr || err.message || "").trim()));
      resolve(stdout);
    });
  });
}

function sha256(crypto, text) {
  return crypto.createHash("sha256").update(String(text || ""), "utf8").digest("hex");
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
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

function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
