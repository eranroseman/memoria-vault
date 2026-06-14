/*
 * QuickAdd user script — "Memoria: open Desk workspace / Library / Studio".
 *
 * Loads a named workspace layout via the core Workspaces plugin, which has
 * no per-workspace palette commands of its own. One script serves all three
 * macros: each macro passes its target via QuickAdd's per-command `settings`
 * ("Workspace" option, second argument to the entry function); if the
 * setting is missing or names an unsaved workspace, a suggester over the
 * saved layouts is the fallback. Pure Obsidian app API — no shelling, so it
 * works identically on every platform.
 */

const WORKSPACES = ["Desk", "Library", "Studio"];

module.exports = {
  entry: async (params, settings) => {
    const { Notice } = params.obsidian;
    const app = params.app || globalThis.app;

    const plugin = app.internalPlugins?.getPluginById?.("workspaces");
    const instance = plugin?.instance;
    if (!plugin?.enabled || typeof instance?.loadWorkspace !== "function") {
      new Notice("Workspaces core plugin is not enabled — turn it on in Settings → Core plugins.", 8000);
      return;
    }

    const saved = Object.keys(instance.workspaces ?? {});
    let name = (settings?.Workspace ?? "").trim();
    if (!name || (saved.length && !saved.includes(name))) {
      const options = saved.length ? saved : WORKSPACES;
      name = await params.quickAddApi.suggester(options, options);
      if (!name) {
        new Notice("No workspace chosen.", 4000);
        return;
      }
    }

    try {
      instance.loadWorkspace(name);
    } catch (e) {
      new Notice("Could not load workspace " + name + ": " + (e?.message ?? e), 8000);
    }
  },
  settings: {
    name: "Memoria: load workspace",
    author: "Memoria",
    options: {
      Workspace: {
        type: "text",
        defaultValue: "",
        placeholder: "Desk | Library | Studio",
      },
    },
  },
};
