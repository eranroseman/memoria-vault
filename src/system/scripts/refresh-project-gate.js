/*
 * QuickAdd user script — "Memoria: refresh project gate".
 *
 * Runs the deterministic structural-impact Operation against the active
 * project note and updates projects/<slug>/project-gate-index.md.
 */

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const app = params.app || globalThis.app;
  const active = app?.workspace?.getActiveFile?.();
  const projectPath = active ? projectNotePath(active.path) : "";
  if (!projectPath) {
    new Notice("Open a project file under projects/<slug>/ before refreshing the Project gate.", 8000);
    return;
  }

  const vault = app.vault.adapter.getBasePath ? app.vault.adapter.getBasePath() : "";
  if (!vault) {
    new Notice("Cannot resolve the vault path for Project gate refresh.", 8000);
    return;
  }
  const python = await pythonCommand(app);
  const script = ".memoria/operations/processing/project/structural_impact.py";
  const args = [script, "--vault", vault, "--project", projectPath];

  new Notice("Refreshing Project gate…", 3000);
  cp.execFile(python, args, { cwd: vault, timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
    if (err) {
      new Notice(("Project gate refresh failed: " + String(stderr || err.message || "").trim()).slice(0, 250), 10000);
      return;
    }
    new Notice(("✓ Project gate refreshed: " + String(stdout || "").trim()).slice(0, 250), 8000);
  });
};

function projectNotePath(path) {
  const parts = String(path || "").split("/");
  if (parts[0] !== "projects" || parts.length < 2) return "";
  return "projects/" + parts[1] + "/project.md";
}

async function pythonCommand(app) {
  const adapter = app.vault.adapter;
  for (const candidate of [".memoria/.venv/Scripts/python.exe", ".memoria/.venv/bin/python"]) {
    if (typeof adapter.exists === "function" && await adapter.exists(candidate)) return candidate;
  }
  return process.platform === "win32" ? "py" : "python3";
}
