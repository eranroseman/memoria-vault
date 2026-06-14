/*
 * QuickAdd user script — "Memoria: capture source from URL".
 *
 * Prompts for a URL and creates an `intake:source` card on the Librarian lane
 * (`hermes kanban create`). The Librarian resolves the URL (DOI / identifiers)
 * during ingest. Mirrors capture-from-zotero.js: the card-create goes through
 * `bash -lc` (wrapped in wsl.exe on Windows) so it reaches hermes in WSL.
 */

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

  const url = (await params.quickAddApi.inputPrompt("Source URL to capture:"))?.trim();
  if (!url) {
    new Notice("No URL entered.", 4000);
    return;
  }
  if (!/^https?:\/\//i.test(url)) {
    new Notice("That doesn't look like a URL (expected http/https).", 6000);
    return;
  }

  const body =
    "intake:source — captured from URL. Resolve and ingest the source at " + url + " " +
    "using the catalog-enrich-record skill: fetch its metadata (DOI / identifiers), add it to the " +
    "library, create the paper entity under catalog/papers/, create the proposed source-note stub " +
    "under notes/source/ for the PI to fill, enrich it, propose the classification, then " +
    "kanban_complete with review_status: requested.";

  new Notice("Capturing " + url + " …", 3000);
  try {
    const card = await writeCandidateCard(params, url);
    new Notice("Needs me card created: " + card, 5000);
  } catch (e) {
    new Notice(("Inbox card write failed; continuing with ingest task: " + e.message).slice(0, 250), 9000);
  }
  try {
    await run(
      "hermes kanban create " + shq("Ingest source: " + url) +
      " --assignee memoria-librarian --skill catalog-enrich-record --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Captured → intake card created on the Librarian lane.", 6000);
  } catch (e) {
    new Notice(("Capture failed: " + e.message).slice(0, 250), 10000);
  }
};

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

async function writeCandidateCard(params, url) {
  const app = params.app || globalThis.app;
  if (!app?.vault?.adapter) throw new Error("Obsidian vault adapter unavailable");
  const adapter = app.vault.adapter;
  const host = new URL(url).hostname || "source";
  const title = "Review captured URL: " + host;
  const action = "Accept this URL into the catalog intake queue";
  const argumentFor = "The PI explicitly captured this URL for possible intake.";
  const argumentAgainst = "The source metadata has not been resolved yet, so relevance and bibliographic quality are still unknown.";
  const whatTippedIt = "A deliberate capture is enough to queue a lightweight keep/skip decision while the Librarian resolves metadata.";
  const stem = "candidate-" + slug(host + "-" + url);
  const path = await uniquePath(adapter, "inbox/" + stem + ".md");
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
    "url: " + yamlString(url),
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
