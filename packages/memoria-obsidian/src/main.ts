const { Modal, Notice, Plugin, PluginSettingTab, Setting, requestUrl } = require("obsidian");
const { sanitizeItemId, validateEvent } = require("./schema");

const TOKEN_KEY = "memoria-obsidian-token";
const DEFAULT_SETTINGS = {
  enabled: false,
  serverUrl: "http://127.0.0.1:8765",
  hasToken: false,
  defaultProjectId: "",
  retentionDays: 30,
  showPrivacyPreview: true,
  queuedEvents: [],
};

module.exports = class MemoriaObsidianPlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.sessionId = "";
    this.sessionStartedAt = 0;
    this.statusBar = this.addStatusBarItem();
    this.addSettingTab(new MemoriaSettingTab(this.app, this));
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
    this.updateStatus();
  }

  onunload() {
    this.statusBar = null;
  }

  async saveSettings() {
    const data = Object.assign({}, this.settings, { hasToken: Boolean(this.settings.hasToken) });
    await this.saveData(data);
  }

  async setToken(token) {
    const clean = String(token || "").trim();
    if (this.app.secretStorage && clean) {
      await this.app.secretStorage.setSecret(TOKEN_KEY, clean);
      this.settings.hasToken = true;
    } else if (this.app.secretStorage) {
      await this.app.secretStorage.setSecret(TOKEN_KEY, "");
      this.settings.hasToken = false;
    } else {
      this.settings.hasToken = false;
      new Notice("Memoria token storage requires Obsidian SecretStorage.");
    }
    await this.saveSettings();
  }

  async token() {
    if (!this.settings.hasToken || !this.app.secretStorage) {
      return "";
    }
    return this.app.secretStorage.getSecret(TOKEN_KEY) || "";
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
    if (!this.settings.enabled) {
      new Notice("Memoria collection is disabled.");
      this.updateStatus("Memoria off");
      return;
    }
    try {
      const status = await this.getJson("/status");
      await this.recordEvent(
        this.baseEvent("http.connected", { workflow: "connection", outcome: "connected" }),
      );
      this.updateStatus("Memoria recording");
      new Notice(`Memoria connected: ${status.api_version || "status ok"}`);
    } catch (error) {
      await this.queueEvent(
        this.baseEvent("http.connected", { workflow: "connection", outcome: "failed" }),
      );
      this.updateStatus(`Memoria offline: ${this.settings.queuedEvents.length} queued`);
      new Notice(`Memoria offline: ${error.message}`);
    }
  }

  async showAttention() {
    const payload = await this.getJson("/attention");
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
    const payload = await this.getJson(`/concept?target=${encodeURIComponent(target)}`);
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
    this.updateStatus("Memoria recording");
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
    this.updateStatus();
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
      this.updateStatus();
    } catch (error) {
      await this.queueEvent(event);
      this.updateStatus(`Memoria offline: ${this.settings.queuedEvents.length} queued`);
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
    this.updateStatus();
    new Notice(`Memoria flushed ${queued.length - remaining.length} event(s).`);
  }

  async deleteQueuedEvents() {
    this.settings.queuedEvents = [];
    await this.saveSettings();
    this.updateStatus();
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

  async getJson(path) {
    const response = await requestUrl({
      url: `${this.settings.serverUrl}${path}`,
      method: "GET",
      headers: await this.headers(),
      throw: false,
    });
    const payload = response.json;
    if (response.status < 200 || response.status >= 300 || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  }

  async postOperation(operationId, payload, idempotencyKey) {
    const response = await requestUrl({
      url: `${this.settings.serverUrl}/operation/run`,
      method: "POST",
      contentType: "application/json",
      headers: await this.headers(),
      body: JSON.stringify({
        operation_id: operationId,
        payload,
        idempotency_key: idempotencyKey,
        actor: "agent",
      }),
      throw: false,
    });
    const result = response.json;
    if (response.status < 200 || response.status >= 300 || result.ok === false) {
      throw new Error(result.error || `HTTP ${response.status}`);
    }
    return result;
  }

  async headers() {
    const token = await this.token();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  updateStatus(text) {
    if (!this.statusBar) {
      return;
    }
    const queued = (this.settings.queuedEvents || []).length;
    const next = text || (!this.settings.enabled ? "Memoria off" : queued ? `Memoria offline: ${queued} queued` : "Memoria recording");
    this.statusBar.setText(next);
  }
};

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
          this.plugin.updateStatus();
        }),
      );
    new Setting(containerEl)
      .setName("Server URL")
      .addText((text) =>
        text.setValue(this.plugin.settings.serverUrl).onChange(async (value) => {
          this.plugin.settings.serverUrl = value.trim() || DEFAULT_SETTINGS.serverUrl;
          await this.plugin.saveSettings();
        }),
      );
    new Setting(containerEl)
      .setName("Bearer token")
      .setDesc("Stored with Obsidian SecretStorage; settings keep only token presence.")
      .addText((text) =>
        text.setPlaceholder(this.plugin.settings.hasToken ? "Token stored" : "Paste token")
          .setValue("")
          .onChange((value) => {
            this.pendingToken = value;
          }),
      )
      .addButton((button) =>
        button.setButtonText("Save").onClick(async () => {
          await this.plugin.setToken(this.pendingToken || "");
          this.display();
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
