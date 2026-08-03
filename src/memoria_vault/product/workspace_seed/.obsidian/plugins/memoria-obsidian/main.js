// Obsidian-compatible CommonJS; hand-authored (no build step).
const {
  AbstractInputSuggest,
  ItemView,
  Modal,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  requestUrl,
} = require("obsidian");
const { execFile } = require("child_process");
const { sanitizeItemId, validateEvent } = require("./schema");
const { buildRelateOperation } = require("./relate");
const {
  HANDSHAKE_TIMEOUT_MS,
  buildHandshakeArgv,
  classifySpawnError,
  createRespawnGate,
  parseHandshake,
} = require("./handshake");
const { computeNextPollDelay, computePill, formatAsOf } = require("./pill");
const {
  collapseAnalysis,
  materialize,
  moveSelection,
  renderBlock,
  renderView,
  sortCards,
} = require("./viewspec");

const DEFAULT_SETTINGS = {
  enabled: false,
  engineCommand: "memoria",
  defaultProjectId: "",
  retentionDays: 30,
  showPrivacyPreview: true,
  queuedEvents: [],
};
const EMPTY_ENGINE = { port: 0, token: "", bootId: "", engineVersion: "", pid: 0 };
const STATUS_PATH = "/v1/status";
const ATTENTION_VIEW_PATH = "/v1/views/attention";
const OPERATION_PATH = "/operation/run";
const VIEW_TYPE_ATTENTION = "memoria-attention";
const VIEW_TYPE_EVIDENCE_REVIEW = "memoria-evidence-review";
const EVIDENCE_REVIEW_VIEW_PATH = "/v1/views/evidence-review";
// "" is the unfiltered queue; the other three are the engine's whole routing
// vocabulary (`EVIDENCE_REVIEW_ROUTING_TYPES`), which the view refuses outside.
const EVIDENCE_ROUTING_FACETS = ["", "implicit", "multi-hop", "incomplete"];

module.exports = class MemoriaObsidianPlugin extends Plugin {
  async onload() {
    // No `|| {}`: Object.assign already ignores the null a never-saved vault
    // returns, so the guard could not change an outcome for any input.
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.sessionId = "";
    this.sessionStartedAt = 0;
    this.statusBar = this.addStatusBarItem();
    this.engine = Object.assign({}, EMPTY_ENGINE);
    this.connectionStatus = "stale";
    this.openCount = 0;
    this.lastPollAt = 0;
    this.missingCredential = "";
    this.linkRelations = [];
    this.lastHandshakeError = "";
    this.pillState = "";
    this.respawnGate = createRespawnGate();
    this._execFile = execFile;
    this.pollTimer = null;
    this.register(() => clearTimeout(this.pollTimer));
    if (typeof window !== "undefined" && this.registerDomEvent) {
      this.registerDomEvent(window, "focus", () => this.schedulePoll());
      this.registerDomEvent(window, "blur", () => this.schedulePoll());
      this.registerDomEvent(this.statusBar, "click", () => this.onPillClick());
    }
    if (this.app.workspace.onLayoutReady) {
      this.app.workspace.onLayoutReady(() => this.poll());
    } else {
      this.schedulePoll();
    }
    this.addSettingTab(new MemoriaSettingTab(this.app, this));
    this.registerView(VIEW_TYPE_ATTENTION, (leaf) => new AttentionView(leaf, this));
    this.addCommand({
      id: "open-attention",
      name: "Memoria: Open attention pane",
      callback: () => this.activateAttentionView(),
    });
    this.registerView(
      VIEW_TYPE_EVIDENCE_REVIEW,
      (leaf) => new EvidenceReviewView(leaf, this),
    );
    this.addCommand({
      id: "open-evidence-review",
      name: "Memoria: Open evidence review",
      callback: () => this.activateEvidenceReviewView(),
    });
    this.addCommand({
      id: "relate",
      name: "Memoria: Relate…",
      callback: () => new RelateModal(this.app, this).open(),
    });
    this.addCommand({
      id: "connect",
      name: "Memoria: Connect to local server",
      callback: () => this.connect(),
    });
    this.addCommand({
      id: "show-attention",
      name: "Memoria: Show attention count",
      callback: () => this.showAttention(),
    });
    this.addCommand({
      id: "show-active-concept",
      name: "Memoria: Show active Concept",
      callback: () => this.showActiveConcept(),
    });
    this.addCommand({
      id: "queue-operation",
      name: "Memoria: Queue operation",
      callback: () => new OperationModal(this.app, this).open(),
    });
    this.addCommand({
      id: "start-session",
      name: "Memoria: Start data collection session",
      callback: () => this.startSession(),
    });
    this.addCommand({
      id: "stop-session",
      name: "Memoria: Stop data collection session",
      callback: () => this.stopSession(),
    });
    this.addCommand({
      id: "record-disposition",
      name: "Memoria: Record disposition",
      callback: () => new EventModal(this.app, this, "disposition.recorded").open(),
    });
    this.addCommand({
      id: "record-fallback",
      name: "Memoria: Record fallback",
      callback: () => new EventModal(this.app, this, "fallback.recorded").open(),
    });
    this.addCommand({
      id: "flush-events",
      name: "Memoria: Flush queued events",
      callback: () => this.flushQueuedEvents(),
    });
    this.addCommand({
      id: "delete-events",
      name: "Memoria: Delete queued events",
      callback: () => this.deleteQueuedEvents(),
    });
    this.forkBadge = "";
    this.addCommand({
      id: "fork-canvas",
      name: "Memoria: Fork canvas to scratch",
      callback: () => this.forkActiveCanvas(),
    });
    this.addCommand({
      id: "graduate-scratch-edges",
      name: "Memoria: Graduate scratch canvas edges",
      callback: () => this.graduateScratchEdges(),
    });
    if (this.app.workspace.on && this.registerEvent) {
      this.registerEvent(
        this.app.workspace.on("active-leaf-change", () => this.updateForkBadge()),
      );
    }
    this.renderPill();
  }

  onunload() {
    this.statusBar = null;
  }

  async saveSettings() {
    await this.saveData(Object.assign({}, this.settings));
  }

  ensureSession() {
    if (!this.sessionId) {
      this.sessionId = randomId();
      this.sessionStartedAt = Date.now();
    }
    return this.sessionId;
  }

  baseEvent(eventType, fields) {
    const event = Object.assign(
      {
        event_id: randomId(),
        event_type: eventType,
        timestamp: new Date().toISOString(),
        session_id: this.ensureSession(),
        surface: "obsidian",
      },
      fields || {},
    );
    if (this.settings.defaultProjectId && !event.project_id) {
      event.project_id = this.settings.defaultProjectId;
    }
    return validateEvent(event);
  }

  async connect() {
    this.respawnGate = createRespawnGate();
    this.engine = Object.assign({}, EMPTY_ENGINE);
    if (!(await this.runHandshake())) {
      new Notice(`Memoria: ${this.connectionStatus.replace("-", " ")}`);
      return;
    }
    await this.poll();
    new Notice(`Memoria connected: engine ${this.engine.engineVersion}`);
    if (this.settings.enabled) {
      await this.recordEvent(
        this.baseEvent("http.connected", { workflow: "connection", outcome: "connected" }),
      );
    }
  }

  async showAttention() {
    const payload = await this.authedJson("/attention");
    const rows = payload.attention || [];
    await this.recordEvent(this.baseEvent("view.opened", { workflow: "evidence-review" }));
    new Notice(`Memoria attention: ${rows.length} item(s)`);
  }

  async showActiveConcept() {
    const file = this.app.workspace.getActiveFile && this.app.workspace.getActiveFile();
    if (!file) {
      new Notice("No active file.");
      return;
    }
    const target = file.path;
    const payload = await this.authedJson(`/concept?target=${encodeURIComponent(target)}`);
    const concept = payload.concept || {};
    await this.recordEvent(
      this.baseEvent("view.opened", {
        workflow: "evidence-review",
        item_type: String(concept.type || "concept"),
        item_id: sanitizeItemId(String(concept.id || target)),
      }),
    );
    new Notice(`Memoria Concept: ${concept.title || target}`);
  }

  async startSession() {
    if (!this.settings.enabled) {
      new Notice("Enable Memoria collection before starting a session.");
      return;
    }
    this.sessionId = randomId();
    this.sessionStartedAt = Date.now();
    await this.recordEvent(this.baseEvent("session.started", { workflow: "session" }));
    this.renderPill();
    new Notice("Memoria data collection started.");
  }

  async stopSession() {
    const duration = this.sessionStartedAt ? Math.max(1, (Date.now() - this.sessionStartedAt) / 1000) : 1;
    await this.recordEvent(
      this.baseEvent("session.stopped", {
        workflow: "session",
        outcome: "stopped",
        duration_s: duration,
      }),
    );
    this.sessionStartedAt = 0;
    this.renderPill();
    new Notice("Memoria data collection stopped.");
  }

  activeCanvasMatch(pattern) {
    const file = this.app.workspace.getActiveFile && this.app.workspace.getActiveFile();
    if (!file) {
      return null;
    }
    const match = file.path.match(pattern);
    return match ? { file, match } : null;
  }

  async forkActiveCanvas() {
    const active = this.activeCanvasMatch(/^projects\/([^/]+)\/argument\.canvas$/);
    if (!active) {
      new Notice("Open a generated argument.canvas to fork it.");
      return;
    }
    new ForkNameModal(this.app, async (name) => {
      await this.enqueueNamedOperation("fork-project-canvas", {
        project_path: `projects/${active.match[1]}/project.md`,
        name: name || "scratch",
      });
    }).open();
  }

  async forkStatusForActiveScratch() {
    const active = this.activeCanvasMatch(/^projects\/([^/]+)\/scratch-[^/]+\.canvas$/);
    if (!active) {
      return null;
    }
    const projectPath = `projects/${active.match[1]}/project.md`;
    const payload = await this.authedJson(
      `/project/canvas/forks?project_path=${encodeURIComponent(projectPath)}`,
    );
    const forks = (payload.canvas_forks && payload.canvas_forks.forks) || [];
    return forks.find((fork) => fork.path === active.file.path) || null;
  }

  async updateForkBadge() {
    try {
      const fork = await this.forkStatusForActiveScratch();
      if (!fork) {
        this.forkBadge = "";
      } else if (fork.error) {
        this.forkBadge = "Memoria fork: unreadable";
      } else {
        this.forkBadge = fork.diff_count
          ? `Memoria fork: ${fork.diff_count} edge(s) diverged`
          : "Memoria fork: in sync";
      }
    } catch {
      this.forkBadge = "";
    }
    this.renderPill();
  }

  async graduateScratchEdges() {
    const fork = await this.forkStatusForActiveScratch();
    if (!fork) {
      new Notice("Open a scratch-*.canvas to graduate its edges.");
      return;
    }
    if (fork.error) {
      new Notice("Memoria could not read this scratch canvas.");
      return;
    }
    const added = fork.added || [];
    for (const edge of added) {
      await this.postOperation(
        "curate-note-link",
        {
          source_note_path: edge.source_note_path,
          link_type: edge.link_type,
          target_path: edge.target_path,
          // The *request's* reason, which the journal records — never the edge
          // warrant, which is the PI's own license text for the inference.
          reason: `graduated from ${fork.path}`,
        },
        `graduate:${fork.path}:${edge.source_note_path}:${edge.link_type}:${edge.target_path}`,
      );
    }
    const skipped = (fork.unresolved || []).length;
    new Notice(
      `Memoria queued ${added.length} link edge(s); skipped ${skipped} unresolved.`,
    );
  }

  async recordDisposition(fields) {
    await this.recordEvent(
      this.baseEvent(
        "disposition.recorded",
        Object.assign({ workflow: "gap", decision: "defer", reason_code: "other" }, fields || {}),
      ),
    );
    new Notice("Memoria disposition recorded.");
  }

  async recordFallback(fields) {
    await this.recordEvent(
      this.baseEvent(
        "fallback.recorded",
        Object.assign({ workflow: "ask", outcome: "fallback", reason_code: "other" }, fields || {}),
      ),
    );
    new Notice("Memoria fallback recorded.");
  }

  async recordEvent(event) {
    if (!this.settings.enabled) {
      return;
    }
    try {
      if (this.settings.showPrivacyPreview && !this.previewShown) {
        this.previewShown = true;
        new Notice(`Memoria event preview: ${event.event_type}`);
      }
      await this.postOperation("empirical-event-record", event, `empirical-event:${event.event_id}`);
      this.renderPill();
    } catch (error) {
      await this.queueEvent(event);
      this.renderPill();
      new Notice(`Memoria event queued: ${error.message}`);
    }
  }

  async queueEvent(event) {
    this.settings.queuedEvents = this.settings.queuedEvents || [];
    this.settings.queuedEvents.push({ event, queued_at: new Date().toISOString() });
    await this.pruneQueuedEvents();
    await this.saveSettings();
  }

  async flushQueuedEvents() {
    const queued = [...(this.settings.queuedEvents || [])];
    const remaining = [];
    for (const item of queued) {
      try {
        await this.postOperation(
          "empirical-event-record",
          item.event,
          `empirical-event:${item.event.event_id}`,
        );
      } catch {
        remaining.push(item);
      }
    }
    this.settings.queuedEvents = remaining;
    await this.saveSettings();
    this.renderPill();
    new Notice(`Memoria flushed ${queued.length - remaining.length} event(s).`);
  }

  async deleteQueuedEvents() {
    this.settings.queuedEvents = [];
    await this.saveSettings();
    this.renderPill();
    new Notice("Memoria queued events deleted.");
  }

  async pruneQueuedEvents() {
    const maxAgeMs = Math.max(1, Number(this.settings.retentionDays || 30)) * 24 * 60 * 60 * 1000;
    const cutoff = Date.now() - maxAgeMs;
    this.settings.queuedEvents = (this.settings.queuedEvents || []).filter((item) => {
      const queuedAt = Date.parse(item.queued_at || "");
      return Number.isNaN(queuedAt) || queuedAt >= cutoff;
    });
  }

  vaultPath() {
    const adapter = this.app.vault.adapter || {};
    if (typeof adapter.getBasePath === "function") {
      return adapter.getBasePath();
    }
    return adapter.basePath || "";
  }

  execEngine(command, args) {
    return new Promise((resolve, reject) => {
      this._execFile(command, args, { timeout: HANDSHAKE_TIMEOUT_MS }, (error, stdout, stderr) => {
        if (error) {
          error.stderr = String(stderr || "");
          reject(error);
        } else {
          resolve(String(stdout || ""));
        }
      });
    });
  }

  async runHandshake() {
    if (!this.respawnGate.tryAcquire()) {
      this.connectionStatus = "server-down";
      this.renderPill();
      return false;
    }
    const { command, args } = buildHandshakeArgv(this.settings.engineCommand, this.vaultPath());
    try {
      this.engine = parseHandshake(await this.execEngine(command, args));
      this.connectionStatus = "connected";
      this.renderPill();
      return true;
    } catch (error) {
      this.lastHandshakeError = String((error && error.stderr) || error.message || error);
      if (classifySpawnError(error) === "engine-missing") {
        this.connectionStatus = "engine-missing";
      } else {
        this.connectionStatus = this.respawnGate.exhausted() ? "server-down" : "stale";
      }
      this.renderPill();
      return false;
    }
  }

  async ensureHandshake() {
    if (this.engine.port) {
      return true;
    }
    return this.runHandshake();
  }

  rawRequest(method, path, body) {
    const options = {
      url: `http://127.0.0.1:${this.engine.port}${path}`,
      method,
      headers: { Authorization: `Bearer ${this.engine.token}` },
      throw: false,
    };
    if (body !== undefined) {
      options.contentType = "application/json";
      options.body = JSON.stringify(body);
    }
    return requestUrl(options);
  }

  async probeStatus() {
    try {
      const response = await requestUrl({
        url: `http://127.0.0.1:${this.engine.port}${STATUS_PATH}`,
        method: "GET",
        throw: false,
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }

  async authedRequest(method, path, body) {
    if (!(await this.ensureHandshake())) {
      throw new Error(`memoria: ${this.connectionStatus}`);
    }
    let response = await this.rawRequest(method, path, body);
    if (response.status === 401) {
      this.engine = Object.assign({}, EMPTY_ENGINE);
      if (!(await this.runHandshake())) {
        throw new Error(`memoria: ${this.connectionStatus}`);
      }
      response = await this.rawRequest(method, path, body);
      if (response.status === 401) {
        this.connectionStatus = (await this.probeStatus()) ? "token-invalid" : "server-down";
        this.renderPill();
        throw new Error("memoria: token invalid");
      }
    }
    const payload = response.json;
    if (response.status < 200 || response.status >= 300 || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  }

  async authedJson(path) {
    return this.authedRequest("GET", path);
  }

  async postOperation(operationId, payload, idempotencyKey) {
    return this.authedRequest("POST", OPERATION_PATH, {
      operation_id: operationId,
      payload,
      idempotency_key: idempotencyKey,
    });
  }

  async enqueueNamedOperation(operationId, payload) {
    try {
      const result = await this.postOperation(operationId, payload, "");
      const requestId = String((result.job && result.job.job_id) || "");
      new Notice(`Memoria queued ${operationId}: ${requestId}`);
      await this.recordEvent(
        this.baseEvent("operation.queued", {
          workflow: "operation",
          item_type: "operation",
          item_id: sanitizeItemId(operationId),
          outcome: "queued",
        }),
      );
      return result;
    } catch (error) {
      new Notice(`Memoria enqueue failed: ${error.message}`);
      return null;
    }
  }

  async poll() {
    try {
      const summary = await this.authedJson(`${ATTENTION_VIEW_PATH}?summary=true`);
      this.openCount = Number(summary.open || 0);
      this.lastPollAt = Date.now();
      this.missingCredential = String((summary.missing_required_credentials || [])[0] || "");
      this.linkRelations = Array.isArray(summary.link_relations) ? summary.link_relations : [];
      this.connectionStatus = "connected";
      for (const viewType of [VIEW_TYPE_ATTENTION, VIEW_TYPE_EVIDENCE_REVIEW]) {
        for (const leaf of this.app.workspace.getLeavesOfType
          ? this.app.workspace.getLeavesOfType(viewType)
          : []) {
          if (leaf.view && typeof leaf.view.refresh === "function") {
            leaf.view.refresh();
          }
        }
      }
    } catch {
      if (this.connectionStatus === "connected") {
        this.connectionStatus = "stale";
      }
    }
    this.renderPill();
    this.schedulePoll();
  }

  schedulePoll() {
    clearTimeout(this.pollTimer);
    const isActive =
      typeof document !== "undefined" &&
      typeof document.hasFocus === "function" &&
      document.hasFocus();
    this.pollTimer = setTimeout(() => this.poll(), computeNextPollDelay(isActive));
    if (this.pollTimer && typeof this.pollTimer.unref === "function") {
      this.pollTimer.unref();
    }
  }

  renderPill() {
    if (!this.statusBar) {
      return;
    }
    const pill = computePill({
      connection: this.connectionStatus,
      openCount: this.openCount,
      lastPollAt: this.lastPollAt,
      missingCredential: this.missingCredential,
    });
    this.pillState = pill.state;
    if (typeof this.statusBar.empty === "function") {
      this.statusBar.empty();
      this.statusBar.createEl("span", { cls: `memoria-pill-dot memoria-pill-${pill.tone}` });
      this.statusBar.createEl("span", { cls: "memoria-pill-text", text: pill.text });
      // A second rendered status value, never a replacement for the connection
      // pill: the fork badge answers "has the graph moved under this scratch",
      // which says nothing about whether the engine is reachable.
      if (this.forkBadge) {
        this.statusBar.createEl("span", {
          cls: "memoria-pill-text",
          text: ` · ${this.forkBadge}`,
        });
      }
    } else {
      this.statusBar.setText(pill.text);
    }
  }

  onPillClick() {
    const retry = () => {
      this.respawnGate = createRespawnGate();
      this.runHandshake().then((ok) => {
        if (ok) {
          this.poll();
        }
      });
    };
    if (this.pillState === "connected") {
      this.activateAttentionView();
      return;
    }
    if (this.pillState === "key-needed") {
      new Notice(
        `Memoria: credential needed — run: memoria secrets set ${this.missingCredential}`,
        10000,
      );
      this.activateAttentionView();
      return;
    }
    if (this.pillState === "stale") {
      this.poll();
      return;
    }
    if (this.pillState === "engine-missing") {
      new Notice(
        `Engine missing — the Memoria CLI was not found (tried: \`${this.settings.engineCommand}\`). ` +
          "Install it: pipx install memoria, then click to retry. " +
          "This vault remains fully readable and editable without it.",
        10000,
      );
      retry();
      return;
    }
    if (this.pillState === "server-down") {
      new Notice(
        `Memoria server down after 3 spawn attempts. ${this.lastHandshakeError} — ` +
          `Start it manually: memoria serve --workspace ${this.vaultPath()} — then click to retry.`,
        10000,
      );
      retry();
      return;
    }
    if (this.pillState === "token-invalid") {
      new Notice(
        `Memoria token invalid — restart the server: memoria serve --stop --workspace ${this.vaultPath()}, ` +
          "then click to reconnect.",
        10000,
      );
      this.engine = Object.assign({}, EMPTY_ENGINE);
      this.respawnGate = createRespawnGate();
      this.connectionStatus = "stale";
      this.poll();
    }
  }

  async activateView(viewType) {
    const existing = this.app.workspace.getLeavesOfType
      ? this.app.workspace.getLeavesOfType(viewType)
      : [];
    const leaf =
      existing[0] || (this.app.workspace.getRightLeaf && this.app.workspace.getRightLeaf(false));
    if (!leaf) {
      return;
    }
    await leaf.setViewState({ type: viewType, active: true });
    if (this.app.workspace.revealLeaf) {
      this.app.workspace.revealLeaf(leaf);
    }
  }

  async activateAttentionView() {
    await this.activateView(VIEW_TYPE_ATTENTION);
  }

  async activateEvidenceReviewView() {
    await this.activateView(VIEW_TYPE_EVIDENCE_REVIEW);
  }
};

class AttentionView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.view = null;
    this.cards = [];
    this.extras = [];
    this.selected = 0;
    this.expandedRef = "";
  }

  getViewType() {
    return VIEW_TYPE_ATTENTION;
  }

  getDisplayText() {
    return "Memoria Attention";
  }

  getIcon() {
    return "bell";
  }

  async onOpen() {
    this.contentEl.addClass("memoria-attention");
    this.contentEl.tabIndex = 0;
    this.registerDomEvent(this.contentEl, "keydown", (event) => this.onKey(event));
    this.registerDomEvent(this.contentEl, "click", (event) => this.onClick(event));
    await this.refresh();
  }

  async refresh() {
    try {
      const payload = await this.plugin.authedJson(ATTENTION_VIEW_PATH);
      this.view = payload.view || null;
    } catch (error) {
      this.contentEl.empty();
      this.contentEl.createDiv({
        cls: "memoria-block-unknown",
        text: `Memoria attention unavailable: ${String(error.message || error)}`,
      });
      return;
    }
    const blocks =
      this.view && this.view.version === "view-spec.v1" ? this.view.blocks || [] : [];
    this.cards = sortCards(blocks.filter((block) => block && block.kind === "card"));
    this.extras = blocks.filter((block) => !block || block.kind !== "card");
    this.selected = Math.max(0, Math.min(this.selected, this.cards.length - 1));
    this.render();
  }

  render() {
    const root = this.contentEl;
    root.empty();
    const header = root.createDiv({ cls: "memoria-attention-header" });
    header.createSpan({ text: "ATTENTION" });
    header.createSpan({
      cls: "memoria-attention-age",
      text: `${this.plugin.openCount} open · as of ${formatAsOf(this.plugin.lastPollAt)}`,
    });
    const relateButton = header.createEl("button", { cls: "memoria-action", text: "Relate…" });
    relateButton.addEventListener("click", () =>
      new RelateModal(this.plugin.app, this.plugin).open(),
    );
    if (!this.view || this.view.version !== "view-spec.v1") {
      for (const tree of renderView(this.view)) {
        materialize(tree, root);
      }
      return;
    }
    for (const extra of this.extras) {
      materialize(renderBlock(extra), root);
    }
    this.cards.forEach((card, index) => {
      const row = root.createDiv({
        cls: index === this.selected ? "memoria-row is-selected" : "memoria-row",
      });
      const loudness = String(card.loudness || "");
      row.createSpan({
        cls: loudness
          ? `memoria-loudness-dot memoria-loudness-${loudness}`
          : "memoria-loudness-dot",
      });
      row.createSpan({ cls: "memoria-row-title", text: String(card.title || "") });
      row.createSpan({ cls: "memoria-row-age", text: String(card.age_label || "") });
      row.setAttribute("data-row-index", String(index));
      if (String(card.ref || "") === this.expandedRef) {
        materialize(renderBlock(card), root);
      }
    });
  }

  toggleExpand(index) {
    this.selected = index;
    const ref = String((this.cards[index] || {}).ref || "");
    this.expandedRef = this.expandedRef === ref ? "" : ref;
    this.render();
  }

  onKey(event) {
    if (event.key === "j" || event.key === "k") {
      this.selected = moveSelection(this.cards.length, this.selected, event.key);
      event.preventDefault();
      this.render();
      return;
    }
    if (event.key === "Enter") {
      if (this.cards.length) {
        event.preventDefault();
        this.toggleExpand(this.selected);
      }
    }
  }

  async onClick(event) {
    const actionEl = event.target.closest("button[data-operation-id]");
    if (actionEl) {
      const payload = JSON.parse(actionEl.getAttribute("data-payload") || "{}");
      await this.plugin.enqueueNamedOperation(
        actionEl.getAttribute("data-operation-id"),
        payload,
      );
      await this.refresh();
      return;
    }
    const linkEl = event.target.closest("a[data-ref]");
    if (linkEl) {
      this.plugin.app.workspace.openLinkText(linkEl.getAttribute("data-ref"), "", false);
      return;
    }
    const rowEl = event.target.closest(".memoria-row");
    if (rowEl) {
      this.toggleExpand(Number(rowEl.getAttribute("data-row-index")));
    }
  }
}

// V2 spec §1: only a top-level evidence card is a queue row. An SRD-gap card
// is already a whole normalized U3 card and carries no evidence decision, so it
// is drawn as itself rather than folded into the row/expand machinery.
// `review_kind` is the card's own claim about what it is, written on every
// evidence card and on nothing else; `kind_line` is a display string, so it is
// deliberately not consulted here.
const isEvidenceCard = (block) =>
  Boolean(block) && block.kind === "card" && block.review_kind === "evidence-set";

class EvidenceReviewView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.view = null;
    this.cards = [];
    this.extras = [];
    this.selected = 0;
    this.expandedRef = "";
    this.analysisOpenRef = "";
    this.facetRouting = "";
  }

  getViewType() {
    return VIEW_TYPE_EVIDENCE_REVIEW;
  }

  getDisplayText() {
    return "Memoria Evidence Review";
  }

  getIcon() {
    return "scale";
  }

  async onOpen() {
    this.contentEl.addClass("memoria-evidence-review");
    this.contentEl.tabIndex = 0;
    this.registerDomEvent(this.contentEl, "keydown", (event) => this.onKey(event));
    this.registerDomEvent(this.contentEl, "click", (event) => this.onClick(event));
    await this.refresh();
  }

  viewPath() {
    return this.facetRouting
      ? `${EVIDENCE_REVIEW_VIEW_PATH}?routing_type=${encodeURIComponent(this.facetRouting)}`
      : EVIDENCE_REVIEW_VIEW_PATH;
  }

  async refresh() {
    try {
      const payload = await this.plugin.authedJson(this.viewPath());
      this.view = payload.view || null;
    } catch (error) {
      this.contentEl.empty();
      this.contentEl.createDiv({
        cls: "memoria-block-unknown",
        text: `Memoria evidence review unavailable: ${String(error.message || error)}`,
      });
      return;
    }
    const blocks =
      this.view && this.view.version === "view-spec.v1" ? this.view.blocks || [] : [];
    // Server queue order is the review order (spec §6) — never re-sorted.
    this.cards = blocks.filter(isEvidenceCard);
    this.extras = blocks.filter((block) => !isEvidenceCard(block));
    this.selected = Math.max(0, Math.min(this.selected, this.cards.length - 1));
    this.render();
  }

  render() {
    const root = this.contentEl;
    root.empty();
    const header = root.createDiv({ cls: "memoria-attention-header" });
    header.createSpan({ text: "EVIDENCE REVIEW" });
    const facet = header.createEl("button", {
      cls: "memoria-action",
      text: this.facetRouting ? `routing: ${this.facetRouting}` : "routing: all",
    });
    facet.setAttribute("data-cycle-routing", "1");
    header.createSpan({
      cls: "memoria-attention-age",
      text: `as of ${formatAsOf(this.plugin.lastPollAt)}`,
    });
    if (!this.view || this.view.version !== "view-spec.v1") {
      for (const tree of renderView(this.view)) {
        materialize(tree, root);
      }
      return;
    }
    this.cards.forEach((card, index) => {
      const row = root.createDiv({
        cls: index === this.selected ? "memoria-row is-selected" : "memoria-row",
      });
      row.createSpan({ cls: "memoria-row-title", text: String(card.title || "") });
      row.createSpan({ cls: "memoria-row-age", text: String(card.age_label || "") });
      row.setAttribute("data-row-index", String(index));
      const ref = String(card.ref || "");
      if (ref && ref === this.expandedRef) {
        materialize(collapseAnalysis(renderBlock(card), this.analysisOpenRef === ref), root);
      }
    });
    // The payload puts SRD-gap cards after the evidence queue and they stay
    // there: they are context for the queue, not the work at the top of it.
    for (const extra of this.extras) {
      materialize(renderBlock(extra), root);
    }
  }

  toggleExpand(index) {
    this.selected = index;
    const ref = String((this.cards[index] || {}).ref || "");
    this.expandedRef = this.expandedRef === ref ? "" : ref;
    // Independence-first: analysis re-collapses on every expand (spec §3).
    this.analysisOpenRef = "";
    this.render();
  }

  onKey(event) {
    if (event.key === "j" || event.key === "k") {
      this.selected = moveSelection(this.cards.length, this.selected, event.key);
      event.preventDefault();
      this.render();
      return;
    }
    if (event.key === "Enter" && this.cards.length) {
      event.preventDefault();
      this.toggleExpand(this.selected);
    }
  }

  async onClick(event) {
    const facetEl = event.target.closest("button[data-cycle-routing]");
    if (facetEl) {
      const at = EVIDENCE_ROUTING_FACETS.indexOf(this.facetRouting);
      this.facetRouting = EVIDENCE_ROUTING_FACETS[(at + 1) % EVIDENCE_ROUTING_FACETS.length];
      await this.refresh();
      return;
    }
    const toggleEl = event.target.closest("button[data-toggle-analysis]");
    if (toggleEl) {
      this.analysisOpenRef = this.analysisOpenRef === this.expandedRef ? "" : this.expandedRef;
      this.render();
      return;
    }
    const actionEl = event.target.closest("button[data-operation-id]");
    if (actionEl) {
      const payload = JSON.parse(actionEl.getAttribute("data-payload") || "{}");
      await this.plugin.enqueueNamedOperation(
        actionEl.getAttribute("data-operation-id"),
        payload,
      );
      // Edit records "I will repair the marker", which is work in the draft:
      // the deep link is how that decision reaches the block it is about.
      // No `expandedRef` guard: an action button only exists inside the
      // expanded card, so there is no state in which it is empty here.
      if (payload.decision === "edit") {
        this.plugin.app.workspace.openLinkText(this.expandedRef, "", false);
      }
      await this.refresh();
      return;
    }
    const linkEl = event.target.closest("a[data-ref]");
    if (linkEl) {
      this.plugin.app.workspace.openLinkText(linkEl.getAttribute("data-ref"), "", false);
      return;
    }
    const rowEl = event.target.closest(".memoria-row");
    if (rowEl) {
      this.toggleExpand(Number(rowEl.getAttribute("data-row-index")));
    }
  }
}

class RelateModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
    const active = app.workspace.getActiveFile && app.workspace.getActiveFile();
    this.fromPath = active ? active.path : "";
    this.relation = "";
    this.toPath = "";
    this.warrant = "";
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("memoria-relate-modal");
    contentEl.createEl("h2", { text: "Memoria: Relate" });
    const roster = this.plugin.linkRelations || [];
    if (!roster.length) {
      contentEl.createDiv({
        cls: "memoria-setting-warning",
        text:
          "Relation roster not loaded yet — it comes from the server payload. " +
          "Retry after the next poll (click the status pill).",
      });
    }
    // No `.trim()` on either endpoint: `buildRelateOperation` trims the same
    // two fields on its way to the payload, so trimming here could not change
    // an outcome for any input.
    new Setting(contentEl).setName("From").addText((text) => {
      text.setValue(this.fromPath).onChange((value) => (this.fromPath = value));
      new NotePathSuggest(this.app, text.inputEl, (path) => {
        this.fromPath = path;
        text.setValue(path);
      });
    });
    const segment = contentEl.createDiv({ cls: "memoria-relation-segment" });
    for (const relation of roster) {
      const button = segment.createEl("button", {
        cls: "memoria-relation-option",
        text: relation,
      });
      button.addEventListener("click", () => {
        this.relation = relation;
        for (const sibling of Array.from(segment.children)) {
          sibling.removeClass("is-active");
        }
        button.addClass("is-active");
      });
    }
    new Setting(contentEl).setName("To").addText((text) => {
      text.onChange((value) => (this.toPath = value));
      new NotePathSuggest(this.app, text.inputEl, (path) => {
        this.toPath = path;
        text.setValue(path);
      });
    });
    new Setting(contentEl)
      .setName("Warrant (optional)")
      .setDesc("A `warrant` relation links a license note; Warrant text annotates the selected edge.")
      .addTextArea((text) => text.onChange((value) => (this.warrant = value)));
    new Setting(contentEl).addButton((button) =>
      button.setButtonText("Queue edge").setCta().onClick(async () => {
        let operation;
        try {
          operation = buildRelateOperation({
            fromPath: this.fromPath,
            relation: this.relation,
            toPath: this.toPath,
            warrant: this.warrant,
            roster,
          });
        } catch (error) {
          new Notice(error.message);
          return;
        }
        // A refused enqueue keeps the form standing: the request the PI typed
        // is still the request they want, and retyping it is the cost.
        if (await this.plugin.enqueueNamedOperation(operation.operationId, operation.payload)) {
          this.close();
        }
      }),
    );
  }
}

class NotePathSuggest extends AbstractInputSuggest {
  constructor(app, inputEl, onPick) {
    super(app, inputEl);
    this.onPick = onPick;
  }

  getSuggestions(query) {
    const needle = String(query || "").toLowerCase();
    return this.app.vault
      .getMarkdownFiles()
      .map((file) => file.path)
      .filter((path) => path.toLowerCase().includes(needle))
      .slice(0, 20);
  }

  renderSuggestion(path, el) {
    el.setText(path);
  }

  selectSuggestion(path) {
    this.onPick(path);
    this.close();
  }
}

class MemoriaSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    new Setting(containerEl)
      .setName("Enable collection")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.enabled).onChange(async (value) => {
          this.plugin.settings.enabled = value;
          await this.plugin.saveSettings();
          this.plugin.renderPill();
        }),
      );
    new Setting(containerEl)
      .setName("Engine command")
      .setDesc("Command used to reach the Memoria CLI (e.g. `wsl memoria` on WSL2 hosts).")
      .addText((text) =>
        text.setValue(this.plugin.settings.engineCommand).onChange(async (value) => {
          this.plugin.settings.engineCommand = value.trim() || DEFAULT_SETTINGS.engineCommand;
          await this.plugin.saveSettings();
        }),
      );
    new Setting(containerEl)
      .setName("Default project ID")
      .addText((text) =>
        text.setValue(this.plugin.settings.defaultProjectId).onChange(async (value) => {
          this.plugin.settings.defaultProjectId = value.trim();
          await this.plugin.saveSettings();
        }),
      );
    new Setting(containerEl)
      .setName("Retention days")
      .addText((text) =>
        text.setValue(String(this.plugin.settings.retentionDays)).onChange(async (value) => {
          this.plugin.settings.retentionDays = Number(value) || DEFAULT_SETTINGS.retentionDays;
          await this.plugin.saveSettings();
        }),
      );
  }
}

class EventModal extends Modal {
  constructor(app, plugin, eventType) {
    super(app);
    this.plugin = plugin;
    this.eventType = eventType;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("memoria-event-modal");
    contentEl.createEl("h2", { text: "Memoria event" });
    const fields = { workflow: "gap", decision: "defer", outcome: "fallback", reason_code: "other" };
    new Setting(contentEl)
      .setName("Workflow")
      .addText((text) => text.setValue(fields.workflow).onChange((value) => (fields.workflow = value)));
    if (this.eventType === "disposition.recorded") {
      new Setting(contentEl)
        .setName("Decision")
        .addText((text) => text.setValue(fields.decision).onChange((value) => (fields.decision = value)));
    }
    if (this.eventType === "fallback.recorded") {
      new Setting(contentEl)
        .setName("Outcome")
        .addText((text) => text.setValue(fields.outcome).onChange((value) => (fields.outcome = value)));
    }
    new Setting(contentEl)
      .setName("Reason code")
      .addText((text) => text.setValue(fields.reason_code).onChange((value) => (fields.reason_code = value)));
    new Setting(contentEl)
      .addButton((button) =>
        button.setButtonText("Record").setCta().onClick(async () => {
          if (this.eventType === "disposition.recorded") {
            await this.plugin.recordDisposition(fields);
          } else {
            await this.plugin.recordFallback(fields);
          }
          this.close();
        }),
      );
  }
}

class OperationModal extends Modal {
  constructor(app, plugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    let operationId = "analyze-gaps";
    let payloadText = "{}";
    contentEl.createEl("h2", { text: "Queue Memoria operation" });
    new Setting(contentEl)
      .setName("Operation ID")
      .addText((text) => text.setValue(operationId).onChange((value) => (operationId = value.trim())));
    new Setting(contentEl)
      .setName("Payload JSON")
      .addTextArea((text) => text.setValue(payloadText).onChange((value) => (payloadText = value)));
    new Setting(contentEl)
      .addButton((button) =>
        button.setButtonText("Queue").setCta().onClick(async () => {
          const payload = JSON.parse(payloadText || "{}");
          if (await this.plugin.enqueueNamedOperation(operationId, payload)) {
            this.close();
          }
        }),
      );
  }
}

class ForkNameModal extends Modal {
  constructor(app, onSubmit) {
    super(app);
    this.onSubmit = onSubmit;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.createEl("h2", { text: "Fork canvas to scratch" });
    let name = "scratch";
    new Setting(contentEl)
      .setName("Scratch name")
      .addText((text) => text.setValue(name).onChange((value) => (name = value.trim())));
    new Setting(contentEl).addButton((button) =>
      button.setButtonText("Queue fork").setCta().onClick(async () => {
        await this.onSubmit(name);
        this.close();
      }),
    );
  }
}

function randomId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const value = Math.floor(Math.random() * 16);
    return (char === "x" ? value : (value & 0x3) | 0x8).toString(16);
  });
}
