/*
 * Report-only qmd neighbour check used before QuickAdd creates new source/claim
 * files. It never blocks creation; it only writes a telemetry row and renders a
 * callout so the PI can notice likely duplicates.
 */

const { exists, run, shq } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

const SIMILARITY_LOG = "system/logs/pre-file-similarity.jsonl";
const SIMILARITY_SCOPES = ["notes/claims/", "notes/sources/"];

async function preFileSimilarityShadow(app, cp, crypto, request) {
  const basePath = vaultBasePath(app);
  const row = {
    timestamp: nowIso(),
    event: "pre_file_similarity_shadow",
    source: request.source || "quickadd",
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

function sha256(crypto, text) {
  return crypto.createHash("sha256").update(String(text || ""), "utf8").digest("hex");
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

module.exports = {
  appendSimilarityTelemetry,
  buildSimilarityCallout,
  preFileSimilarityShadow,
};
