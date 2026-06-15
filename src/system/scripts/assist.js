/*
 * QuickAdd user script — "Memoria: assist …".
 *
 * Verb-shaped PI entry point (#380). The same script backs Find, Search,
 * Patterns, Ask, Draft, and Explore from the command palette. When text is
 * selected in the active editor, the selection rides with the card so invoking
 * the palette from a selection has a concrete local target. The Agent Client
 * pane is still the conversational version of Ask/Explore; this script is the
 * staged-proposal version for work that should leave an auditable artifact.
 */

const RESULTS_STAGE =
  "Results must land as proposals in staging or another review-gated proposal surface " +
  "(inbox/, notes/fleeting/, draft project output, or a returned pattern output_target). " +
  "Do not write directly to canonical/current notes.";

const PATTERNS_DIR = "system/patterns/";

const VERBS = {
  find: {
    label: "Find",
    prompt: "Source, topic, DOI, URL, or clue to find:",
    title: (goal) => "Assist find: " + short(goal),
    assignee: "memoria-librarian",
    skill: "catalog-find-source",
    body: (goal, ctx) =>
      "assist:find — from the palette or selection. Use catalog-find-source to find candidate sources for: " +
      goal + contextBody(ctx) + "\n\n" + RESULTS_STAGE,
  },
  search: {
    label: "Search",
    prompt: "Search lens or coverage question:",
    title: (goal) => "Assist search: " + short(goal),
    assignee: "memoria-librarian",
    skill: "map-report-coverage",
    body: (goal, ctx) =>
      "assist:search — from the palette or selection. Use map-report-coverage to search the corpus and report relevant coverage, gaps, or nearby material for this lens: " +
      goal + contextBody(ctx) + "\n\n" + RESULTS_STAGE,
  },
  ask: {
    label: "Ask",
    prompt: "Question for the Co-PI:",
    title: (goal) => "Assist ask: " + short(goal),
    assignee: "memoria-copi",
    skill: "ask-question-source",
    body: (goal, ctx) =>
      "assist:ask — staged Co-PI question from the palette or selection. Use ask-question-source or ask-read-lens as appropriate to answer: " +
      goal + contextBody(ctx) +
      "\n\nReturn the answer as a proposal artifact or Inbox note if it should persist; otherwise complete with a brief response summary. " +
      RESULTS_STAGE,
  },
  draft: {
    label: "Draft",
    prompt: "Draft goal, section, or outline ref:",
    title: (goal) => "Assist draft: " + short(goal),
    assignee: "memoria-writer",
    skill: "draft-write-section",
    body: (goal, ctx) =>
      "assist:draft — from the palette or selection. Use draft-write-section to draft: " +
      goal + contextBody(ctx) +
      "\n\nBind citations to claim notes and request review when complete. " + RESULTS_STAGE,
  },
  explore: {
    label: "Explore",
    prompt: "Question, tension, or frame to explore:",
    title: (goal) => "Assist explore: " + short(goal),
    assignee: "memoria-copi",
    skill: "explore-framings",
    body: (goal, ctx) =>
      "assist:explore — staged Co-PI exploration from the palette or selection. Use explore-framings to generate alternative framings for: " +
      goal + contextBody(ctx) +
      "\n\nIf a durable follow-up is warranted, propose it through the normal gated route. " +
      RESULTS_STAGE,
  },
};

async function entry(params, settings = {}) {
  const { Notice } = params.obsidian;
  const cp = require("child_process");
  const onWindows = process.platform === "win32";
  const verb = String(settings.Verb || "").toLowerCase();

  const run = (sh) =>
    new Promise((resolve, reject) => {
      const file = onWindows ? "wsl.exe" : "bash";
      const args = onWindows ? ["bash", "-lc", sh] : ["-lc", sh];
      cp.execFile(file, args, { timeout: 30000, maxBuffer: 1 << 20 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(String(stderr || err.message || "").trim()));
        resolve(stdout);
      });
    });

  const ctx = selectionContext(params);
  if (verb === "patterns") {
    await queuePattern(params, run, ctx);
    return;
  }

  const spec = VERBS[verb];
  if (!spec) {
    new Notice("Unknown Memoria assist verb: " + (settings.Verb || "missing"), 8000);
    return;
  }

  const goal = (await params.quickAddApi.inputPrompt(spec.prompt))?.trim() || ctx.selection;
  if (!goal) {
    new Notice("No " + spec.label.toLowerCase() + " request entered.", 4000);
    return;
  }

  const body = spec.body(goal, ctx);
  const idemKey = "quickadd-assist-" + verb + "-" + fnv1a(goal + "\n" + ctx.activePath + "\n" + ctx.selection);

  new Notice("Queuing assist " + verb + "…", 3000);
  try {
    await run(
      "hermes kanban create " + shq(spec.title(goal)) +
      " --assignee " + spec.assignee + " --skill " + spec.skill +
      " --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Assist " + verb + " card created (" + spec.assignee + ").", 6000);
  } catch (e) {
    new Notice(("Assist " + verb + " failed: " + e.message).slice(0, 250), 10000);
  }
}

module.exports = {
  entry,
  settings: {
    name: "Memoria: assist",
    author: "Memoria",
    options: {
      Verb: {
        type: "text",
        defaultValue: "find",
        placeholder: "find | search | patterns | ask | draft | explore",
      },
    },
  },
};

async function queuePattern(params, run, ctx) {
  const { Notice } = params.obsidian;
  const patterns = params.app.vault
    .getMarkdownFiles()
    .filter((f) => f.path.startsWith(PATTERNS_DIR) && !f.name.startsWith("_"))
    .filter((f) => {
      const fm = params.app.metadataCache.getFileCache(f)?.frontmatter || {};
      return fm.type === "pattern" && fm.lifecycle === "current";
    })
    .sort((a, b) => a.basename.localeCompare(b.basename));
  if (!patterns.length) {
    new Notice("No runnable patterns found under " + PATTERNS_DIR, 6000);
    return;
  }

  const display = patterns.map((f) => {
    const fm = params.app.metadataCache.getFileCache(f)?.frontmatter || {};
    return (fm.title || f.basename) + " (" + f.basename + ")";
  });
  const patternId = await params.quickAddApi.suggester(display, patterns.map((f) => f.basename));
  if (!patternId) {
    new Notice("No pattern chosen.", 4000);
    return;
  }

  const instruction = (await params.quickAddApi.inputPrompt(
    "Optional pattern goal or lens (Enter to use active note/selection):"
  ))?.trim();
  const body =
    "assist:patterns — from the palette or selection. Call patterns_run with pattern_id: " + patternId +
    (ctx.activePath ? " and input_ref: " + ctx.activePath + " (load that note as the input)" : "") +
    (instruction ? ". Apply this lens: " + instruction : "") + contextBody(ctx) +
    "\n\nExecute the composed prompt, write only to the returned output_target " +
    "(dry-run results are reported, not written), then kanban_complete with review_status: requested. " +
    RESULTS_STAGE;
  const idemKey = "quickadd-assist-patterns-" + fnv1a(patternId + "\n" + instruction + "\n" + ctx.activePath + "\n" + ctx.selection);

  new Notice("Queuing assist pattern " + patternId + "…", 3000);
  try {
    await run(
      "hermes kanban create " + shq("Assist patterns: " + patternId + (ctx.activePath ? " on " + ctx.activePath : "")) +
      " --assignee memoria-librarian --created-by quickadd" +
      " --idempotency-key " + shq(idemKey) +
      " --body " + shq(body)
    );
    new Notice("✓ Assist patterns card created (" + patternId + ").", 6000);
  } catch (e) {
    new Notice(("Assist patterns failed: " + e.message).slice(0, 250), 10000);
  }
}

function selectionContext(params) {
  const active = params.app.workspace.getActiveFile();
  let selection = "";
  const view = params.app.workspace.getActiveViewOfType?.(params.obsidian.MarkdownView);
  if (view?.editor?.getSelection) {
    selection = String(view.editor.getSelection() || "").trim();
  }
  return {
    activePath: active ? active.path : "",
    selection,
  };
}

function contextBody(ctx) {
  let text = "";
  if (ctx.activePath) text += "\n\nActive note: " + ctx.activePath;
  if (ctx.selection) text += "\n\nSelection:\n```markdown\n" + fence(ctx.selection) + "\n```";
  return text;
}

function fence(s) {
  return String(s).replace(/```/g, "` ` `");
}

function short(s) {
  const oneLine = String(s).replace(/\s+/g, " ").trim();
  return oneLine.length > 72 ? oneLine.slice(0, 69) + "..." : oneLine;
}

// POSIX single-quote escape.
function shq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

// FNV-1a 32-bit hash, hex — small and dependency-free.
function fnv1a(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}
