/*
 * QuickAdd user script — "Memoria: capture from Zotero selection".
 *
 * Reads the item currently selected in Zotero (Better BibTeX JSON-RPC) and
 * creates a Tier-0 catalog stub plus an `intake:source` card on the Librarian
 * lane (Hermes kanban). The gateway's embedded dispatcher then enriches the
 * citekey in catalog/papers/.
 *
 * Both the Zotero read and the card-create go through `bash -lc`. We
 * deliberately use `curl`, NOT Obsidian's requestUrl:
 * Zotero's local server refuses any request carrying an Origin header (which
 * requestUrl always sends), so a browser-style fetch gets HTTP 000. curl sends
 * no Origin and is accepted.
 */

const BBT_RPC = "http://127.0.0.1:23119/better-bibtex/json-rpc";
const SELECTED_CITEKEY_REQUEST =
  '[{"jsonrpc":"2.0","method":"item.citationkey","params":["selected"],"id":1}]';

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = "bash";
      const args = ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

  // 1. Current Zotero selection via curl (no Origin header -> Zotero accepts it)
  let raw;
  try {
    raw = (await run(
      `curl -s --max-time 8 -H 'Content-Type: application/json' --data ${shq(SELECTED_CITEKEY_REQUEST)} '${BBT_RPC}'`
    )).trim();
  } catch (e) {
    new Notice("Zotero not reachable — is it running with Better BibTeX? " + e.message, 9000);
    return;
  }
  if (!raw) {
    new Notice("No Zotero item selected — select a source in Zotero, then run this again.", 8000);
    return;
  }
  let citekeys;
  try {
    citekeys = parseSelectedCitekeys(raw);
  } catch (e) {
    new Notice(e.message.slice(0, 240), 9000);
    return;
  }
  if (citekeys.length === 0) {
    new Notice("No Zotero item selected — select a source in Zotero, then run this again.", 8000);
    return;
  }

  const citekey = citekeys[0];
  const title = "";
  if (!citekey) {
    new Notice("Selected Zotero item has no citekey — pin a Better BibTeX key first.", 9000);
    return;
  }
  if (citekeys.length > 1) {
    new Notice(`${citekeys.length} items selected — capturing the first (${citekey}).`, 6000);
  }

  // 1b. Capture commits first — append the durability anchor to the intake log
  //     BEFORE the gated write, so a failure downstream loses nothing (the
  //     reconcile sweep re-drives any logged citekey with no note on disk).
  const app = params.app || globalThis.app;
  const LOG = "system/logs/capture-intake.jsonl";
  try {
    const rec = JSON.stringify({
      ts: new Date().toISOString(),
      citekey,
      source: "zotero",
      note_path: `catalog/papers/${citekey}.md`,
    }) + "\n";
    const adapter = app.vault.adapter;
    let prev = "";
    try { prev = await adapter.read(LOG); } catch (e) { /* first capture — file absent */ }
    await adapter.write(LOG, prev + rec);
  } catch (e) {
    // Non-fatal: warn but still create the card (don't block capture on a log write).
    new Notice(`Capture-intake log write failed for ${citekey} (continuing): ${e.message}`.slice(0, 200), 6000);
  }

  // 1c. Materialize the Tier-0 Catalog floor immediately. This is intentionally
  //     minimal and idempotent: the Librarian enriches it later, but capture
  //     itself must visibly add the selected Zotero item to the Catalog.
  try {
    const stub = await writePaperStub(params, citekey, title);
    new Notice("Catalog stub ready: " + stub, 5000);
  } catch (e) {
    new Notice(("Catalog stub write failed; continuing with ingest task: " + e.message).slice(0, 250), 9000);
  }

  // 2. Create the intake:source card on the Librarian lane
  const cardTitle = `Ingest source: ${citekey}`;
  const body =
    "intake:source — captured from Zotero. " +
    "Ingest the source with citekey " + citekey +
    (title ? " (title: " + title + ")" : "") +
    " using the catalog-enrich-record skill with source " + citekey + ". " +
    "Create the paper entity under catalog/papers/, create the proposed source-note stub " +
    "under notes/sources/ for the PI to fill, enrich it, propose the classification, " +
    "then kanban_complete with review_status: requested.";

  new Notice(`Capturing ${citekey}…`, 3000);
  try {
    const card = await writeCandidateCard(params, citekey, title);
    new Notice("Needs me card created: " + card, 5000);
  } catch (e) {
    new Notice(("Inbox card write failed; continuing with ingest task: " + e.message).slice(0, 250), 9000);
  }
  try {
    await run(
      hermesCommand() + " kanban create " + shq(cardTitle) +
      " --assignee memoria-librarian --skill catalog-enrich-record --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice(`✓ Captured ${citekey} → intake card created on the Librarian lane.`, 6000);
  } catch (e) {
    new Notice(`Capture failed for ${citekey}: ${e.message}`.slice(0, 300), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

function hermesCommand() {
  return [
    'PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"',
    'command -v hermes >/dev/null || { echo "Hermes not found on PATH; install Hermes or add it to the WSL login-shell PATH." >&2; exit 127; }',
    'hermes',
  ].join("; ");
}

function parseSelectedCitekeys(raw) {
  let response;
  try {
    response = JSON.parse(raw);
  } catch (e) {
    throw new Error("Couldn't parse Better BibTeX's response: " + String(raw).slice(0, 160));
  }
  const first = Array.isArray(response) ? response[0] : response;
  if (!first || typeof first !== "object") {
    throw new Error("Better BibTeX returned an unexpected response: " + String(raw).slice(0, 160));
  }
  if (first.error) {
    throw new Error("Better BibTeX selection lookup failed: " + String(first.error.message || JSON.stringify(first.error)).slice(0, 180));
  }
  const result = first.result || {};
  return Object.values(result).filter((key) => typeof key === "string" && key.trim()).map((key) => key.trim());
}

async function writeCandidateCard(params, citekey, sourceTitle) {
  const app = params.app || globalThis.app;
  if (!app?.vault?.adapter) throw new Error("Obsidian vault adapter unavailable");
  const adapter = app.vault.adapter;
  const title = "Review Zotero capture: " + citekey;
  const action = "Accept Zotero item " + citekey + " into the catalog intake queue";
  const argumentFor = "The PI explicitly selected this Zotero item for possible intake.";
  const argumentAgainst = "The bibliographic record has not been enriched yet, so relevance and metadata quality are still unknown.";
  const whatTippedIt = "A deliberate Zotero selection is enough to queue a lightweight keep/skip decision while the Librarian resolves metadata.";
  const path = await uniquePath(adapter, "inbox/candidate-zotero-" + slug(citekey) + ".md");
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
    "certainty: unsure",
    "citekey: " + yamlString(citekey),
    "raised_by: quickadd",
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
    sourceTitle ? "Source title: " + sourceTitle : "",
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
  ].filter((line, idx, lines) => line || lines[idx - 1]).join("\n");
  await adapter.write(path, frontmatter + body);
  return path;
}

async function writePaperStub(params, citekey, sourceTitle) {
  const app = params.app || globalThis.app;
  if (!app?.vault?.adapter) throw new Error("Obsidian vault adapter unavailable");
  const adapter = app.vault.adapter;
  const path = "catalog/papers/" + citekey + ".md";
  if (await exists(adapter, path)) return path;
  await ensureFolder(adapter, "catalog/papers");
  const today = new Date().toISOString().slice(0, 10);
  const title = sourceTitle || "Zotero capture: " + citekey;
  const frontmatter = [
    "---",
    "title: " + yamlString(title),
    "type: paper",
    "lifecycle: current",
    "citekey: " + yamlString(citekey),
    "ingest_status: tier0",
    "doi: \"\"",
    "authors: []",
    "venue: \"\"",
    "url: \"\"",
    "research_area: []",
    "methodology: []",
    "relationships:",
    "  cited_by: []",
    "  authored_by: []",
    "  published_in: \"\"",
    "created: " + today,
    "---",
    "",
  ].join("\n");
  const body = [
    "# What it is",
    "",
    "Captured from Zotero with citekey `" + citekey + "`. The Librarian still needs to enrich this Tier-0 stub.",
    "",
    "# Relationships",
    "",
    "Given facts only — built by the ingest operation, never authored here (ADR-52).",
    "",
  ].join("\n");
  await adapter.write(path, frontmatter + body);
  return path;
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

async function ensureFolder(adapter, folder) {
  const parts = folder.split("/");
  let current = "";
  for (const part of parts) {
    current = current ? current + "/" + part : part;
    if (!(await exists(adapter, current))) await adapter.mkdir(current);
  }
}

function slug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "source";
}

function yamlString(s) {
  return "\"" + String(s).replace(/\\/g, "\\\\").replace(/"/g, "\\\"") + "\"";
}
