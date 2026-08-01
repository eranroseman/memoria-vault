// Obsidian-compatible CommonJS; hand-authored (no build step).
// `AbstractInputSuggest` (U3-PLUG.8) joins this list when the code that uses it
// lands, not before.
const {
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
const {
  HANDSHAKE_TIMEOUT_MS,
  buildHandshakeArgv,
  classifySpawnError,
  createRespawnGate,
  parseHandshake,
} = require("./handshake");
const { computeNextPollDelay, computePill, formatAsOf } = require("./pill");
const { materialize, moveSelection, renderBlock, renderView, sortCards } = require("./viewspec");

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

  async queueOperation(operationId, payload) {
    const result = await this.postOperation(operationId, payload, "");
    await this.recordEvent(
      this.baseEvent("operation.queued", {
        workflow: "operation",
        item_type: "operation",
        item_id: sanitizeItemId(operationId),
        outcome: "queued",
      }),
    );
    new Notice(`Memoria operation queued: ${operationId}`);
    return result;
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
      for (const leaf of this.app.workspace.getLeavesOfType
        ? this.app.workspace.getLeavesOfType(VIEW_TYPE_ATTENTION)
        : []) {
        if (leaf.view && typeof leaf.view.refresh === "function") {
          leaf.view.refresh();
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

  async activateAttentionView() {
    const existing = this.app.workspace.getLeavesOfType
      ? this.app.workspace.getLeavesOfType(VIEW_TYPE_ATTENTION)
      : [];
    const leaf =
      existing[0] || (this.app.workspace.getRightLeaf && this.app.workspace.getRightLeaf(false));
    if (!leaf) {
      return;
    }
    await leaf.setViewState({ type: VIEW_TYPE_ATTENTION, active: true });
    if (this.app.workspace.revealLeaf) {
      this.app.workspace.revealLeaf(leaf);
    }
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
          await this.plugin.queueOperation(operationId, JSON.parse(payloadText || "{}"));
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
