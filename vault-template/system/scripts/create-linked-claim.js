/*
 * QuickAdd user script — "Memoria: create linked claim note".
 *
 * From an active source note, create a schema-shaped claim note, link it back to
 * the source citekey in frontmatter, append the claim link under Worth distilling,
 * and open the new claim for the PI to edit.
 */

const { appendSimilarityTelemetry, buildSimilarityCallout, preFileSimilarityShadow } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-similarity.js"));
const { slug, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

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
  const claimPath = await uniquePath(adapter, "notes/claims/" + slug(claim, "claim") + ".md");
  const claimLink = "[[" + claimPath.replace(/\.md$/, "") + "|" + claim + "]]";
  const today = new Date().toISOString().slice(0, 10);
  const similarity = await preFileSimilarityShadow(app, cp, crypto, {
    source: "quickadd.create-linked-claim",
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

function appendWorthDistillingLink(text, claimLink) {
  const line = "- " + claimLink;
  const heading = /^# Worth distilling\s*$/m;
  const match = heading.exec(text);
  if (!match) return text.replace(/\s*$/, "\n\n# Worth distilling\n\n" + line + "\n");
  const insertAt = match.index + match[0].length;
  return text.slice(0, insertAt) + "\n\n" + line + text.slice(insertAt);
}
