/*
 * QuickAdd user script — "Memoria: create linked claim note".
 *
 * From an active source note, create a schema-shaped claim note, link it back to
 * the source citekey in frontmatter, append the claim link under Worth distilling,
 * and open the new claim for the PI to edit.
 */

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const crypto = require("crypto");
  const app = params.app || globalThis.app;
  const source = app?.workspace?.getActiveFile?.();
  if (!source || !source.path.startsWith("notes/sources/")) {
    new Notice("Open a source note in notes/sources/ before creating a linked claim.", 7000);
    return;
  }

  const claim = (await params.quickAddApi.inputPrompt("Claim, as one sentence:"))?.trim();
  if (!claim) {
    new Notice("No claim entered.", 4000);
    return;
  }

  const adapter = app.vault.adapter;
  const sourceText = await adapter.read(source.path);
  if (!/^type:\s*source$/m.test(sourceText)) {
    new Notice("Active note is not a source note.", 7000);
    return;
  }

  const sourceKey = source.basename;
  const claimPath = await uniquePath(adapter, "notes/claims/" + slug(claim) + ".md");
  const claimLink = "[[" + claimPath.replace(/\.md$/, "") + "|" + claim + "]]";
  const today = new Date().toISOString().slice(0, 10);
  const similarity = await preFileSimilarityShadow(app, cp, crypto, {
    noteType: "claim",
    path: claimPath,
    query: claim,
    sourcePath: source.path,
  });

  const frontmatter = [
    "---",
    "title: " + yamlString(claim),
    "type: claim",
    "schema_version: 2",
    "lifecycle: current",
    "maturity: seedling",
    "sources:",
    "  - " + yamlString(sourceKey),
    "topics: []",
    "links:",
    "  supports: []",
    "  contradicts: []",
    "superseded_by: \"\"",
    "created: " + today,
    "---",
    "",
  ].join("\n");
  const body = [
    "# Claim",
    "",
    claim,
    "",
    "# Evidence",
    "",
    "- Source: [[" + source.path.replace(/\.md$/, "") + "|" + sourceKey + "]]",
    "",
    "# Connections",
    "",
    "Typed links (`supports` / `contradicts`) are confirmed at the link gate.",
    "",
    buildSimilarityCallout(similarity),
    "",
  ].join("\n");

  const created = await app.vault.create(claimPath, frontmatter + body);
  try { await appendSimilarityTelemetry(app, similarity); } catch (e) { /* telemetry is shadow-only */ }
  await app.vault.modify(source, appendWorthDistillingLink(sourceText, claimLink));
  await app.workspace.getLeaf(true).openFile(created);
  new Notice("Created linked claim: " + claimPath, 6000);
};

const SIMILARITY_LOG = "system/logs/pre-file-similarity.jsonl";
const SIMILARITY_SCOPES = ["notes/claims/", "notes/sources/"];

async function preFileSimilarityShadow(app, cp, crypto, request) {
  const basePath = vaultBasePath(app);
  const row = {
    timestamp: nowIso(),
    event: "pre_file_similarity_shadow",
    source: "quickadd.create-linked-claim",
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

function appendWorthDistillingLink(text, claimLink) {
  const line = "- " + claimLink;
  const heading = /^# Worth distilling\s*$/m;
  const match = heading.exec(text);
  if (!match) return text.replace(/\s*$/, "\n\n# Worth distilling\n\n" + line + "\n");
  const insertAt = match.index + match[0].length;
  return text.slice(0, insertAt) + "\n\n" + line + text.slice(insertAt);
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
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 70) || "claim";
}

function yamlString(s) {
  return "\"" + String(s).replace(/\\/g, "\\\\").replace(/"/g, "\\\"") + "\"";
}

function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
