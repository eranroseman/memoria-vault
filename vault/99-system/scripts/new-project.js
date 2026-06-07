/*
 * QuickAdd user script — "Memoria: new project".
 *
 * Scaffolds a writing project: native input prompts (title, research question,
 * output type) → creates `40-workbench/<slug>/` with the six canonical
 * subfolders (`01-map` … `06-code`) → writes `README.md` from the project-note
 * template → creates a Mapper scope card (`hermes kanban create`). The card
 * produces the `corpus-map.md` the start-a-writing-project how-to ran manually.
 * Mirrors capture-from-url.js: the card-create goes through `bash -lc` (wrapped
 * in wsl.exe on Windows) so it reaches hermes in WSL.
 */

const SUBFOLDERS = ["01-map", "02-framing", "03-canvas", "04-drafts", "05-verification", "06-code"];
const TEMPLATE_PATH = "99-system/templates/project-note.md";

module.exports = async (params) => {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;
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

  // 1. Collect the form via native prompts.
  const title = (await params.quickAddApi.inputPrompt("Project title:"))?.trim();
  if (!title) {
    new Notice("No project title entered.", 4000);
    return;
  }
  const slug = slugify(title);
  if (!slug) {
    new Notice("Couldn't derive a folder slug from that title — use letters/numbers.", 6000);
    return;
  }
  const researchQuestion = (await params.quickAddApi.inputPrompt("Research question (optional):"))?.trim() || "";
  const outputType = (await params.quickAddApi.inputPrompt("Output type (paper / chapter / section / post):"))?.trim() || "";

  const adapter = app.vault.adapter;
  const projectDir = "40-workbench/" + slug;

  // 2. Scaffold the folder tree (project dir + six canonical subfolders).
  if (await adapter.exists(projectDir)) {
    new Notice("40-workbench/" + slug + "/ already exists — pick a different title.", 8000);
    return;
  }
  try {
    await adapter.mkdir(projectDir);
    for (const sub of SUBFOLDERS) {
      await adapter.mkdir(projectDir + "/" + sub);
    }
  } catch (e) {
    new Notice(("Couldn't create the project folders: " + e.message).slice(0, 250), 9000);
    return;
  }

  // 3. Write README.md from the project-note template.
  const today = new Date().toISOString().slice(0, 10);
  let readme;
  try {
    const tmpl = await adapter.read(TEMPLATE_PATH);
    readme = tmpl
      .replace(/\{\{VALUE:project title\}\}/g, title)
      .replace(/^research_question:.*$/m, 'research_question: "' + researchQuestion.replace(/"/g, '\\"') + '"')
      .replace(/^start_date:.*$/m, "start_date: " + today)
      .replace(/^outputs:.*$/m, "outputs: " + (outputType ? '["' + outputType.replace(/"/g, '\\"') + '"]' : "[]"))
      .replace(/\{\{DATE:YYYY-MM-DD\}\}/g, today);
  } catch (e) {
    new Notice(("Couldn't read the project-note template: " + e.message).slice(0, 250), 9000);
    return;
  }
  try {
    await adapter.write(projectDir + "/README.md", readme);
  } catch (e) {
    new Notice(("Couldn't write README.md: " + e.message).slice(0, 250), 9000);
    return;
  }

  // 4. Create the Mapper scope card.
  const body =
    "Scope the writing project `" + slug + "` (title: " + title + ")" +
    (researchQuestion ? ". Research question: " + researchQuestion : "") +
    ". Run the scope-project skill: search the vault for claim notes and source notes " +
    "relevant to the project, then write a corpus map to " +
    projectDir + "/01-map/corpus-map.md summarizing what's present and what's missing.";

  new Notice("Scaffolded 40-workbench/" + slug + "/ — creating the Mapper scope card…", 4000);
  try {
    await run(
      "hermes kanban create " + shq("Scope project: " + slug) +
      " --assignee memoria-mapper --skill scope-project --created-by quickadd" +
      " --body " + shq(body)
    );
    new Notice("✓ Project scaffolded → Mapper scope card created.", 6000);
  } catch (e) {
    new Notice(("Project scaffolded, but the scope card failed: " + e.message).slice(0, 250), 10000);
  }
};

// Derive a folder slug from the title: lowercase, words joined by hyphens.
function slugify(s) {
  return String(s)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}
