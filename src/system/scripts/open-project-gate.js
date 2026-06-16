/*
 * QuickAdd user script — "Memoria: open Project gate".
 *
 * Project is not a fourth saved workspace. It is the bounded-inquiry gate
 * opened inside the Studio workspace shell.
 */

const WORKSPACE = "Studio";
const PROJECT_GATE = "system/dashboards/project-gate.md";

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;

  const plugin = app.internalPlugins?.getPluginById?.("workspaces");
  const instance = plugin?.instance;
  if (!plugin?.enabled || typeof instance?.loadWorkspace !== "function") {
    new Notice("Workspaces core plugin is not enabled — turn it on in Settings → Core plugins.", 8000);
    return;
  }

  try {
    const loaded = instance.loadWorkspace(WORKSPACE);
    if (loaded && typeof loaded.then === "function") await loaded;
  } catch (e) {
    new Notice("Could not load Studio workspace: " + (e?.message ?? e), 8000);
    return;
  }

  const file = app.vault.getAbstractFileByPath(PROJECT_GATE);
  if (!file) {
    new Notice("Project gate dashboard not found: " + PROJECT_GATE, 8000);
    return;
  }

  await app.workspace.getLeaf(false).openFile(file, { active: true });
};
