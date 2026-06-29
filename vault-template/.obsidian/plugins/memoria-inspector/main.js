const { ItemView, Plugin } = require("obsidian");

const VIEW_TYPE = "memoria-inspector-view";
const BOARD_STATE = "system/logs/board-state.jsonl";
const AUDIT_LOG = "system/logs/audit.jsonl";
const JOURNAL_PREFIX = "journal/";
const LINT_VERDICT_PREFIX = "system/metrics/lint-verdict-";
const LANE_METRIC_PREFIX = "system/metrics/lane-";
const BOARD_DASHBOARD = "system/dashboards/board-state";
const AUDIT_DASHBOARD = "system/dashboards/audit-log";
const DRIFT_DASHBOARD = "spaces/maintenance#Drift watch";
const FLEET_DASHBOARD = "system/dashboards/fleet-health";
const KNOWLEDGE_DASHBOARD = "knowledge/views/knowledge.base";
const QUEUE_ROOT = ".memoria/queue/";
const QUEUE_PENDING = ".memoria/queue/pending";
const QUEUE_STATES = ["pending", "running", "failed"];
const REFRESH_INTERVAL_MS = 60000;
const GRAPH_PREFIXES = ["catalog/", "knowledge/"];
const GRAPH_TYPES = ["source", "digest", "note", "hub", "project"];

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

    const [board, audit, flags, verdict, laneMetrics, graph, queue] = await Promise.all([
      latestJsonLine(this.app, BOARD_STATE),
      recentJsonLines(this.app, AUDIT_LOG, 5),
      recentIntegrityFlags(this.app),
      latestLintVerdict(this.app),
      latestLaneMetrics(this.app),
      knowledgeGraphSummary(this.app),
      workerQueueSummary(this.app),
    ]);

    renderControls(root, this.app);
    renderQueue(root, queue);
    renderLintBand(root, verdict, this.app);
    renderFlags(root, flags);
    renderGraph(root, graph, this.app);
    renderBoard(root, board, this.app);
    renderAudit(root, audit, this.app);
    renderFleet(root, laneMetrics, this.app);
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

async function latestLaneMetrics(app) {
  const files = app.vault
    .getFiles()
    .filter((file) => file.path.startsWith(LANE_METRIC_PREFIX))
    .sort((a, b) => b.path.localeCompare(a.path));
  const latestByLane = new Map();
  for (const file of files) {
    const frontmatter = parseFrontmatter(await readText(app, file.path));
    const lane = frontmatter.lane;
    if (!lane || latestByLane.has(lane)) continue;
    latestByLane.set(lane, {
      path: file.path,
      lane,
      period: frontmatter.period ?? periodFromName(file.basename),
      trust_score: frontmatter.trust_score ?? null,
      band: frontmatter.band ?? "unknown",
      samples: frontmatter.samples ?? null,
    });
  }
  return Array.from(latestByLane.values()).sort((a, b) => a.lane.localeCompare(b.lane));
}

async function recentIntegrityFlags(app, limit = 5) {
  const rows = [];
  const files = app.vault
    .getFiles()
    .filter((file) => file.path.startsWith(JOURNAL_PREFIX) && file.path.endsWith(".jsonl"))
    .sort((a, b) => a.path.localeCompare(b.path));
  for (const file of files) {
    const text = await readText(app, file.path);
    for (const line of text.split("\n")) {
      const row = safeJson(line.trim());
      if (!row || row.event !== "check-fired" || row.status !== "failed") continue;
      rows.push({ ...row, path: file.path });
    }
  }
  return rows
    .sort((a, b) => String(b.timestamp ?? "").localeCompare(String(a.timestamp ?? "")))
    .slice(0, limit);
}

async function knowledgeGraphSummary(app, limit = 6) {
  const counts = Object.fromEntries(GRAPH_TYPES.map((type) => [type, 0]));
  const nodes = [];
  const graphEdges = [];
  let edgeCount = 0;
  const files = app.vault
    .getFiles()
    .filter(
      (file) =>
        file.extension === "md" &&
        GRAPH_PREFIXES.some((prefix) => file.path.startsWith(prefix)),
    )
    .sort((a, b) => a.path.localeCompare(b.path));
  for (const file of files) {
    const text = await readText(app, file.path);
    const frontmatter = parseFrontmatter(text);
    const type = frontmatter.type;
    if (frontmatter.check_status !== "checked" || !GRAPH_TYPES.includes(type)) continue;
    counts[type] += 1;
    const refs = graphRefs(text);
    edgeCount += refs.length;
    nodes.push({
      path: file.path,
      type,
      title: frontmatter.title ?? file.basename,
    });
    for (const ref of refs) {
      graphEdges.push({
        source: file.path,
        sourceTitle: frontmatter.title ?? file.basename,
        sourceType: type,
        target: graphTargetPath(ref),
      });
    }
  }
  return {
    counts,
    edgeCount,
    graphEdges: graphEdges.slice(0, limit),
    nodes: nodes.slice(0, limit),
    totalNodes: nodes.length,
  };
}

async function workerQueueSummary(app, limit = 5) {
  const counts = Object.fromEntries(QUEUE_STATES.map((state) => [state, 0]));
  const failed = [];
  const files = app.vault
    .getFiles()
    .filter((file) => file.path.startsWith(QUEUE_ROOT) && file.path.endsWith(".json"))
    .sort((a, b) => a.path.localeCompare(b.path));
  for (const file of files) {
    const state = file.path.slice(QUEUE_ROOT.length).split("/")[0];
    if (!QUEUE_STATES.includes(state)) continue;
    counts[state] += 1;
    if (state === "failed") {
      const job = safeJson(await readText(app, file.path)) ?? {};
      failed.push({ ...job, path: file.path });
    }
  }
  return {
    counts,
    failed: failed
      .sort((a, b) =>
        String(b.failed_at ?? b.completed_at ?? b.started_at ?? b.created_at ?? "").localeCompare(
          String(a.failed_at ?? a.completed_at ?? a.started_at ?? a.created_at ?? ""),
        ),
      )
      .slice(0, limit),
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

function graphRefs(text) {
  const frontmatter = frontmatterText(text);
  if (!frontmatter) return [];
  const matches =
    frontmatter.match(/\b(?:catalog|knowledge)\/[A-Za-z0-9._~!$&'()*+,;=:@\/-]+(?:\.md)?/g) ??
    [];
  return Array.from(new Set(matches));
}

function graphTargetPath(ref) {
  if (ref.startsWith("catalog/sources/") && !ref.endsWith(".md")) {
    return `${ref.replace(/\/$/, "")}/source.md`;
  }
  return ref.endsWith(".md") ? ref : `${ref}.md`;
}

function frontmatterText(text) {
  if (!text.startsWith("---\n")) return "";
  const end = text.indexOf("\n---", 4);
  return end === -1 ? "" : text.slice(4, end);
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

function renderLintBand(root, verdict, app) {
  const band = root.createDiv({
    cls: `memoria-inspector__band memoria-inspector__band--${(
      verdict?.verdict ?? "UNKNOWN"
    ).toLowerCase()}`,
  });
  const header = band.createDiv({ cls: "memoria-inspector__band-head" });
  header.createEl("span", { text: "Linter" });
  dashboardButton(header, app, DRIFT_DASHBOARD);
  band.createEl("strong", { text: verdict?.verdict ?? "UNKNOWN" });
  band.createEl("small", {
    text: verdict
      ? `${verdict.period} - ${formatCount(verdict.finding_count, "finding")}`
      : "No lint verdict note found",
  });
}

function renderBoard(root, snapshot, app) {
  const section = panel(root, "Board counts", app, BOARD_DASHBOARD);
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

function renderFlags(root, rows) {
  const section = panel(root, "Integrity flags");
  if (rows.length === 0) {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No failed integrity checks found.",
    });
    return;
  }
  const list = section.createEl("ul", { cls: "memoria-inspector__flags" });
  for (const row of rows) {
    const item = list.createEl("li");
    item.createEl("strong", { text: row.check ?? "check-fired" });
    item.createEl("span", { text: ` ${row.route ?? row.status ?? "failed"}` });
    item.createEl("small", {
      text: compact(
        [row.timestamp, row.target_id, row.reason, row.path].filter(Boolean).join(" - "),
      ),
    });
  }
}

function renderQueue(root, queue) {
  const section = panel(root, "Worker queue");
  const grid = section.createDiv({ cls: "memoria-inspector__counts" });
  for (const state of QUEUE_STATES) {
    const item = grid.createDiv({ cls: "memoria-inspector__count" });
    item.createEl("span", { text: state });
    item.createEl("strong", { text: String(queue.counts[state] ?? 0) });
  }
  if (queue.failed.length === 0) {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No failed worker jobs found.",
    });
    return;
  }
  const list = section.createEl("ul", { cls: "memoria-inspector__flags" });
  for (const job of queue.failed) {
    const item = list.createEl("li");
    item.createEl("strong", { text: job.operation_id ?? job.kind ?? "worker job" });
    item.createEl("span", { text: job.job_id ? ` ${job.job_id}` : "" });
    item.createEl("small", {
      text: compact(
        [job.failed_at, job.error, job.path].filter(Boolean).join(" - "),
      ),
    });
  }
}

function renderGraph(root, graph, app) {
  const section = panel(root, "Knowledge graph", app, KNOWLEDGE_DASHBOARD);
  const grid = section.createDiv({ cls: "memoria-inspector__counts" });
  for (const type of GRAPH_TYPES) {
    const item = grid.createDiv({ cls: "memoria-inspector__count" });
    item.createEl("span", { text: label(type) });
    item.createEl("strong", { text: String(graph.counts[type] ?? 0) });
  }
  section.createEl("small", {
    cls: "memoria-inspector__summary",
    text: `${formatCount(graph.edgeCount, "declared edge")} across ${formatCount(
      graph.totalNodes,
      "checked Concept",
    )}`,
  });
  if (graph.nodes.length === 0) {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No checked graph Concepts found.",
    });
    return;
  }
  const list = section.createEl("ul", { cls: "memoria-inspector__graph" });
  for (const node of graph.nodes) {
    const item = list.createEl("li");
    const labelEl = item.createDiv({ cls: "memoria-inspector__graph-label" });
    labelEl.createEl("strong", { text: node.title });
    labelEl.createEl("span", { text: node.type });
    item.createEl("small", { text: node.path });
    openButton(item, app, node.path);
  }
  if (graph.graphEdges.length > 0) {
    const edgeList = section.createEl("ul", { cls: "memoria-inspector__graph" });
    for (const edge of graph.graphEdges) {
      const item = edgeList.createEl("li");
      const labelEl = item.createDiv({ cls: "memoria-inspector__graph-label" });
      labelEl.createEl("strong", { text: edge.sourceTitle });
      labelEl.createEl("span", { text: `${edge.sourceType} edge` });
      item.createEl("small", { text: `${edge.source} -> ${edge.target}` });
      openButton(item, app, edge.target);
    }
  }
}

function renderAudit(root, rows, app) {
  const section = panel(root, "Recent audit", app, AUDIT_DASHBOARD);
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

function renderFleet(root, metrics, app) {
  const section = panel(root, "Fleet trust", app, FLEET_DASHBOARD);
  if (metrics.length === 0) {
    section.createEl("p", {
      cls: "memoria-inspector__empty",
      text: "No lane metric notes found.",
    });
    return;
  }
  const list = section.createEl("ul", { cls: "memoria-inspector__fleet" });
  for (const metric of metrics) {
    const item = list.createEl("li");
    item.createEl("strong", { text: metric.lane });
    item.createEl("span", { text: ` ${formatScore(metric.trust_score)} (${metric.band})` });
    item.createEl("small", {
      text: compact(
        [metric.period, formatCount(metric.samples, "sample"), metric.path]
          .filter(Boolean)
          .join(" - "),
      ),
    });
  }
}

function renderControls(root, app) {
  const section = panel(root, "Control");
  const actions = section.createDiv({ cls: "memoria-inspector__actions" });
  const status = section.createEl("small", {
    cls: "memoria-inspector__status",
    text: "Worker actions enqueue jobs only.",
  });
  const checkEvidence = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check evidence",
    attr: { type: "button" },
  });
  const checkQuotes = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check quotes",
    attr: { type: "button" },
  });
  const checkClaims = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check claims",
    attr: { type: "button" },
  });
  const checkProvenance = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check provenance",
    attr: { type: "button" },
  });
  const checkLinks = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check links",
    attr: { type: "button" },
  });
  const checkSources = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Check sources",
    attr: { type: "button" },
  });
  const refreshProjections = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Refresh projections",
    attr: { type: "button" },
  });
  const rebuildSearch = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Rebuild search",
    attr: { type: "button" },
  });
  const analyzeGaps = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Analyze gaps",
    attr: { type: "button" },
  });
  const projectPath = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Project path",
      "aria-label": "Project path",
    },
  });
  const analyzeProject = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Analyze project",
    attr: { type: "button" },
  });
  const renderProjectCanvas = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Render canvas",
    attr: { type: "button" },
  });
  const askQuery = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Ask query",
      "aria-label": "Ask query",
    },
  });
  const answerQuery = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Ask query",
    attr: { type: "button" },
  });
  const captureUrl = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "url",
      placeholder: "Source URL",
      "aria-label": "Source URL",
    },
  });
  const captureUrlButton = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Capture URL",
    attr: { type: "button" },
  });
  const copiSource = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Co-PI source id",
      "aria-label": "Co-PI source id",
    },
  });
  const copiResponse = section.createEl("textarea", {
    cls: "memoria-inspector__input",
    attr: {
      placeholder: "Co-PI interview takeaway",
      "aria-label": "Co-PI interview takeaway",
      rows: "3",
    },
  });
  const recordInterview = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Record interview",
    attr: { type: "button" },
  });
  const hubTopics = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Hub topics",
      "aria-label": "Hub topics",
    },
  });
  const compileDigest = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Compile digest",
    attr: { type: "button" },
  });
  const digestPath = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Digest path",
      "aria-label": "Digest path",
    },
  });
  const candidateJson = section.createEl("textarea", {
    cls: "memoria-inspector__input",
    attr: {
      placeholder: "Note candidate JSON array",
      "aria-label": "Note candidate JSON array",
      rows: "3",
    },
  });
  const proposeNotes = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Propose notes",
    attr: { type: "button" },
  });
  const noteCandidate = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Note candidate path",
      "aria-label": "Note candidate path",
    },
  });
  const acceptNote = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Accept note",
    attr: { type: "button" },
  });
  const rejectNote = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Reject note",
    attr: { type: "button" },
  });
  const linkSource = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Link source note path",
      "aria-label": "Link source note path",
    },
  });
  const linkTarget = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Link target path",
      "aria-label": "Link target path",
    },
  });
  const supportsNote = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Supports",
    attr: { type: "button" },
  });
  const contradictsNote = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Contradicts",
    attr: { type: "button" },
  });
  const extendsNote = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Extends",
    attr: { type: "button" },
  });
  const rollbackTarget = section.createEl("input", {
    cls: "memoria-inspector__input",
    attr: {
      type: "text",
      placeholder: "Attention or trace target path",
      "aria-label": "Attention or trace target path",
    },
  });
  const includeTargetLabel = section.createEl("label", {
    cls: "memoria-inspector__check",
  });
  const includeTarget = includeTargetLabel.createEl("input", {
    attr: { type: "checkbox" },
  });
  includeTargetLabel.createSpan({ text: "Include target" });
  const rollbackTrace = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Rollback trace",
    attr: { type: "button" },
  });
  const acknowledgeAttention = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Acknowledge",
    attr: { type: "button" },
  });
  const resolveAttention = actions.createEl("button", {
    cls: "memoria-inspector__action",
    text: "Resolve",
    attr: { type: "button" },
  });
  checkEvidence.addEventListener("click", async () => {
    checkEvidence.disabled = true;
    try {
      const path = await enqueueOperation(app, "integrity-evidence-check", { shadow: false });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkEvidence.disabled = false;
    }
  });
  checkQuotes.addEventListener("click", async () => {
    checkQuotes.disabled = true;
    try {
      const path = await enqueueOperation(app, "integrity-quote-anchor-check", { shadow: false });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkQuotes.disabled = false;
    }
  });
  checkClaims.addEventListener("click", async () => {
    checkClaims.disabled = true;
    try {
      const path = await enqueueOperation(app, "integrity-claim-quote-check", { shadow: false });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkClaims.disabled = false;
    }
  });
  checkProvenance.addEventListener("click", async () => {
    checkProvenance.disabled = true;
    try {
      const path = await enqueueOperation(app, "integrity-provenance-checkpoint", {
        shadow: false,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkProvenance.disabled = false;
    }
  });
  checkLinks.addEventListener("click", async () => {
    checkLinks.disabled = true;
    try {
      const path = await enqueueOperation(app, "integrity-link-target-check", { shadow: false });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkLinks.disabled = false;
    }
  });
  checkSources.addEventListener("click", async () => {
    checkSources.disabled = true;
    try {
      const path = await enqueueOperation(app, "check-source-metadata", { shadow: false });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      checkSources.disabled = false;
    }
  });
  refreshProjections.addEventListener("click", async () => {
    refreshProjections.disabled = true;
    try {
      const path = await enqueueOperation(app, "regenerate-tracked-projections");
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      refreshProjections.disabled = false;
    }
  });
  rebuildSearch.addEventListener("click", async () => {
    rebuildSearch.disabled = true;
    try {
      const path = await enqueueOperation(app, "rebuild-checked-qmd-source");
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      rebuildSearch.disabled = false;
    }
  });
  analyzeGaps.addEventListener("click", async () => {
    analyzeGaps.disabled = true;
    try {
      const path = await enqueueOperation(app, "analyze-gaps");
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      analyzeGaps.disabled = false;
    }
  });
  analyzeProject.addEventListener("click", async () => {
    const project = projectPath.value.trim();
    if (!project) {
      status.setText("Enter a project path.");
      return;
    }
    analyzeProject.disabled = true;
    try {
      const path = await enqueueOperation(app, "analyze-project-argument", {
        project_path: project,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      analyzeProject.disabled = false;
    }
  });
  renderProjectCanvas.addEventListener("click", async () => {
    const project = projectPath.value.trim();
    if (!project) {
      status.setText("Enter a project path.");
      return;
    }
    renderProjectCanvas.disabled = true;
    try {
      const path = await enqueueOperation(app, "render-project-argument-canvas", {
        project_path: project,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      renderProjectCanvas.disabled = false;
    }
  });
  answerQuery.addEventListener("click", async () => {
    const query = askQuery.value.trim();
    if (!query) {
      status.setText("Enter an Ask query.");
      return;
    }
    answerQuery.disabled = true;
    try {
      const path = await enqueueOperation(app, "answer-query", { query });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      answerQuery.disabled = false;
    }
  });
  captureUrlButton.addEventListener("click", async () => {
    const url = captureUrl.value.trim();
    if (!url) {
      status.setText("Enter a source URL.");
      return;
    }
    captureUrlButton.disabled = true;
    try {
      const path = await enqueueOperation(app, "capture-url-source", { url });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      captureUrlButton.disabled = false;
    }
  });
  recordInterview.addEventListener("click", async () => {
    const sourceId = copiSource.value.trim();
    const response = copiResponse.value.trim();
    if (!sourceId || !response) {
      status.setText("Enter a source id and interview takeaway.");
      return;
    }
    recordInterview.disabled = true;
    try {
      const path = await enqueueOperation(app, "record-copi-interview", {
        source_id: sourceId,
        response,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      recordInterview.disabled = false;
    }
  });
  compileDigest.addEventListener("click", async () => {
    const sourceId = copiSource.value.trim();
    const topics = hubTopics.value
      .split(",")
      .map((topic) => topic.trim())
      .filter(Boolean);
    if (!sourceId || topics.length === 0) {
      status.setText("Enter a source id and hub topics.");
      return;
    }
    compileDigest.disabled = true;
    try {
      const path = await enqueueOperation(app, "compile-source-digest", {
        source_id: sourceId,
        hub_topics: topics,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      compileDigest.disabled = false;
    }
  });
  proposeNotes.addEventListener("click", async () => {
    const digest = digestPath.value.trim();
    const candidates = safeJson(candidateJson.value.trim());
    if (!digest || !Array.isArray(candidates)) {
      status.setText("Enter a digest path and note candidate JSON array.");
      return;
    }
    proposeNotes.disabled = true;
    try {
      const path = await enqueueOperation(app, "propose-note-candidates", {
        digest_path: digest,
        candidates,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      proposeNotes.disabled = false;
    }
  });
  acceptNote.addEventListener("click", async () => {
    await enqueueNoteCuration(app, noteCandidate, status, acceptNote, "accepted");
  });
  rejectNote.addEventListener("click", async () => {
    await enqueueNoteCuration(app, noteCandidate, status, rejectNote, "rejected");
  });
  supportsNote.addEventListener("click", async () => {
    await enqueueNoteLink(app, linkSource, linkTarget, status, supportsNote, "supports");
  });
  contradictsNote.addEventListener("click", async () => {
    await enqueueNoteLink(app, linkSource, linkTarget, status, contradictsNote, "contradicts");
  });
  extendsNote.addEventListener("click", async () => {
    await enqueueNoteLink(app, linkSource, linkTarget, status, extendsNote, "extends");
  });
  rollbackTrace.addEventListener("click", async () => {
    const target = rollbackTarget.value.trim();
    if (!target) {
      status.setText("Enter a trace target path.");
      return;
    }
    rollbackTrace.disabled = true;
    try {
      const path = await enqueueOperation(app, "cascade-rollback", {
        target_id: target,
        reason: "pi-requested-rollback",
        include_target: includeTarget.checked,
      });
      status.setText(`Queued ${path}`);
    } catch (error) {
      status.setText(error instanceof Error ? error.message : String(error));
    } finally {
      rollbackTrace.disabled = false;
    }
  });
  acknowledgeAttention.addEventListener("click", async () => {
    await enqueueAttention(app, rollbackTarget, status, acknowledgeAttention, "acknowledge-attention");
  });
  resolveAttention.addEventListener("click", async () => {
    await enqueueAttention(app, rollbackTarget, status, resolveAttention, "resolve-attention");
  });
}

async function enqueueNoteCuration(app, noteInput, status, button, decision) {
  const notePath = noteInput.value.trim();
  if (!notePath) {
    status.setText("Enter a note candidate path.");
    return;
  }
  button.disabled = true;
  try {
    const path = await enqueueOperation(app, "curate-note-candidate", {
      note_path: notePath,
      status: decision,
      reason: "pi-note-curation",
    });
    status.setText(`Queued ${path}`);
  } catch (error) {
    status.setText(error instanceof Error ? error.message : String(error));
  } finally {
    button.disabled = false;
  }
}

async function enqueueNoteLink(app, sourceInput, targetInput, status, button, linkType) {
  const sourceNotePath = sourceInput.value.trim();
  const targetPath = targetInput.value.trim();
  if (!sourceNotePath || !targetPath) {
    status.setText("Enter source and target note paths.");
    return;
  }
  button.disabled = true;
  try {
    const path = await enqueueOperation(app, "curate-note-link", {
      source_note_path: sourceNotePath,
      target_path: targetPath,
      link_type: linkType,
      reason: "pi-note-link",
    });
    status.setText(`Queued ${path}`);
  } catch (error) {
    status.setText(error instanceof Error ? error.message : String(error));
  } finally {
    button.disabled = false;
  }
}

async function enqueueAttention(app, targetInput, status, button, operationId) {
  const target = targetInput.value.trim();
  if (!target) {
    status.setText("Enter an attention target path.");
    return;
  }
  button.disabled = true;
  try {
    const path = await enqueueOperation(app, operationId, {
      target_id: target,
      reason: "pi-attention-decision",
    });
    status.setText(`Queued ${path}`);
  } catch (error) {
    status.setText(error instanceof Error ? error.message : String(error));
  } finally {
    button.disabled = false;
  }
}

async function enqueueOperation(app, operationId, payload = {}) {
  const stamp = new Date().toISOString().replace(/[^0-9A-Za-z_-]/g, "-");
  const suffix = Math.random().toString(16).slice(2, 8);
  const jobId = `${operationId}-${stamp}-${suffix}`;
  const path = `${QUEUE_PENDING}/${jobId}.json`;
  if (!path.startsWith(QUEUE_PENDING)) throw new Error("worker queue path rejected");
  const job = {
    job_id: jobId,
    kind: "operation",
    status: "pending",
    created_at: new Date().toISOString(),
    operation_id: operationId,
    payload,
    source: "memoria-inspector",
  };
  await app.vault.adapter.write(path, `${JSON.stringify(job, null, 2)}\n`);
  return path;
}

function panel(root, title, app, dashboard) {
  const section = root.createEl("section", { cls: "memoria-inspector__panel" });
  const header = section.createDiv({ cls: "memoria-inspector__panel-header" });
  header.createEl("h3", { text: title });
  if (dashboard) dashboardButton(header, app, dashboard);
  return section;
}

function dashboardButton(parent, app, dashboard) {
  openButton(parent, app, dashboard);
}

function openButton(parent, app, target) {
  const button = parent.createEl("button", {
    cls: "memoria-inspector__link",
    text: "Open",
    attr: { type: "button" },
  });
  button.addEventListener("click", () => {
    app.workspace.openLinkText(target, "", false);
  });
}

function periodFromName(name) {
  const match = name.match(/(\d{4}-W\d{2})$/);
  return match ? match[1] : name;
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

function formatScore(value) {
  if (value === null || value === undefined) return "score unavailable";
  return `${value}/100`;
}
