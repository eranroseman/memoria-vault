/*
 * QuickAdd user script - "Memoria: load sample vault".
 *
 * Copies the bundled sample notes from .memoria/samples into the live vault.
 * Existing files are left untouched so the command never overwrites user work.
 */

const fs = require("fs");
const path = require("path");
const { exists } = require(path.join(
  globalThis.app.vault.adapter.getBasePath(),
  "system/scripts/quickadd-utils.js",
));

const SAMPLE_ROOT = ".memoria/samples/mediterranean-diet";
const LIVE_PREFIXES = ["catalog/", "notes/"];

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const adapter = app.vault.adapter;
  const basePath = adapter.getBasePath();
  const sourceRoot = path.join(basePath, SAMPLE_ROOT);

  if (!fs.existsSync(sourceRoot)) {
    new Notice("Sample bundle not found: " + SAMPLE_ROOT, 8000);
    return;
  }

  try {
    let copied = 0;
    let skipped = 0;
    for (const sourcePath of listMarkdownFiles(sourceRoot)) {
      const rel = path.relative(sourceRoot, sourcePath).split(path.sep).join("/");
      if (!LIVE_PREFIXES.some((prefix) => rel.startsWith(prefix))) continue;
      if (await exists(adapter, rel)) {
        skipped += 1;
        continue;
      }
      await ensureParentFolder(adapter, rel);
      await adapter.write(rel, fs.readFileSync(sourcePath, "utf8"));
      copied += 1;
    }

    if (!copied && skipped) {
      new Notice("Sample vault already loaded (" + skipped + " files present).", 7000);
      return;
    }
    new Notice(
      "Loaded sample vault: " + copied + " files copied, " + skipped + " existing skipped.",
      8000,
    );
  } catch (e) {
    new Notice(("Load sample vault failed: " + (e?.message || e)).slice(0, 250), 10000);
  }
};

function listMarkdownFiles(root) {
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) out.push(...listMarkdownFiles(full));
    if (entry.isFile() && entry.name.endsWith(".md")) out.push(full);
  }
  return out.sort();
}

async function ensureParentFolder(adapter, filePath) {
  const parts = filePath.split("/").slice(0, -1);
  let current = "";
  for (const part of parts) {
    current = current ? current + "/" + part : part;
    if (!(await exists(adapter, current))) await adapter.mkdir(current);
  }
}
