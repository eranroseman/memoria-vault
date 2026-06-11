/*
 * QuickAdd user script — "Memoria: capture from Zotero selection".
 *
 * Reads the item currently selected in Zotero (Better BibTeX CAYW) and creates
 * an `intake:source` card on the Librarian lane (`hermes kanban create`). The
 * gateway's embedded dispatcher then ingests the citekey into catalog/papers/.
 *
 * Both the Zotero read and the card-create go through `bash -lc` (wrapped in
 * wsl.exe on Windows). We deliberately use `curl`, NOT Obsidian's requestUrl:
 * Zotero's local server refuses any request carrying an Origin header (which
 * requestUrl always sends), so a browser-style fetch gets HTTP 000. curl sends
 * no Origin and is accepted. On Windows this also reuses WSL2 mirrored
 * networking to reach Zotero on 127.0.0.1:23119.
 */

const CAYW = "http://127.0.0.1:23119/better-bibtex/cayw?selected=true&format=json";

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const onWindows = process.platform === "win32";

  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = onWindows ? "wsl.exe" : "bash";
      const args = onWindows ? ["bash", "-lc", sh] : ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

  // 1. Current Zotero selection via curl (no Origin header -> Zotero accepts it)
  let raw;
  try {
    raw = (await run(`curl -s --max-time 8 '${CAYW}'`)).trim();
  } catch (e) {
    new Notice("Zotero not reachable — is it running with Better BibTeX? " +
               "(On Windows, WSL2 mirrored networking must be on.) " + e.message, 9000);
    return;
  }
  if (!raw) {
    new Notice("No Zotero item selected — select a source in Zotero, then run this again.", 8000);
    return;
  }
  let items;
  try {
    items = JSON.parse(raw);
  } catch (e) {
    new Notice("Couldn't parse Zotero's response: " + raw.slice(0, 160), 9000);
    return;
  }
  if (!Array.isArray(items) || items.length === 0) {
    new Notice("No Zotero item selected — select a source in Zotero, then run this again.", 8000);
    return;
  }

  const item = items[0];
  const citekey = String(item.citationKey || item.citekey || "").trim();
  const title = String(item.title || "").replace(/\s+/g, " ").trim();
  if (!citekey) {
    new Notice("Selected Zotero item has no citekey — pin a Better BibTeX key first.", 9000);
    return;
  }
  if (items.length > 1) {
    new Notice(`${items.length} items selected — capturing the first (${citekey}).`, 6000);
  }

  // 1b. Capture commits first — append the durability anchor to the intake log
  //     BEFORE the gated write, so a failure downstream loses nothing (the
  //     reconcile sweep re-drives any logged citekey with no note on disk).
  const app = params.app || globalThis.app;
  const LOG = "99-system/logs/capture-intake.jsonl";
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

  // 2. Create the intake:source card on the Librarian lane
  const cardTitle = `Ingest source: ${citekey}`;
  const body =
    "intake:source — captured from Zotero. " +
    "Ingest the source with citekey `" + citekey + "`" +
    (title ? " (title: " + title + ")" : "") +
    " using the catalog-enrich-record skill: run `/catalog-enrich-record --source " + citekey + "`. " +
    "Create the paper entity under catalog/papers/, enrich it, propose the classification, " +
    "then kanban_complete with review_status: requested.";

  new Notice(`Capturing ${citekey}…`, 3000);
  try {
    await run(
      "hermes kanban create " + shq(cardTitle) +
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
