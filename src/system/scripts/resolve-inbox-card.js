/*
 * QuickAdd user script — "Memoria: resolve inbox card".
 *
 * Resolves the ACTIVE inbox card in place: prompts for an outcome, flips the
 * frontmatter `lifecycle:` to a schema-valid inbox value and stamps `resolved:` with
 * today's date. It also appends Obsidian-side attention, triage, and review
 * disposition rows. Pure Obsidian app API — no shelling, so it works
 * identically on every platform.
 */

// Outcome label → lifecycle value written to the card.
const VERDICTS = {
  "Keep as reminder": "current",
  "Dismiss": "archived",
};

const DISPOSITIONS = {
  "Keep as reminder": "accepted",
};

const ATTENTION_LOG = "system/logs/attention.jsonl";
const TRIAGE_LOG = "system/logs/triage.jsonl";
const DISPOSITION_LOG = "system/logs/disposition.jsonl";

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function durationMinutes(start, end) {
  if (!start || !end) return null;
  const t0 = Date.parse(start);
  const t1 = Date.parse(end);
  if (!Number.isFinite(t0) || !Number.isFinite(t1) || t1 < t0) return null;
  return Math.round(((t1 - t0) / 60000) * 10) / 10;
}

function frontmatterDate(fm, key) {
  const value = fm[key];
  if (!value) return "";
  if (value instanceof Date) return value.toISOString();
  return String(value);
}

async function ensureFolder(app, folder) {
  const parts = folder.split("/");
  let cur = "";
  for (const part of parts) {
    cur = cur ? cur + "/" + part : part;
    if (!(await app.vault.adapter.exists(cur))) {
      await app.vault.createFolder(cur);
    }
  }
}

async function appendJsonl(app, path, row) {
  await ensureFolder(app, "system/logs");
  const line = JSON.stringify(row) + "\n";
  const exists = await app.vault.adapter.exists(path);
  const current = exists ? await app.vault.adapter.read(path) : "";
  await app.vault.adapter.write(path, current + line);
}

async function openInbox(app) {
  const inbox = app.vault.getAbstractFileByPath("spaces/inbox.md");
  if (inbox) {
    await app.workspace.getLeaf(false).openFile(inbox);
  }
}

async function entry(params, settings = {}) {
  const { Notice } = params.obsidian;
  const app = params.app || globalThis.app;

  const file = app.workspace.getActiveFile();
  if (!file) {
    new Notice("No active note — open the inbox card first.", 6000);
    return;
  }
  if (!file.path.startsWith("inbox/")) {
    new Notice("Not an inbox card (" + file.path + ") — only notes under inbox/ resolve here.", 8000);
    return;
  }

  const labels = Object.keys(VERDICTS);
  const configuredOutcome = String(settings.Outcome || "").trim();
  const verdict = labels.includes(configuredOutcome)
    ? configuredOutcome
    : await params.quickAddApi.suggester(labels, labels);
  if (!verdict) {
    new Notice("No verdict chosen.", 4000);
    return;
  }

  const lifecycle = VERDICTS[verdict];
  const today = todayIsoDate();
  const resolvedAt = nowIso();
  let attentionRow = null;
  let triageRow = null;
  let dispositionRow = null;
  try {
    await app.fileManager.processFrontMatter(file, (fm) => {
      const openedAt = frontmatterDate(fm, "attention_opened_at")
        || frontmatterDate(fm, "opened_at")
        || frontmatterDate(fm, "created");
      attentionRow = {
        timestamp: resolvedAt,
        event: "inbox_card_resolved",
        path: file.path,
        card_type: fm.type || "",
        lane: fm.lane || fm.assignee || "unknown",
        task_id: fm.task_id || "",
        outcome: verdict,
        lifecycle_from: fm.lifecycle || "",
        lifecycle_to: lifecycle,
        opened_at: openedAt,
        resolved_at: resolvedAt,
        duration_minutes: durationMinutes(openedAt, resolvedAt),
      };
      triageRow = {
        timestamp: resolvedAt,
        event: "inbox_card_resolved",
        path: file.path,
        card_type: fm.type || "",
        lane: fm.lane || fm.assignee || "unknown",
        task_id: fm.task_id || "",
        outcome: verdict,
        lifecycle_from: fm.lifecycle || "",
        lifecycle_to: lifecycle,
        source: "quickadd.resolve-inbox-card",
      };
      if ((fm.type || "") === "work-prompt" && fm.task_id && DISPOSITIONS[verdict]) {
        dispositionRow = {
          timestamp: resolvedAt,
          event: "work_prompt_reviewed",
          path: file.path,
          lane: fm.lane || fm.assignee || "unknown",
          task_id: fm.task_id || "",
          disposition: DISPOSITIONS[verdict],
          outcome: verdict,
          lifecycle_from: fm.lifecycle || "",
          lifecycle_to: lifecycle,
          agent_recommendation: fm.agent_recommendation || "",
          source: "quickadd.resolve-inbox-card",
        };
      }
      fm.lifecycle = lifecycle;
      fm.resolved = today;
    });
    if (attentionRow) {
      await appendJsonl(app, ATTENTION_LOG, attentionRow);
    }
    if (triageRow) {
      await appendJsonl(app, TRIAGE_LOG, triageRow);
    }
    if (dispositionRow) {
      await appendJsonl(app, DISPOSITION_LOG, dispositionRow);
    }
    if (verdict === "Dismiss") {
      try {
        await openInbox(app);
      } catch (e) {
        // Dismissal is complete even if Obsidian refuses to switch panes.
      }
    }
    new Notice("✓ Resolved " + file.basename + " → lifecycle: " + lifecycle + ", resolved: " + today + ".", 6000);
  } catch (e) {
    new Notice(("Resolve failed: " + e.message).slice(0, 250), 10000);
  }
}

module.exports = {
  entry,
  settings: {
    name: "Memoria: resolve inbox card",
    author: "Memoria",
    options: {
      Outcome: {
        type: "text",
        defaultValue: "",
        placeholder: "Keep as reminder | Dismiss",
      },
    },
  },
};
