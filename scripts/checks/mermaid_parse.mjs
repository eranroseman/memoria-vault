#!/usr/bin/env node
// Parse every ```mermaid fence in the given Markdown files.
//
// Just the Docs renders mermaid in the browser, so a malformed fence fails no
// build and no test -- it just shows readers an error box on the published
// page. Prose under docs/ has markdownlint, cspell, and vale; diagrams had
// nothing. This closes that.
//
// The installed mermaid must match `docs/_config.yml`'s pinned version: a gate
// that parses a different version than the site renders reports the wrong
// answer in both directions, so a mismatch is a hard failure, not a warning.

import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

// pre-commit installs node `additional_dependencies` into a global prefix
// (`<env>/lib/node_modules`) that Node's resolver never searches for a script
// run by path -- only published bins like markdownlint resolve their own deps.
// So look there explicitly, finding the prefix from the env's bin on PATH.
function envModuleRoot() {
  for (const dir of (process.env.PATH ?? "").split(path.delimiter)) {
    const match = /^(.*node_env[^/]*)[/\\]bin[/\\]?$/.exec(dir);
    if (match) return path.join(match[1], "lib", "node_modules");
  }
  return null;
}

// A local node_modules (a developer who ran npm install) wins; the pre-commit
// prefix is the fallback. Either way the version check below is what decides
// whether the resolved copy is the one the site renders.
async function load(name) {
  try {
    return await import(name);
  } catch (error) {
    if (error?.code !== "ERR_MODULE_NOT_FOUND") throw error;
  }
  const root = envModuleRoot();
  if (!root) throw new Error(`cannot find ${name}: no node_env on PATH and no local node_modules`);
  const dir = path.join(root, name);
  const meta = JSON.parse(await readFile(path.join(dir, "package.json"), "utf8"));
  const entry =
    meta.exports?.["."]?.import ?? meta.exports?.["."]?.default ?? meta.module ?? meta.main;
  return import(pathToFileURL(path.join(dir, entry)).href);
}

const FENCE = /^([ \t]*)```mermaid[ \t]*$/;

function fences(text) {
  const lines = text.split("\n");
  const found = [];
  for (let i = 0; i < lines.length; i++) {
    const open = FENCE.exec(lines[i]);
    if (!open) continue;
    const closer = new RegExp(`^${open[1]}\`\`\`[ \t]*$`);
    const body = [];
    let j = i + 1;
    for (; j < lines.length && !closer.test(lines[j]); j++) body.push(lines[j]);
    // `line` is 1-indexed and points at the ```mermaid opener, so an error
    // message pastes straight into an editor.
    found.push({ line: i + 1, source: body.join("\n") });
    i = j;
  }
  return found;
}

// Read from package.json rather than mermaid's export: this runs before jsdom
// is set up, and importing mermaid without a DOM throws.
async function installedMermaidVersion() {
  try {
    return require("mermaid/package.json").version;
  } catch (error) {
    if (error?.code !== "MODULE_NOT_FOUND") throw error;
  }
  const root = envModuleRoot();
  if (!root) throw new Error("cannot find mermaid: no node_env on PATH and no local node_modules");
  const meta = JSON.parse(await readFile(path.join(root, "mermaid", "package.json"), "utf8"));
  return meta.version;
}

function siteVersion(repoRoot) {
  const config = require("node:fs").readFileSync(path.join(repoRoot, "docs/_config.yml"), "utf8");
  // Deliberately a regex rather than a YAML dependency: this gate should not
  // grow a parser to read one pinned string.
  const match = /^\s*version:\s*"?([\d.]+)"?\s*$/m.exec(config.slice(config.indexOf("mermaid:")));
  return match ? match[1] : null;
}

async function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) return 0;

  const repoRoot = process.cwd();
  const installed = await installedMermaidVersion();
  const site = siteVersion(repoRoot);
  if (site && installed !== site) {
    console.error(
      `mermaid-parse: gate runs mermaid ${installed} but docs/_config.yml renders ${site}.\n` +
        "  Pin them together in .pre-commit-config.yaml, or the gate grades the wrong grammar.",
    );
    return 1;
  }

  // jsdom first: mermaid touches `document` while its module body runs, so the
  // globals have to exist before it is imported.
  const { JSDOM } = await load("jsdom");
  const dom = new JSDOM("<!doctype html><body></body>", { pretendToBeVisual: true });
  global.window = dom.window;
  global.document = dom.window.document;

  const { default: mermaid } = await load("mermaid");
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

  const errors = [];
  for (const file of files) {
    const text = await readFile(file, "utf8");
    for (const { line, source } of fences(text)) {
      try {
        await mermaid.parse(source);
      } catch (err) {
        const detail = String(err?.message ?? err).split("\n")[0];
        errors.push(`${path.relative(repoRoot, file)}:${line}: ${detail}`);
      }
    }
  }

  for (const error of errors) console.error(error);
  if (errors.length) {
    console.error(`mermaid-parse: ${errors.length} fence(s) failed to parse`);
    return 1;
  }
  return 0;
}

process.exitCode = await main();
