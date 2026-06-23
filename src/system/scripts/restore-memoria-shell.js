/*
 * QuickAdd startup script - restore the shipped Memoria Obsidian shell.
 *
 * Workspaces owns the layout. This script only asks the enabled core plugin to
 * reload the saved Memoria workspace after Obsidian's first layout is ready.
 */

const WORKSPACE_NAME = "Memoria";
const NAV_FILE = "_nav.md";
const RAIL_SETTLE_MS = 500;

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
  const workspaces = app?.internalPlugins?.plugins?.workspaces?.instance;

  if (!workspaces?.loadWorkspace) {
    new Notice("Memoria startup shell unavailable - enable the Workspaces core plugin.", 8000);
    return;
  }
  if (!workspaces.workspaces?.[WORKSPACE_NAME]) {
    new Notice("Memoria startup shell missing saved workspace: " + WORKSPACE_NAME, 8000);
    return;
  }

  await workspaces.loadWorkspace(WORKSPACE_NAME);
  await revealNavRail(app);

  // ponytail: Portals can finish startup after QuickAdd; one delayed reveal wins the race.
  await new Promise((resolve) => setTimeout(resolve, RAIL_SETTLE_MS));
  await revealNavRail(app);
};

async function revealNavRail(app) {
  const navLeaf = app.workspace.getLeavesOfType?.("markdown")
    ?.find((leaf) => leaf.getViewState?.()?.state?.file === NAV_FILE);
  if (navLeaf && app.workspace.revealLeaf) {
    await app.workspace.revealLeaf(navLeaf);
  }
}
