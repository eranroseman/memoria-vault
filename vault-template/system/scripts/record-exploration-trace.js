/*
 * QuickAdd user script — "Memoria: record exploration trace".
 *
 * Captures a rejected direction/dead end beside a Librarian map-lane report.
 * The note is project-local context under knowledge/notes/maps/. It is born
 * unchecked; the worker/check loop owns promotion.
 */

const MAPS_DIR = "knowledge/notes/maps/";
const { fnv1a, uniquePath, yamlString } = require(require("path").join(globalThis.app.vault.adapter.getBasePath(), "system/scripts/quickadd-utils.js"));

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app;
  const active = app.workspace.getActiveFile();
  const activeReport = active && isMapReport(active.path) ? active.path : "";

  const reportPath =
    (await params.quickAddApi.inputPrompt(
      "Map or gap report path:",
      activeReport,
    ))?.trim() || activeReport;
  if (!reportPath || !isMapReport(reportPath)) {
    new Notice("Choose a report under " + MAPS_DIR + " to attach the trace.", 7000);
    return;
  }

  const direction = (await params.quickAddApi.inputPrompt(
    "Rejected direction or dead end:"
  ))?.trim();
  if (!direction) {
    new Notice("No rejected direction entered.", 4000);
    return;
  }

  const reason = (await params.quickAddApi.inputPrompt(
    "Why did it stall or get rejected?"
  ))?.trim() || "Not recorded.";
  const evidence = (await params.quickAddApi.inputPrompt(
    "Evidence checked (queries, notes, sources):"
  ))?.trim() || "Not recorded.";
  const retry = (await params.quickAddApi.inputPrompt(
    "Retry only if:"
  ))?.trim() || "New evidence changes the scope.";

  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const base = stripMd(reportPath).split("/").pop();
  const path = await uniquePath(
    app.vault.adapter,
    MAPS_DIR + base + "-exploration-trace-" + fnv1a(direction).slice(0, 8) + ".md",
  );
  const reportLink = "[[" + stripMd(reportPath) + "|" + base + "]]";
  const body = [
    "---",
    "title: " + yamlString("Exploration trace: " + direction),
    "type: note",
    "check_status: unchecked",
    "description: " + yamlString("Project-local exploration trace."),
    "created: " + today,
    "---",
    "",
    "# Exploration trace",
    "",
    "- Report: " + reportLink,
    "- Captured: " + now.toISOString(),
    "",
    "## Rejected direction",
    "",
    direction,
    "",
    "## Why rejected",
    "",
    reason,
    "",
    "## Evidence checked",
    "",
    evidence,
    "",
    "## Retry only if",
    "",
    retry,
    "",
    "## Boundary",
    "",
    "This is project-local exploration context. It is not a source, digest, or hub, and it is never adopted automatically into curated knowledge.",
    "",
  ].join("\n");

  await ensureFolder(app.vault.adapter, MAPS_DIR);
  await app.vault.adapter.write(path, body);
  new Notice("✓ Exploration trace captured: " + path, 7000);
};

function isMapReport(path) {
  return path.startsWith(MAPS_DIR) && (
    path.includes("/corpus-map-") ||
    path.includes("/gap-report-") ||
    path.includes("/cluster-map-")
  ) && path.endsWith(".md");
}

function stripMd(path) {
  return String(path).replace(/\.md$/, "");
}

async function ensureFolder(adapter, folder) {
  const parts = folder.replace(/\/$/, "").split("/");
  let current = "";
  for (const part of parts) {
    current = current ? current + "/" + part : part;
    if (!(await adapter.exists(current))) await adapter.mkdir(current);
  }
}
