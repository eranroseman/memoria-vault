/*
 * Shared helpers for Memoria QuickAdd user scripts.
 *
 * Keep this dependency-free: these scripts run inside Obsidian's QuickAdd
 * CommonJS environment.
 */

function run(cp, sh) {
  return new Promise((resolve, reject) => {
    cp.execFile("bash", ["-lc", sh], { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(String(stderr || err.message || "").trim()));
      resolve(stdout);
    });
  });
}

function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

function fnv1a(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

function queueHermesCard(cp, card) {
  let command =
    "hermes kanban create " + shq(card.title) +
    " --assignee " + card.assignee +
    (card.skill ? " --skill " + card.skill : "") +
    " --created-by quickadd" +
    " --idempotency-key " + shq(card.idemKey) +
    " --body " + shq(card.body);
  return run(cp, command);
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

async function archiveActiveNote(params, spec) {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const file = app.workspace.getActiveFile();
  if (!file) {
    new Notice("No active note — open the " + spec.label + " note first.", 6000);
    return;
  }
  if (!file.path.startsWith(spec.folder) || !file.path.endsWith(".md")) {
    new Notice(
      "Not a " + spec.label + " note (" + file.path + ") — only notes under " +
        spec.folder + " archive here.",
      8000
    );
    return;
  }
  try {
    await app.fileManager.processFrontMatter(file, (fm) => {
      if ((fm.type || "") !== spec.type) {
        throw new Error("Active note is not type: " + spec.type + ".");
      }
      fm.lifecycle = "archived";
      fm.archived = todayIsoDate();
    });
    new Notice("Archived " + spec.label + " note: " + file.basename, 6000);
  } catch (e) {
    new Notice(("Archive " + spec.label + " note failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
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

function slug(s, fallback = "note") {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || fallback;
}

function yamlString(s) {
  return "\"" + String(s).replace(/\\/g, "\\\\").replace(/"/g, "\\\"") + "\"";
}

function normalizeList(value) {
  if (Array.isArray(value)) return value.map(String).map((s) => s.trim()).filter(Boolean);
  if (typeof value === "string") {
    return value.split(/[,;\n]/).map((s) => s.trim()).filter(Boolean);
  }
  return [];
}

async function appendCallout(app, file, callout) {
  const content = await app.vault.read(file);
  const updated = content.endsWith("\n")
    ? content + "\n" + callout
    : content + "\n\n" + callout;
  await app.vault.modify(file, updated);
}

module.exports = {
  appendCallout,
  archiveActiveNote,
  exists,
  fnv1a,
  normalizeList,
  queueHermesCard,
  run,
  shq,
  slug,
  todayIsoDate,
  uniquePath,
  yamlString,
};
