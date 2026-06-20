const { ItemView, Plugin } = require("obsidian");

const VIEW_TYPE = "memoria-inspector-view";
const BOARD_STATE = "system/logs/board-state.jsonl";
const AUDIT_LOG = "system/logs/audit.jsonl";
const LINT_VERDICT_PREFIX = "system/metrics/lint-verdict-";
const REFRESH_INTERVAL_MS = 60000;

module.exports = class MemoriaInspectorPlugin extends Plugin {
  async onload() {
    this.registerView(
      VIEW_TYPE,
      (leaf) => new MemoriaInspectorView(leaf, this.app),
    );
    this.addRibbonIcon("activity", "Open Memoria Inspector", () => {
      this.activateView();
    });
    this.addCommand({
      id: "open-memoria-inspector",
      name: "Open Memoria Inspector",
      callback: () => this.activateView(),
    });
    this.registerInterval(
      window.setInterval(() => this.refreshOpenViews(), REFRESH_INTERVAL_MS),
    );
  }

  async activateView() {
    const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE);
    const leaf = leaves[0] ?? this.app.workspace.getRightLeaf(false);
    if (!leaf) return;
    await leaf.setViewState({ type: VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  refreshOpenViews() {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE)) {
      if (leaf.view && typeof leaf.view.refresh === "function") {
        leaf.view.refresh();
      }
    }
  }
};

class MemoriaInspectorView extends ItemView {
  constructor(leaf, app) {
    super(leaf);
    this.app = app;
  }

  getViewType() {
    return VIEW_TYPE;
  }

  getDisplayText() {
    return "Memoria Inspector";
  }

  getIcon() {
    return "activity";
  }

  async onOpen() {
    await this.refresh();
  }

  async refresh() {
    const root = this.containerEl.children[1];
    root.empty();
    root.addClass("memoria-inspector");

    const header = root.createDiv({ cls: "memoria-inspector__header" });
    header.createEl("h2", { text: "Memoria Inspector" });
    const refresh = header.createEl("button", {
      cls: "memoria-inspector__refresh",
      text: "Refresh",
      attr: { type: "button" },
    });
    refresh.addEventListener("click", () => this.refresh());

    const [board, audit, verdict] = await Promise.all([
      latestJsonLine(this.app, BOARD_STATE),
      recentJsonLines(this.app, AUDIT_LOG, 5),
      latestLintVerdict(this.app),
    ]);

    renderLintBand(root, verdict);
    renderBoard(root, board);
    renderAudit(root, audit);
  }
}

async function readText(app, path) {
  try {
    return await app.vault.adapter.read(path);
  } catch {
    return "";
  }
}

async function latestJsonLine(app, path) {
  const rows = await recentJsonLines(app, path, 1);
  return rows[0] ?? null;
}

async function recentJsonLines(app, path, limit) {
  const text = await readText(app, path);
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(-limit)
    .map((line) => safeJson(line))
    .filter(Boolean)
    .reverse();
}

async function latestLintVerdict(app) {
  const files = app.vault
    .getFiles()
    .filter((file) => file.path.startsWith(LINT_VERDICT_PREFIX))
    .sort((a, b) => b.path.localeCompare(a.path));
  if (files.length === 0) return null;
  const text = await readText(app, files[0].path);
  const frontmatter = parseFrontmatter(text);
  return {
    path: files[0].path,
    period: frontmatter.period ?? files[0].basename.replace("lint-verdict-", ""),
    verdict: frontmatter.verdict ?? "UNKNOWN",
    finding_count: frontmatter.finding_count ?? null,
    critical_count: frontmatter.critical_count ?? null,
    high_count: frontmatter.high_count ?? null,
    medium_count: frontmatter.medium_count ?? null,
    low_count: frontmatter.low_count ?? null,
  };
}

function parseFrontmatter(text) {
  if (!text.startsWith("---\n")) return {};
  const end = text.indexOf("\n---", 4);
  if (end === -1) return {};
  const data = {};
  for (const line of text.slice(4, end).split("\n")) {
    const match = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!match) continue;
    const value = match[2].trim();
    data[match[1]] = parseScalar(value);
  }
  return data;
}

function parseScalar(value) {
  if (value === "null") return null;
  if (/^-?\d+$/.test(value)) return Number.parseInt(value, 10);
  return value.replace(/^["']|["']$/g, "");
}

function safeJson(line) {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

function renderLintBand(root, verdict) {
  const band = root.createDiv({
    cls: `memoria-inspector__band memoria-inspector__band--${(
      verdict?.verdict ?? "UNKNOWN"
    ).toLowerCase()}`,
  });
  band.createEl("span", { text: "Linter" });
  band.createEl("strong", { text: verdict?.verdict ?? "UNKNOWN" });
  band.createEl("small", {
    text: verdict
      ? `${verdict.period} - ${formatCount(verdict.finding_count, "finding")}`
      : "No lint verdict note found",
  });
}

function renderBoard(root, snapshot) {
  const section = panel(root, "Board counts");
  if (!snapshot || typeof snapshot !== "object") {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No board-state snapshot found.",
    });
    return;
  }

  const totals = snapshot.totals ?? {};
  const grid = section.createDiv({ cls: "memoria-inspector__counts" });
  for (const key of ["running", "ready", "blocked", "review_queue", "retrying"]) {
    const item = grid.createDiv({ cls: "memoria-inspector__count" });
    item.createEl("span", { text: label(key) });
    item.createEl("strong", { text: String(totals[key] ?? 0) });
  }

  const lanes = Object.entries(snapshot.lanes ?? {});
  if (lanes.length > 0) {
    const list = section.createEl("ul", { cls: "memoria-inspector__lanes" });
    for (const [lane, counts] of lanes) {
      list
        .createEl("li")
        .createSpan({
          text: `${lane}: ${counts.ready ?? 0} ready, ${counts.running ?? 0} running, ${counts.blocked ?? 0} blocked`,
        });
    }
  }
}

function renderAudit(root, rows) {
  const section = panel(root, "Recent audit");
  if (rows.length === 0) {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No audit rows found.",
    });
    return;
  }
  const list = section.createEl("ul", { cls: "memoria-inspector__audit" });
  for (const row of rows) {
    const item = list.createEl("li");
    item.createEl("strong", { text: row.decision ?? row.event ?? "event" });
    item.createEl("span", { text: row.action ? ` ${row.action}` : "" });
    item.createEl("small", {
      text: compact(
        [row.timestamp, row.profile, row.path, row.task_id].filter(Boolean).join(" - "),
      ),
    });
  }
}

function panel(root, title) {
  const section = root.createEl("section", { cls: "memoria-inspector__panel" });
  section.createEl("h3", { text: title });
  return section;
}

function label(value) {
  return value.replace(/_/g, " ");
}

function compact(value) {
  if (value.length <= 120) return value;
  return `${value.slice(0, 117)}...`;
}

function formatCount(value, singular) {
  if (value === null || value === undefined) return "count unavailable";
  return `${value} ${Number(value) === 1 ? singular : `${singular}s`}`;
}
