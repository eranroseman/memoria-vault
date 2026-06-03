/*
 * QuickAdd user script — "Memoria: capture from Zotero selection".
 *
 * Reads the item currently selected in Zotero (via the Better BibTeX CAYW
 * endpoint) and creates an `intake:source` card on the Librarian lane. The
 * Librarian dispatcher then ingests the citekey into 20-sources/ and completes
 * the card. This is the in-Obsidian half of the capture flow; the auto-pickup
 * also needs a running Librarian dispatcher (gateway + `hermes kanban dispatch`).
 *
 * Wiring: QuickAdd → Macro choice → this UserScript. Registered as the
 * command-palette entry `Memoria: capture from Zotero selection`.
 *
 * Requirements:
 *   - Zotero running with Better BibTeX (local server on 127.0.0.1:23119).
 *   - hermes on PATH inside WSL (Windows) or locally (Linux/Mac).
 *   - On Windows: WSL2 mirrored networking, so Obsidian can reach 23119.
 */

const ZOTERO_CAYW =
  "http://127.0.0.1:23119/better-bibtex/cayw?selected=true&format=json";

module.exports = async (params) => {
  const { Notice, requestUrl } = params.obsidian;

  // 1. Current Zotero selection -> citekey + title -----------------------------
  let items;
  try {
    const res = await requestUrl({ url: ZOTERO_CAYW, method: "GET", throw: false });
    if (res.status !== 200) throw new Error("HTTP " + res.status);
    items = res.json !== undefined ? res.json : JSON.parse(res.text);
  } catch (e) {
    new Notice("Zotero not reachable — is it running with Better BibTeX? " +
               "(On Windows, WSL2 mirrored networking must be on.)", 9000);
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

  // 2. Create the intake:source card on the Librarian lane ---------------------
  const cardTitle = `Ingest source: ${citekey}`;
  const body =
    "intake:source — captured from Zotero.\n\n" +
    "Ingest the source with citekey `" + citekey + "`" +
    (title ? " (title: " + title + ")" : "") +
    " using the obsidian-paper-note skill: run `/obsidian-paper-note --source " + citekey + "`. " +
    "Create the paper-note under 20-sources/, enrich it, propose the classification, " +
    "then kanban_complete with review_status: requested.";

  const sh =
    "hermes kanban create " + shq(cardTitle) +
    " --assignee memoria-librarian --skill obsidian-paper-note --created-by quickadd" +
    " --body " + shq(body);

  const cp = require("child_process");
  const onWindows = process.platform === "win32";
  const file = onWindows ? "wsl.exe" : "bash";
  const args = onWindows ? ["bash", "-lc", sh] : ["-lc", sh];

  new Notice(`Capturing ${citekey}…`, 3000);
  try {
    await new Promise((resolve, reject) => {
      cp.execFile(file, args, { timeout: 30000 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });
    new Notice(`✓ Captured ${citekey} → intake card created on the Librarian lane.`, 6000);
  } catch (e) {
    new Notice(`Capture failed for ${citekey}: ${e.message}`.slice(0, 300), 10000);
  }
};

// POSIX single-quote escape: wrap in '...', and close/escape/reopen on each '.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
