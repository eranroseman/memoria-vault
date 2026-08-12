var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};

// src/schema.js
var require_schema = __commonJS({
  "src/schema.js"(exports2, module2) {
    var SURFACES = /* @__PURE__ */ new Set(["obsidian"]);
    var WORKFLOWS = /* @__PURE__ */ new Set([
      "ask",
      "capture",
      "gap",
      "evidence-review",
      "canvas",
      "draft",
      "srd",
      "export",
      "session",
      "connection",
      "operation"
    ]);
    var DECISIONS = /* @__PURE__ */ new Set(["accept", "reject", "edit", "defer", "override", "abandon"]);
    var OUTCOMES = /* @__PURE__ */ new Set([
      "connected",
      "queued",
      "flushed",
      "kept-artifact",
      "fallback",
      "exported",
      "blocked",
      "failed",
      "stopped"
    ]);
    var REASON_CODES = /* @__PURE__ */ new Set([
      "useful",
      "not-useful",
      "too-slow",
      "missing-context",
      "wrong-scope",
      "duplicate",
      "confusing",
      "privacy",
      "offline",
      "external-tool",
      "other"
    ]);
    var BASE_REQUIRED_FIELDS = /* @__PURE__ */ new Set([
      "event_id",
      "event_type",
      "timestamp",
      "session_id",
      "surface"
    ]);
    var EVENT_REQUIRED_FIELDS = {
      "session.started": /* @__PURE__ */ new Set(["workflow"]),
      "session.stopped": /* @__PURE__ */ new Set(["workflow", "outcome", "duration_s"]),
      "http.connected": /* @__PURE__ */ new Set(["workflow", "outcome"]),
      "view.opened": /* @__PURE__ */ new Set(["workflow"]),
      "operation.queued": /* @__PURE__ */ new Set(["workflow", "outcome"]),
      "disposition.recorded": /* @__PURE__ */ new Set(["workflow", "decision", "reason_code"]),
      "fallback.recorded": /* @__PURE__ */ new Set(["workflow", "outcome", "reason_code"]),
      "export.attempted": /* @__PURE__ */ new Set(["workflow", "variant", "outcome", "reason_code"])
    };
    var ALLOWED_FIELDS = /* @__PURE__ */ new Set([
      ...BASE_REQUIRED_FIELDS,
      "workflow",
      "decision",
      "outcome",
      "reason_code",
      "duration_s",
      "project_id",
      "item_type",
      "item_id",
      "variant"
    ]);
    var ENUMS = {
      surface: SURFACES,
      workflow: WORKFLOWS,
      decision: DECISIONS,
      outcome: OUTCOMES,
      reason_code: REASON_CODES
    };
    var OPAQUE_ID_FIELDS = /* @__PURE__ */ new Set(["session_id", "project_id", "item_id"]);
    function validateEvent2(payload) {
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw new Error("empirical event payload must be an object");
      }
      const unknown = Object.keys(payload).filter((key) => !ALLOWED_FIELDS.has(key)).sort();
      if (unknown.length) {
        throw new Error(`empirical event contains unsupported fields: ${unknown.join(", ")}`);
      }
      const eventType = stringField(payload, "event_type");
      const requiredForType = EVENT_REQUIRED_FIELDS[eventType];
      if (!requiredForType) {
        throw new Error(
          `event_type must be one of: ${Object.keys(EVENT_REQUIRED_FIELDS).sort().join(", ")}`
        );
      }
      for (const field of [...BASE_REQUIRED_FIELDS, ...requiredForType]) {
        if (missing(payload[field])) {
          throw new Error(`empirical event missing required field: ${field}`);
        }
      }
      const event = {};
      for (const field of Object.keys(payload).sort()) {
        const value = payload[field];
        if (field === "duration_s") {
          event[field] = duration(value);
        } else {
          event[field] = stringField(payload, field);
        }
      }
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        event.event_id
      )) {
        throw new Error("event_id must be a UUID");
      }
      if (Number.isNaN(Date.parse(event.timestamp)) || !/(Z|[+-]\d\d:\d\d)$/.test(event.timestamp)) {
        throw new Error("timestamp must be ISO-8601 with timezone");
      }
      for (const [field, allowed] of Object.entries(ENUMS)) {
        if (event[field] && !allowed.has(event[field])) {
          throw new Error(`${field} must be one of: ${Array.from(allowed).sort().join(", ")}`);
        }
      }
      for (const field of OPAQUE_ID_FIELDS) {
        if (event[field]) {
          rejectPathlike(field, event[field]);
        }
      }
      return event;
    }
    function sanitizeItemId2(value) {
      const raw = String(value || "").trim();
      if (!raw) {
        return "";
      }
      if (!isPathlike(raw)) {
        return raw;
      }
      return `vault-item-${hash64(raw)}`;
    }
    function missing(value) {
      return value === void 0 || value === null || typeof value === "string" && !value.trim();
    }
    function stringField(payload, field) {
      const value = payload[field];
      if (typeof value !== "string" || !value.trim()) {
        throw new Error(`${field} must be a non-empty string`);
      }
      return value.trim();
    }
    function duration(value) {
      if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
        throw new Error("duration_s must be positive");
      }
      return value;
    }
    function rejectPathlike(field, value) {
      if (isPathlike(value)) {
        throw new Error(`${field} must be an opaque id, not a path or URI`);
      }
    }
    function isPathlike(value) {
      return value.includes("/") || value.includes("\\") || value.includes("..") || value.includes("://") || value.startsWith("~") || value.startsWith(".") || value.startsWith("file:");
    }
    function hash64(value) {
      let hash = 0xcbf29ce484222325n;
      for (const char of value) {
        hash ^= BigInt(char.codePointAt(0));
        hash = BigInt.asUintN(64, hash * 0x100000001b3n);
      }
      return hash.toString(16).padStart(16, "0");
    }
    module2.exports = { sanitizeItemId: sanitizeItemId2, validateEvent: validateEvent2 };
  }
});

// src/relate.js
var require_relate = __commonJS({
  "src/relate.js"(exports2, module2) {
    function buildRelateOperation2({ fromPath, relation, toPath, warrant, roster }) {
      const relations = Array.isArray(roster) ? roster : [];
      if (!relations.length) {
        throw new Error("relate: relation roster unavailable \u2014 retry after the next poll");
      }
      const source = String(fromPath || "").trim();
      const target = String(toPath || "").trim();
      if (!source) {
        throw new Error("relate: From note is required");
      }
      if (!target) {
        throw new Error("relate: To note is required");
      }
      if (!relations.includes(relation)) {
        throw new Error(`relate: relation must be one of ${relations.join(", ")}`);
      }
      const payload = { source_note_path: source, link_type: relation, target_path: target };
      const warrantText = String(warrant || "").trim();
      if (warrantText) {
        payload.warrant = warrantText;
      }
      return { operationId: "curate-note-link", payload };
    }
    module2.exports = { buildRelateOperation: buildRelateOperation2 };
  }
});

// src/handshake.js
var require_handshake = __commonJS({
  "src/handshake.js"(exports2, module2) {
    var HANDSHAKE_TIMEOUT_MS2 = 1e4;
    var RESPAWN_LIMIT = 3;
    var RESPAWN_WINDOW_MS = 3 * 60 * 1e3;
    function buildHandshakeArgv2(engineCommand, vaultPath) {
      const parts = String(engineCommand || "").trim().split(/\s+/).filter(Boolean);
      if (parts.length === 0) {
        parts.push("memoria");
      }
      return {
        command: parts[0],
        args: [...parts.slice(1), "handshake", "--vault", String(vaultPath), "--spawn", "--json"]
      };
    }
    function parseHandshake2(stdoutText) {
      let payload;
      try {
        payload = JSON.parse(String(stdoutText || ""));
      } catch {
        throw new Error("handshake: stdout is not JSON");
      }
      const coordinates = {
        port: Number(payload.port),
        token: String(payload.token || ""),
        bootId: String(payload.boot_id || ""),
        engineVersion: String(payload.engine_version || ""),
        pid: Number(payload.pid || 0)
      };
      if (!Number.isInteger(coordinates.port) || coordinates.port <= 0) {
        throw new Error("handshake: missing port");
      }
      if (!coordinates.token) {
        throw new Error("handshake: missing token");
      }
      if (!coordinates.bootId) {
        throw new Error("handshake: missing boot_id");
      }
      if (!coordinates.engineVersion) {
        throw new Error("handshake: missing engine_version");
      }
      if (!Number.isInteger(coordinates.pid) || coordinates.pid <= 0) {
        throw new Error("handshake: missing pid");
      }
      return coordinates;
    }
    function classifySpawnError2(error) {
      return error && error.code === "ENOENT" ? "engine-missing" : "spawn-failed";
    }
    function createRespawnGate2(now = Date.now) {
      const attempts = [];
      const prune = () => {
        const cutoff = now() - RESPAWN_WINDOW_MS;
        while (attempts.length && attempts[0] <= cutoff) {
          attempts.shift();
        }
      };
      return {
        tryAcquire() {
          prune();
          if (attempts.length >= RESPAWN_LIMIT) {
            return false;
          }
          attempts.push(now());
          return true;
        },
        exhausted() {
          prune();
          return attempts.length >= RESPAWN_LIMIT;
        }
      };
    }
    module2.exports = {
      HANDSHAKE_TIMEOUT_MS: HANDSHAKE_TIMEOUT_MS2,
      RESPAWN_LIMIT,
      RESPAWN_WINDOW_MS,
      buildHandshakeArgv: buildHandshakeArgv2,
      classifySpawnError: classifySpawnError2,
      createRespawnGate: createRespawnGate2,
      parseHandshake: parseHandshake2
    };
  }
});

// src/pill.js
var require_pill = __commonJS({
  "src/pill.js"(exports2, module2) {
    var PILL_STATES = [
      "connected",
      "stale",
      "server-down",
      "token-invalid",
      "engine-missing",
      "key-needed"
    ];
    var POLL_ACTIVE_MS = 30 * 1e3;
    var POLL_IDLE_MS = 2 * 60 * 1e3;
    function formatAsOf2(epochMs) {
      const date = new Date(epochMs);
      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");
      return `${hours}:${minutes}`;
    }
    function computePill2({ connection, openCount, lastPollAt, missingCredential }) {
      if (connection === "engine-missing") {
        return { state: "engine-missing", text: "Memoria \xB7 engine missing", tone: "gray" };
      }
      if (connection === "server-down") {
        return { state: "server-down", text: "Memoria \xB7 server down", tone: "red" };
      }
      if (connection === "token-invalid") {
        return { state: "token-invalid", text: "Memoria \xB7 token invalid", tone: "red" };
      }
      if (connection === "stale") {
        if (!lastPollAt) {
          return { state: "stale", text: "Memoria \xB7 connecting\u2026", tone: "amber" };
        }
        return {
          state: "stale",
          text: `Memoria \xB7 ${openCount} open \xB7 as of ${formatAsOf2(lastPollAt)}`,
          tone: "amber"
        };
      }
      if (missingCredential) {
        return {
          state: "key-needed",
          text: `Memoria \xB7 ${openCount} open \xB7 key needed`,
          tone: "accent"
        };
      }
      return { state: "connected", text: `Memoria \xB7 ${openCount} open`, tone: "green" };
    }
    function computeNextPollDelay2(isActive) {
      return isActive ? POLL_ACTIVE_MS : POLL_IDLE_MS;
    }
    module2.exports = {
      PILL_STATES,
      POLL_ACTIVE_MS,
      POLL_IDLE_MS,
      computeNextPollDelay: computeNextPollDelay2,
      computePill: computePill2,
      formatAsOf: formatAsOf2
    };
  }
});

// src/viewspec.js
var require_viewspec = __commonJS({
  "src/viewspec.js"(exports2, module2) {
    var VIEW_SPEC_VERSION = "view-spec.v1";
    var KNOWN_BLOCK_KINDS = ["card", "text", "badge", "action-row", "evidence-list"];
    var LOUDNESS_RANK = { block: 0, alert: 1, notice: 2, quiet: 3 };
    function node(tag, cls, text, children, attrs) {
      return { tag, cls: cls || "", text: text || "", children: children || [], attrs: attrs || {} };
    }
    function loudnessClass(block) {
      const value = String(block.loudness || "");
      return value ? ` memoria-loudness-${value}` : "";
    }
    function unknownBlock(block) {
      return node(
        "div",
        "memoria-block-unknown",
        `Unknown block type: ${String(block && block.kind)}`,
        [node("pre", "memoria-block-unknown-raw", JSON.stringify(block))]
      );
    }
    function renderBlock2(block) {
      if (!block || typeof block !== "object") {
        return unknownBlock(block);
      }
      switch (block.kind) {
        case "text":
          return node("p", "memoria-block-text", String(block.text || ""));
        case "badge":
          return node("span", `memoria-badge${loudnessClass(block)}`, String(block.label || ""));
        case "evidence-list":
          return node(
            "div",
            "memoria-evidence",
            "",
            (block.items || []).map(
              (item) => node("a", "memoria-evidence-link", String(item.label || item.ref || ""), [], {
                "data-ref": String(item.ref || "")
              })
            )
          );
        case "action-row":
          return node(
            "div",
            "memoria-action-row",
            "",
            (block.actions || []).map(
              (action) => node(
                "button",
                action.primary ? "memoria-action memoria-action-primary" : "memoria-action",
                String(action.label || ""),
                [],
                {
                  "data-operation-id": String(action.operation_id || ""),
                  "data-payload": JSON.stringify(action.payload || {})
                }
              )
            )
          );
        case "card":
          return renderCard(block);
        default:
          return unknownBlock(block);
      }
    }
    function renderCard(block) {
      const semanticChildren = (Array.isArray(block.blocks) ? block.blocks : []).map(renderBlock2);
      const analysis = [];
      const argumentNodes = [];
      if (block.argument_for) {
        argumentNodes.push(node("span", "memoria-card-for", String(block.argument_for)));
      }
      if (block.argument_against) {
        argumentNodes.push(node("span", "memoria-card-against", String(block.argument_against)));
      }
      if (argumentNodes.length) {
        analysis.push(node("div", "memoria-card-arguments", "", argumentNodes));
      }
      const tipping = [];
      if (block.tipped_by) {
        tipping.push(
          node("span", "memoria-card-tipped-label", "tipped by: " + String(block.tipped_by))
        );
      }
      if (block.certainty) {
        tipping.push(node("span", "memoria-certainty-chip", String(block.certainty)));
      }
      if (tipping.length) {
        analysis.push(node("div", "memoria-card-tipped", "", tipping));
      }
      const raisedBy = String(block.raised_by || "");
      const raisedAt = String(block.raised_at || "");
      const meta = [raisedBy ? "raised by " + raisedBy : "", raisedAt].filter(Boolean).join(" \xB7 ");
      return node(
        "div",
        "memoria-card" + loudnessClass(block),
        "",
        [
          node("div", "memoria-card-kind" + loudnessClass(block), String(block.kind_line || "")),
          node("div", "memoria-card-title", String(block.title || "")),
          ...semanticChildren,
          ...analysis,
          ...meta ? [node("div", "memoria-card-meta", meta)] : []
        ],
        { "data-ref": String(block.ref || "") }
      );
    }
    function renderView2(view) {
      if (!view || view.version !== VIEW_SPEC_VERSION) {
        return [
          node(
            "div",
            "memoria-block-unknown",
            `Unknown view-spec version: ${String(view && view.version)}`
          )
        ];
      }
      return (view.blocks || []).map(renderBlock2);
    }
    function sortCards2(cards) {
      const rank = (card) => {
        const value = LOUDNESS_RANK[String(card.loudness || "")];
        return value === void 0 ? LOUDNESS_RANK.quiet + 1 : value;
      };
      const age = (card) => Math.max(0, Number(card.age_s) || 0);
      return [...cards].sort((a, b) => {
        if (rank(a) !== rank(b)) {
          return rank(a) - rank(b);
        }
        return age(b) - age(a);
      });
    }
    var ANALYSIS_CLASSES = ["memoria-card-arguments", "memoria-card-tipped"];
    function collapseAnalysis2(tree, open) {
      const isAnalysis = (child) => ANALYSIS_CLASSES.includes(child.cls);
      const moved = tree.children.filter(isAnalysis);
      if (!moved.length) {
        return tree;
      }
      const children = [];
      let disclosed = false;
      for (const child of tree.children) {
        if (!isAnalysis(child)) {
          children.push(child);
          continue;
        }
        if (disclosed) {
          continue;
        }
        disclosed = true;
        children.push(
          node(
            "button",
            "memoria-analysis-toggle",
            open ? "Hide analysis" : "Show analysis (machine)",
            [],
            { "data-toggle-analysis": "1" }
          ),
          node("div", open ? "memoria-analysis" : "memoria-analysis is-collapsed", "", moved)
        );
      }
      return { ...tree, children };
    }
    function moveSelection2(count, index, key) {
      if (!count) {
        return 0;
      }
      if (key === "j") {
        return Math.min(count - 1, index + 1);
      }
      if (key === "k") {
        return Math.max(0, index - 1);
      }
      return index;
    }
    function materialize2(tree, parentEl) {
      const el = parentEl.createEl(tree.tag, {
        cls: tree.cls || void 0,
        text: tree.text || void 0
      });
      for (const [key, value] of Object.entries(tree.attrs || {})) {
        el.setAttribute(key, value);
      }
      for (const child of tree.children || []) {
        materialize2(child, el);
      }
      return el;
    }
    module2.exports = {
      KNOWN_BLOCK_KINDS,
      LOUDNESS_RANK,
      VIEW_SPEC_VERSION,
      collapseAnalysis: collapseAnalysis2,
      materialize: materialize2,
      moveSelection: moveSelection2,
      renderBlock: renderBlock2,
      renderView: renderView2,
      sortCards: sortCards2
    };
  }
});

// src/main.js
var {
  AbstractInputSuggest,
  ItemView,
  Modal,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  requestUrl
} = require("obsidian");
var { execFile } = require("child_process");
var { sanitizeItemId, validateEvent } = require_schema();
var { buildRelateOperation } = require_relate();
var {
  HANDSHAKE_TIMEOUT_MS,
  buildHandshakeArgv,
  classifySpawnError,
  createRespawnGate,
  parseHandshake
} = require_handshake();
var { computeNextPollDelay, computePill, formatAsOf } = require_pill();
var {
  collapseAnalysis,
  materialize,
  moveSelection,
  renderBlock,
  renderView,
  sortCards
} = require_viewspec();
var DEFAULT_SETTINGS = {
  enabled: false,
  engineCommand: "memoria",
  defaultProjectId: "",
  retentionDays: 30,
  showPrivacyPreview: true,
  queuedEvents: []
};
var EMPTY_ENGINE = { port: 0, token: "", bootId: "", engineVersion: "", pid: 0 };
var STATUS_PATH = "/v1/status";
var ATTENTION_VIEW_PATH = "/v1/views/attention";
var OPERATION_PATH = "/operation/run";
var VIEW_TYPE_ATTENTION = "memoria-attention";
var VIEW_TYPE_EVIDENCE_REVIEW = "memoria-evidence-review";
var EVIDENCE_REVIEW_VIEW_PATH = "/v1/views/evidence-review";
var EVIDENCE_ROUTING_FACETS = ["", "implicit", "multi-hop", "incomplete"];
module.exports = class MemoriaObsidianPlugin extends Plugin {
  async onload() {
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
      callback: () => this.activateAttentionView()
    });
    this.registerView(VIEW_TYPE_EVIDENCE_REVIEW, (leaf) => new EvidenceReviewView(leaf, this));
    this.addCommand({
      id: "open-evidence-review",
      name: "Memoria: Open evidence review",
      callback: () => this.activateEvidenceReviewView()
    });
    this.addCommand({
      id: "relate",
      name: "Memoria: Relate\u2026",
      callback: () => new RelateModal(this.app, this).open()
    });
    this.addCommand({
      id: "connect",
      name: "Memoria: Connect to local server",
      callback: () => this.connect()
    });
    this.addCommand({
      id: "show-attention",
      name: "Memoria: Show attention count",
      callback: () => this.showAttention()
    });
    this.addCommand({
      id: "show-active-concept",
      name: "Memoria: Show active Concept",
      callback: () => this.showActiveConcept()
    });
    this.addCommand({
      id: "queue-operation",
      name: "Memoria: Queue operation",
      callback: () => new OperationModal(this.app, this).open()
    });
    this.addCommand({
      id: "start-session",
      name: "Memoria: Start data collection session",
      callback: () => this.startSession()
    });
    this.addCommand({
      id: "stop-session",
      name: "Memoria: Stop data collection session",
      callback: () => this.stopSession()
    });
    this.addCommand({
      id: "record-disposition",
      name: "Memoria: Record disposition",
      callback: () => new EventModal(this.app, this, "disposition.recorded").open()
    });
    this.addCommand({
      id: "record-fallback",
      name: "Memoria: Record fallback",
      callback: () => new EventModal(this.app, this, "fallback.recorded").open()
    });
    this.addCommand({
      id: "flush-events",
      name: "Memoria: Flush queued events",
      callback: () => this.flushQueuedEvents()
    });
    this.addCommand({
      id: "delete-events",
      name: "Memoria: Delete queued events",
      callback: () => this.deleteQueuedEvents()
    });
    this.forkBadge = "";
    this.addCommand({
      id: "fork-canvas",
      name: "Memoria: Fork canvas to scratch",
      callback: () => this.forkActiveCanvas()
    });
    this.addCommand({
      id: "graduate-scratch-edges",
      name: "Memoria: Graduate scratch canvas edges",
      callback: () => this.graduateScratchEdges()
    });
    if (this.app.workspace.on && this.registerEvent) {
      this.registerEvent(this.app.workspace.on("active-leaf-change", () => this.updateForkBadge()));
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
        timestamp: (/* @__PURE__ */ new Date()).toISOString(),
        session_id: this.ensureSession(),
        surface: "obsidian"
      },
      fields || {}
    );
    if (this.settings.defaultProjectId && !event.project_id) {
      event.project_id = this.settings.defaultProjectId;
    }
    return validateEvent(event);
  }
  async connect() {
    this.respawnGate = createRespawnGate();
    this.engine = Object.assign({}, EMPTY_ENGINE);
    if (!await this.runHandshake()) {
      new Notice(`Memoria: ${this.connectionStatus.replace("-", " ")}`);
      return;
    }
    await this.poll();
    new Notice(`Memoria connected: engine ${this.engine.engineVersion}`);
    if (this.settings.enabled) {
      await this.recordEvent(
        this.baseEvent("http.connected", { workflow: "connection", outcome: "connected" })
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
        item_id: sanitizeItemId(String(concept.id || target))
      })
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
    const duration = this.sessionStartedAt ? Math.max(1, (Date.now() - this.sessionStartedAt) / 1e3) : 1;
    await this.recordEvent(
      this.baseEvent("session.stopped", {
        workflow: "session",
        outcome: "stopped",
        duration_s: duration
      })
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
        name: name || "scratch"
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
      `/project/canvas/forks?project_path=${encodeURIComponent(projectPath)}`
    );
    const forks = payload.canvas_forks && payload.canvas_forks.forks || [];
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
        this.forkBadge = fork.diff_count ? `Memoria fork: ${fork.diff_count} edge(s) diverged` : "Memoria fork: in sync";
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
          reason: `graduated from ${fork.path}`
        },
        `graduate:${fork.path}:${edge.source_note_path}:${edge.link_type}:${edge.target_path}`
      );
    }
    const skipped = (fork.unresolved || []).length;
    new Notice(`Memoria queued ${added.length} link edge(s); skipped ${skipped} unresolved.`);
  }
  async recordDisposition(fields) {
    await this.recordEvent(
      this.baseEvent(
        "disposition.recorded",
        Object.assign({ workflow: "gap", decision: "defer", reason_code: "other" }, fields || {})
      )
    );
    new Notice("Memoria disposition recorded.");
  }
  async recordFallback(fields) {
    await this.recordEvent(
      this.baseEvent(
        "fallback.recorded",
        Object.assign({ workflow: "ask", outcome: "fallback", reason_code: "other" }, fields || {})
      )
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
      await this.postOperation(
        "empirical-event-record",
        event,
        `empirical-event:${event.event_id}`
      );
      this.renderPill();
    } catch (error) {
      await this.queueEvent(event);
      this.renderPill();
      new Notice(`Memoria event queued: ${error.message}`);
    }
  }
  async queueEvent(event) {
    this.settings.queuedEvents = this.settings.queuedEvents || [];
    this.settings.queuedEvents.push({ event, queued_at: (/* @__PURE__ */ new Date()).toISOString() });
    await this.pruneQueuedEvents();
    await this.saveSettings();
  }
  async flushQueuedEvents() {
    const queued = [...this.settings.queuedEvents || []];
    const remaining = [];
    for (const item of queued) {
      try {
        await this.postOperation(
          "empirical-event-record",
          item.event,
          `empirical-event:${item.event.event_id}`
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
    const maxAgeMs = Math.max(1, Number(this.settings.retentionDays || 30)) * 24 * 60 * 60 * 1e3;
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
      this.lastHandshakeError = String(error && error.stderr || error.message || error);
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
      throw: false
    };
    if (body !== void 0) {
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
        throw: false
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }
  async authedRequest(method, path, body) {
    if (!await this.ensureHandshake()) {
      throw new Error(`memoria: ${this.connectionStatus}`);
    }
    let response = await this.rawRequest(method, path, body);
    if (response.status === 401) {
      this.engine = Object.assign({}, EMPTY_ENGINE);
      if (!await this.runHandshake()) {
        throw new Error(`memoria: ${this.connectionStatus}`);
      }
      response = await this.rawRequest(method, path, body);
      if (response.status === 401) {
        this.connectionStatus = await this.probeStatus() ? "token-invalid" : "server-down";
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
      idempotency_key: idempotencyKey
    });
  }
  async enqueueNamedOperation(operationId, payload) {
    try {
      const result = await this.postOperation(operationId, payload, "");
      const requestId = String(result.job && result.job.request_id || "");
      new Notice(`Memoria queued ${operationId}: ${requestId}`);
      await this.recordEvent(
        this.baseEvent("operation.queued", {
          workflow: "operation",
          item_type: "operation",
          item_id: sanitizeItemId(operationId),
          outcome: "queued"
        })
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
        for (const leaf of this.app.workspace.getLeavesOfType ? this.app.workspace.getLeavesOfType(viewType) : []) {
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
    const isActive = typeof document !== "undefined" && typeof document.hasFocus === "function" && document.hasFocus();
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
      missingCredential: this.missingCredential
    });
    this.pillState = pill.state;
    if (typeof this.statusBar.empty === "function") {
      this.statusBar.empty();
      this.statusBar.createEl("span", { cls: `memoria-pill-dot memoria-pill-${pill.tone}` });
      this.statusBar.createEl("span", { cls: "memoria-pill-text", text: pill.text });
      if (this.forkBadge) {
        this.statusBar.createEl("span", {
          cls: "memoria-pill-text",
          text: ` \xB7 ${this.forkBadge}`
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
        `Memoria: credential needed \u2014 run: memoria secrets set ${this.missingCredential}`,
        1e4
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
        `Engine missing \u2014 the Memoria CLI was not found (tried: \`${this.settings.engineCommand}\`). Install it: pipx install memoria, then click to retry. This vault remains fully readable and editable without it.`,
        1e4
      );
      retry();
      return;
    }
    if (this.pillState === "server-down") {
      new Notice(
        `Memoria server down after 3 spawn attempts. ${this.lastHandshakeError} \u2014 Start it manually: memoria serve --workspace ${this.vaultPath()} \u2014 then click to retry.`,
        1e4
      );
      retry();
      return;
    }
    if (this.pillState === "token-invalid") {
      new Notice(
        `Memoria token invalid \u2014 restart the server: memoria serve --stop --workspace ${this.vaultPath()}, then click to reconnect.`,
        1e4
      );
      this.engine = Object.assign({}, EMPTY_ENGINE);
      this.respawnGate = createRespawnGate();
      this.connectionStatus = "stale";
      this.poll();
    }
  }
  async activateView(viewType) {
    const existing = this.app.workspace.getLeavesOfType ? this.app.workspace.getLeavesOfType(viewType) : [];
    const leaf = existing[0] || this.app.workspace.getRightLeaf && this.app.workspace.getRightLeaf(false);
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
var AttentionView = class extends ItemView {
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
        text: `Memoria attention unavailable: ${String(error.message || error)}`
      });
      return;
    }
    const blocks = this.view && this.view.version === "view-spec.v1" ? this.view.blocks || [] : [];
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
      text: `${this.plugin.openCount} open \xB7 as of ${formatAsOf(this.plugin.lastPollAt)}`
    });
    const relateButton = header.createEl("button", { cls: "memoria-action", text: "Relate\u2026" });
    relateButton.addEventListener(
      "click",
      () => new RelateModal(this.plugin.app, this.plugin).open()
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
        cls: index === this.selected ? "memoria-row is-selected" : "memoria-row"
      });
      const loudness = String(card.loudness || "");
      row.createSpan({
        cls: loudness ? `memoria-loudness-dot memoria-loudness-${loudness}` : "memoria-loudness-dot"
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
      await this.plugin.enqueueNamedOperation(actionEl.getAttribute("data-operation-id"), payload);
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
};
var isEvidenceCard = (block) => Boolean(block) && block.kind === "card" && block.review_kind === "evidence-set";
var EvidenceReviewView = class extends ItemView {
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
    return this.facetRouting ? `${EVIDENCE_REVIEW_VIEW_PATH}?routing_type=${encodeURIComponent(this.facetRouting)}` : EVIDENCE_REVIEW_VIEW_PATH;
  }
  async refresh() {
    try {
      const payload = await this.plugin.authedJson(this.viewPath());
      this.view = payload.view || null;
    } catch (error) {
      this.contentEl.empty();
      this.contentEl.createDiv({
        cls: "memoria-block-unknown",
        text: `Memoria evidence review unavailable: ${String(error.message || error)}`
      });
      return;
    }
    const blocks = this.view && this.view.version === "view-spec.v1" ? this.view.blocks || [] : [];
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
      text: this.facetRouting ? `routing: ${this.facetRouting}` : "routing: all"
    });
    facet.setAttribute("data-cycle-routing", "1");
    header.createSpan({
      cls: "memoria-attention-age",
      text: `as of ${formatAsOf(this.plugin.lastPollAt)}`
    });
    if (!this.view || this.view.version !== "view-spec.v1") {
      for (const tree of renderView(this.view)) {
        materialize(tree, root);
      }
      return;
    }
    this.cards.forEach((card, index) => {
      const row = root.createDiv({
        cls: index === this.selected ? "memoria-row is-selected" : "memoria-row"
      });
      row.createSpan({ cls: "memoria-row-title", text: String(card.title || "") });
      row.createSpan({ cls: "memoria-row-age", text: String(card.age_label || "") });
      row.setAttribute("data-row-index", String(index));
      const ref = String(card.ref || "");
      if (ref && ref === this.expandedRef) {
        materialize(collapseAnalysis(renderBlock(card), this.analysisOpenRef === ref), root);
      }
    });
    for (const extra of this.extras) {
      materialize(renderBlock(extra), root);
    }
  }
  toggleExpand(index) {
    this.selected = index;
    const ref = String((this.cards[index] || {}).ref || "");
    this.expandedRef = this.expandedRef === ref ? "" : ref;
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
      await this.plugin.enqueueNamedOperation(actionEl.getAttribute("data-operation-id"), payload);
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
};
var RelateModal = class extends Modal {
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
        text: "Relation roster not loaded yet \u2014 it comes from the server payload. Retry after the next poll (click the status pill)."
      });
    }
    new Setting(contentEl).setName("From").addText((text) => {
      text.setValue(this.fromPath).onChange((value) => this.fromPath = value);
      new NotePathSuggest(this.app, text.inputEl, (path) => {
        this.fromPath = path;
        text.setValue(path);
      });
    });
    const segment = contentEl.createDiv({ cls: "memoria-relation-segment" });
    for (const relation of roster) {
      const button = segment.createEl("button", {
        cls: "memoria-relation-option",
        text: relation
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
      text.onChange((value) => this.toPath = value);
      new NotePathSuggest(this.app, text.inputEl, (path) => {
        this.toPath = path;
        text.setValue(path);
      });
    });
    new Setting(contentEl).setName("Warrant (optional)").setDesc(
      "A `warrant` relation links a license note; Warrant text annotates the selected edge."
    ).addTextArea((text) => text.onChange((value) => this.warrant = value));
    new Setting(contentEl).addButton(
      (button) => button.setButtonText("Queue edge").setCta().onClick(async () => {
        let operation;
        try {
          operation = buildRelateOperation({
            fromPath: this.fromPath,
            relation: this.relation,
            toPath: this.toPath,
            warrant: this.warrant,
            roster
          });
        } catch (error) {
          new Notice(error.message);
          return;
        }
        if (await this.plugin.enqueueNamedOperation(operation.operationId, operation.payload)) {
          this.close();
        }
      })
    );
  }
};
var NotePathSuggest = class extends AbstractInputSuggest {
  constructor(app, inputEl, onPick) {
    super(app, inputEl);
    this.onPick = onPick;
  }
  getSuggestions(query) {
    const needle = String(query || "").toLowerCase();
    return this.app.vault.getMarkdownFiles().map((file) => file.path).filter((path) => path.toLowerCase().includes(needle)).slice(0, 20);
  }
  renderSuggestion(path, el) {
    el.setText(path);
  }
  selectSuggestion(path) {
    this.onPick(path);
    this.close();
  }
};
var MemoriaSettingTab = class extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    new Setting(containerEl).setName("Enable collection").addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.enabled).onChange(async (value) => {
        this.plugin.settings.enabled = value;
        await this.plugin.saveSettings();
        this.plugin.renderPill();
      })
    );
    new Setting(containerEl).setName("Engine command").setDesc("Command used to reach the Memoria CLI (e.g. `wsl memoria` on WSL2 hosts).").addText(
      (text) => text.setValue(this.plugin.settings.engineCommand).onChange(async (value) => {
        this.plugin.settings.engineCommand = value.trim() || DEFAULT_SETTINGS.engineCommand;
        await this.plugin.saveSettings();
      })
    );
    new Setting(containerEl).setName("Default project ID").addText(
      (text) => text.setValue(this.plugin.settings.defaultProjectId).onChange(async (value) => {
        this.plugin.settings.defaultProjectId = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new Setting(containerEl).setName("Retention days").addText(
      (text) => text.setValue(String(this.plugin.settings.retentionDays)).onChange(async (value) => {
        this.plugin.settings.retentionDays = Number(value) || DEFAULT_SETTINGS.retentionDays;
        await this.plugin.saveSettings();
      })
    );
  }
};
var EventModal = class extends Modal {
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
    const fields = {
      workflow: "gap",
      decision: "defer",
      outcome: "fallback",
      reason_code: "other"
    };
    new Setting(contentEl).setName("Workflow").addText(
      (text) => text.setValue(fields.workflow).onChange((value) => fields.workflow = value)
    );
    if (this.eventType === "disposition.recorded") {
      new Setting(contentEl).setName("Decision").addText(
        (text) => text.setValue(fields.decision).onChange((value) => fields.decision = value)
      );
    }
    if (this.eventType === "fallback.recorded") {
      new Setting(contentEl).setName("Outcome").addText(
        (text) => text.setValue(fields.outcome).onChange((value) => fields.outcome = value)
      );
    }
    new Setting(contentEl).setName("Reason code").addText(
      (text) => text.setValue(fields.reason_code).onChange((value) => fields.reason_code = value)
    );
    new Setting(contentEl).addButton(
      (button) => button.setButtonText("Record").setCta().onClick(async () => {
        if (this.eventType === "disposition.recorded") {
          await this.plugin.recordDisposition(fields);
        } else {
          await this.plugin.recordFallback(fields);
        }
        this.close();
      })
    );
  }
};
var OperationModal = class extends Modal {
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
    new Setting(contentEl).setName("Operation ID").addText(
      (text) => text.setValue(operationId).onChange((value) => operationId = value.trim())
    );
    new Setting(contentEl).setName("Payload JSON").addTextArea((text) => text.setValue(payloadText).onChange((value) => payloadText = value));
    new Setting(contentEl).addButton(
      (button) => button.setButtonText("Queue").setCta().onClick(async () => {
        const payload = JSON.parse(payloadText || "{}");
        if (await this.plugin.enqueueNamedOperation(operationId, payload)) {
          this.close();
        }
      })
    );
  }
};
var ForkNameModal = class extends Modal {
  constructor(app, onSubmit) {
    super(app);
    this.onSubmit = onSubmit;
  }
  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.createEl("h2", { text: "Fork canvas to scratch" });
    let name = "scratch";
    new Setting(contentEl).setName("Scratch name").addText((text) => text.setValue(name).onChange((value) => name = value.trim()));
    new Setting(contentEl).addButton(
      (button) => button.setButtonText("Queue fork").setCta().onClick(async () => {
        await this.onSubmit(name);
        this.close();
      })
    );
  }
};
function randomId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const value = Math.floor(Math.random() * 16);
    return (char === "x" ? value : value & 3 | 8).toString(16);
  });
}
