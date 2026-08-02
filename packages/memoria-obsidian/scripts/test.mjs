import assert from "node:assert/strict";
import { createRequire } from "node:module";
import Module from "node:module";

// The attention header states an "as of" in the PI's local time (U3 section 3),
// so this file has the same footing as `test-pill.mjs`: under CI's TZ=UTC a
// local-vs-UTC mistake is invisible, and the half-hour offset here moves the
// hour *and* the minute.
process.env.TZ = "Asia/Kolkata";
assert.equal(new Date(0).getHours(), 5, "TZ pin did not take effect");

const require = createRequire(import.meta.url);
const { sanitizeItemId, validateEvent } = require("../schema.js");

const base = {
  event_id: "11111111-1111-4111-8111-111111111111",
  event_type: "disposition.recorded",
  timestamp: "2026-07-08T00:00:00.000Z",
  session_id: "22222222-2222-4222-8222-222222222222",
  surface: "obsidian",
  workflow: "gap",
  decision: "defer",
  reason_code: "other",
};

assert.equal(validateEvent(base).event_id, base.event_id);

for (const key of ["body", "content", "text", "note_text", "excerpt", "path", "uri"]) {
  assert.throws(() => validateEvent({ ...base, [key]: "private" }), /unsupported fields/);
}

for (const key of ["session_id", "project_id", "item_id"]) {
  assert.throws(() => validateEvent({ ...base, [key]: "notes/private.md" }), /opaque id/);
}

assert.match(sanitizeItemId("notes/private.md"), /^vault-item-[a-f0-9]{16}$/);
assert.equal(sanitizeItemId("memoria-id-1"), "memoria-id-1");

const requests = [];
const notices = [];
const workspaceEvents = [];
const opened = [];
const modals = [];
const settings = [];
const suggests = [];

// The healthy poll payload. `open` — not `open_count` — is the wire field the
// pill's count comes from (cross-section contract 2), and the two loudness
// bands are deliberately 1 and 1 so no single `by_loudness` entry equals it:
// a renderer reading the wrong field cannot land on 2 by coincidence.
const SUMMARY_JSON = {
  ok: true,
  api_version: "engine-read-api.v1",
  open: 2,
  by_loudness: { notice: 1, alert: 1 },
  as_of: "2026-07-29T12:00:00Z",
  missing_required_credentials: [],
  link_relations: ["contradicts", "extends", "qualifier", "rebuttal", "supports", "warrant"],
  engine_version: "0.1.0-alpha.20",
  // `POST /operation/run` answers through the same mock, and the enqueue toast
  // has to name the request id it was handed rather than an empty string.
  job: { job_id: "req-123" },
};

// The full view payload (cross-section contract 3). Its card order is the
// *payload* order, deliberately not the row order: `block` arrives second, so a
// pane that skipped `sortCards` would draw these two the other way round. The
// unknown top-level block is here because U3-ENG.5 pinned additive blocks as
// fail-visible — the pane must draw a labeled box, never drop it.
const ATTENTION_VIEW_JSON = {
  ok: true,
  api_version: "engine-read-api.v1",
  view: {
    version: "view-spec.v1",
    kind: "attention",
    blocks: [
      {
        kind: "card",
        id: "inbox_candidate.md",
        ref: "inbox/candidate.md",
        title: "Capture Smith 2024",
        loudness: "notice",
        kind_line: "candidate",
        age_s: 259200,
        age_label: "3d",
        blocks: [
          {
            kind: "evidence-list",
            id: "inbox_candidate.md-evidence",
            items: [{ label: "notes/alpha.md", ref: "notes/alpha.md" }],
          },
          { kind: "text", id: "inbox_candidate.md-body", text: "Review the candidate." },
          {
            kind: "action-row",
            id: "inbox_candidate.md-actions",
            actions: [
              {
                label: "Resolve",
                operation_id: "resolve-attention",
                payload: { target_id: "inbox/candidate.md" },
                primary: true,
              },
            ],
          },
        ],
      },
      {
        kind: "card",
        id: "inbox_blocker.md",
        ref: "inbox/blocker.md",
        title: "Broken citation",
        loudness: "block",
        kind_line: "flag",
        age_s: 0,
        age_label: "0d",
        blocks: [],
      },
      { kind: "sparkline", id: "future-block", points: [1, 2, 3] },
    ],
  },
};

// The evidence-review view payload (V2R-B's binding row grammar): one nested
// card per evidence row, plus a trailing SRD-gap card that is a whole U3 card
// and not an evidence row. The reviewable row carries the four `resolve-evidence`
// actions and parent-owned analysis; the cure row carries neither, which is the
// pair the pane's read-only handling has to tell apart.
const EVIDENCE_REVIEW_VIEW_JSON = {
  ok: true,
  api_version: "engine-read-api.v1",
  view: {
    version: "view-spec.v1",
    kind: "evidence-review",
    blocks: [
      {
        kind: "card",
        id: "ev-0011aabb",
        ref: "projects/project-alpha/draft.md#^blk-a1b2",
        title: "Implicit synthesis claim",
        kind_line: "evidence-review",
        review_kind: "evidence-set",
        evidence_id: "ev-0011aabb",
        project: "projects/project-alpha/project.md",
        routing_type: "implicit",
        reviewable: true,
        disposition: "open",
        item_count: 1,
        age_days: 0,
        age_s: 0,
        age_label: "0d",
        tipped_by: "implicit derivation",
        certainty: "possible",
        blocks: [
          {
            kind: "evidence-list",
            id: "ev-0011aabb-grounds",
            ref: "projects/project-alpha/draft.md#^blk-a1b2",
            items: [{ ref: "source-span:work-alpha:3", kind: "source-span", resolves: true }],
          },
          { kind: "text", id: "ev-0011aabb-routing", text: "implicit" },
          {
            kind: "action-row",
            id: "ev-0011aabb-actions",
            actions: [
              { label: "Accept", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "accept" } },
              { label: "Reject", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "reject" } },
              { label: "Edit", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "edit" } },
              { label: "Defer", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "defer" } },
            ],
          },
        ],
      },
      {
        kind: "card",
        id: "ev-0022ccdd",
        ref: "projects/project-alpha/draft.md#^blk-c3d4",
        title: "Drifted claim text",
        kind_line: "evidence-review",
        review_kind: "evidence-set",
        evidence_id: "ev-0022ccdd",
        project: "projects/project-alpha/project.md",
        routing_type: "",
        reviewable: false,
        disposition: "open",
        item_count: 0,
        age_days: 9,
        age_s: 777600,
        age_label: "9d",
        cure: "repair the draft marker, then re-verify",
        blocks: [
          { kind: "evidence-list", id: "ev-0022ccdd-grounds", items: [] },
          { kind: "text", id: "ev-0022ccdd-routing", text: "evidence-text-drift" },
        ],
      },
      {
        kind: "card",
        id: "srd-gap-1",
        ref: "attention/srd-gap-1.md",
        title: "SRD gap: no falsifier recorded",
        kind_line: "srd-gap",
        age_label: "9d",
        blocks: [{ kind: "text", id: "srd-gap-1-body", text: "Record a falsifier." }],
      },
      // Transport hands the pane whatever JSON arrived, so a malformed payload
      // can put a non-object where a block belongs. It fails visible next to
      // the queue rather than throwing on the way to classifying it.
      null,
    ],
  },
};

// The subset of Obsidian's element API the pane uses. `closest` is real enough
// to answer the three selectors the click handler asks for and to answer them
// by walking parents, because "which control was clicked" is the decision that
// handler makes.
function makeEl(tag, options = {}, parent = null) {
  const el = {
    tag,
    parent,
    children: [],
    cls: String((options && options.cls) || ""),
    text: String((options && options.text) || ""),
    attrs: {},
    listeners: [],
    createEl(childTag, childOptions) {
      const child = makeEl(childTag, childOptions, el);
      el.children.push(child);
      return child;
    },
    createDiv(childOptions) {
      return el.createEl("div", childOptions);
    },
    createSpan(childOptions) {
      return el.createEl("span", childOptions);
    },
    empty() {
      el.children = [];
    },
    addClass(name) {
      el.cls = `${el.cls} ${name}`.trim();
    },
    removeClass(name) {
      el.cls = el.cls
        .split(/\s+/)
        .filter((entry) => entry && entry !== name)
        .join(" ");
    },
    hasClass(name) {
      return el.cls.split(/\s+/).includes(name);
    },
    setAttribute(key, value) {
      el.attrs[key] = value;
    },
    getAttribute(key) {
      return Object.prototype.hasOwnProperty.call(el.attrs, key) ? el.attrs[key] : null;
    },
    addEventListener(event, handler) {
      el.listeners.push({ event, handler });
    },
    matches(selector) {
      const attribute = selector.match(/^(\w+)\[([\w-]+)\]$/);
      if (attribute) {
        return el.tag === attribute[1] && el.getAttribute(attribute[2]) !== null;
      }
      return selector.startsWith(".") && el.hasClass(selector.slice(1));
    },
    closest(selector) {
      for (let node = el; node; node = node.parent) {
        if (node.matches(selector)) {
          return node;
        }
      }
      return null;
    },
  };
  return el;
}

const flatten = (el) => [el, ...el.children.flatMap(flatten)];
const withClass = (el, cls) => flatten(el).filter((node) => node.hasClass(cls));
const clickOn = (target) => ({ target, preventDefault() {} });
const fireClick = (el) => el.listeners.find((entry) => entry.event === "click").handler();

// The relate modal builds its whole form through `Setting`, so an inert stub
// leaves every decision it makes -- which field a value lands in, which control
// carries the help text, what the button does -- unassertable. These record the
// controls they build and let a test do what the PI does: type, pick, click.
const settingsOf = (modal) => settings.filter((entry) => entry.containerEl === modal.contentEl);
const componentsOf = (modal) => settingsOf(modal).flatMap((entry) => entry.components);
const settingNamed = (modal, name) => settingsOf(modal).find((entry) => entry.name === name);
const controlNamed = (modal, name) => settingNamed(modal, name).components[0];
const buttonLabeled = (modal, label) =>
  componentsOf(modal).find((component) => component.label === label);

// Scenarios that need a 401 ladder, an error body, or a probe verdict install
// their own responder; `null` means "healthy summary".
let respond = null;

const settle = () => new Promise((resolve) => setImmediate(resolve));

function okHandshake(token = "sandbox-token") {
  return (command, args, options, callback) => {
    callback(
      null,
      JSON.stringify({
        port: 43210,
        token,
        boot_id: "boot-1",
        engine_version: "0.1.0-alpha.20",
        pid: 4242,
      }),
      "",
    );
  };
}

const originalLoad = Module._load;
Module._load = function load(request, parent, isMain) {
  if (request === "obsidian") {
    class Plugin {
      constructor() {
        this.app = {
          vault: {
            adapter: { basePath: "/tmp/mock-vault" },
            getMarkdownFiles: () => [],
          },
          workspace: {
            getActiveFile: () => null,
            getLeavesOfType: () => [],
            // Recorded, not swallowed: the fork badge is wired to
            // `active-leaf-change`, and a handler nothing can fire is a
            // subscription no test can tell from a missing one.
            on: (name, handler) => {
              workspaceEvents.push({ name, handler, plugin: this });
              return { name };
            },
            openLinkText: (...args) => {
              opened.push(args);
            },
          },
        };
        this.manifest = { version: "0.1.0-alpha.20" };
        this.persistedData = {};
        this.domEvents = [];
      }

      async loadData() {
        return this.persistedData;
      }

      async saveData() {}

      addStatusBarItem() {
        const el = {
          children: [],
          textContent: "",
          setText(text) {
            this.textContent = text;
          },
          empty() {
            this.children = [];
          },
          createEl(tag, options = {}) {
            const child = { tag, cls: options.cls || "", text: options.text || "" };
            this.children.push(child);
            return child;
          },
        };
        return el;
      }

      addSettingTab() {}

      addCommand(command) {
        (this.commands = this.commands || []).push(command.id);
        // Kept whole as well as by id: a command whose callback is wired to the
        // wrong thing has the right id, and the id roster cannot see it.
        (this.commandRoster = this.commandRoster || []).push(command);
      }

      registerView(type, factory) {
        (this.views = this.views || {})[type] = factory;
      }

      registerDomEvent(target, event, handler) {
        this.domEvents.push({ target, event, handler });
      }

      registerEvent(reference) {
        (this.registeredEvents = this.registeredEvents || []).push(reference);
      }

      register() {}
    }
    class Base {
      constructor() {}
    }
    // The host owns `contentEl` and `registerDomEvent` on a leaf view, so the
    // stub owns them here: without them the pane has nothing to draw into and
    // `onOpen` could only be asserted about, never run.
    class ItemViewStub {
      constructor(leaf) {
        this.leaf = leaf;
        this.contentEl = makeEl("div");
        this.domEvents = [];
      }

      registerDomEvent(target, event, handler) {
        this.domEvents.push({ target, event, handler });
      }
    }
    class Notice {
      constructor(message) {
        notices.push(String(message));
      }
    }
    // The host owns a modal's `app`, its `contentEl`, and the `open`/`close`
    // pair. `open()` really calls `onOpen()`, because the form the PI fills in
    // only exists once it has run.
    class ModalStub {
      constructor(app) {
        this.app = app;
        this.contentEl = makeEl("div");
        this.closed = 0;
        modals.push(this);
      }

      open() {
        this.onOpen();
      }

      close() {
        this.closed += 1;
      }
    }
    class SettingStub {
      constructor(containerEl) {
        this.containerEl = containerEl;
        this.itemEl = containerEl.createDiv({ cls: "setting-item" });
        this.name = "";
        this.desc = "";
        this.components = [];
        settings.push(this);
      }

      setName(name) {
        this.name = String(name);
        return this;
      }

      setDesc(desc) {
        this.desc = String(desc);
        return this;
      }

      addText(build) {
        return this._addInput("input", build);
      }

      addTextArea(build) {
        return this._addInput("textarea", build);
      }

      addToggle(build) {
        return this._addInput("checkbox", build);
      }

      addButton(build) {
        const button = {
          label: "",
          cta: false,
          click: null,
          setButtonText(label) {
            button.label = String(label);
            return button;
          },
          setCta() {
            button.cta = true;
            return button;
          },
          onClick(handler) {
            button.click = handler;
            return button;
          },
        };
        this.components.push(button);
        build(button);
        return this;
      }

      _addInput(tag, build) {
        const component = {
          value: "",
          inputEl: this.itemEl.createEl(tag),
          changed: null,
          // Obsidian's `setValue` fills the control without firing `onChange`;
          // a stub that fired it would let a modal that never reads what the PI
          // typed still pass.
          setValue(value) {
            component.value = String(value);
            return component;
          },
          onChange(handler) {
            component.changed = handler;
            return component;
          },
          type(value) {
            component.value = String(value);
            component.changed(component.value);
            return component;
          },
        };
        this.components.push(component);
        build(component);
        return this;
      }
    }
    // The host constructs a suggester against one input element. Recording the
    // instances is how a test reaches a picker the modal never stores.
    class AbstractInputSuggestStub {
      constructor(app, inputEl) {
        this.app = app;
        this.inputEl = inputEl;
        this.closed = 0;
        suggests.push(this);
      }

      close() {
        this.closed += 1;
      }
    }
    return {
      AbstractInputSuggest: AbstractInputSuggestStub,
      ItemView: ItemViewStub,
      Modal: ModalStub,
      Notice,
      Plugin,
      PluginSettingTab: Base,
      Setting: SettingStub,
      requestUrl: async (options) => {
        requests.push(options);
        return respond ? respond(options) : { status: 200, json: SUMMARY_JSON };
      },
    };
  }
  return originalLoad.call(this, request, parent, isMain);
};

const realSetTimeout = globalThis.setTimeout;
const scheduledDelays = [];

try {
  const PluginClass = require("../main.js");

  // 1) Handshake: spawn argv, coordinates in memory only, never persisted.
  const plugin = new PluginClass();
  await plugin.onload();
  plugin.settings.enabled = true;
  plugin._execFile = (command, args, options, callback) => {
    assert.equal(command, "memoria");
    assert.deepEqual(args, ["handshake", "--vault", "/tmp/mock-vault", "--spawn", "--json"]);
    callback(
      null,
      JSON.stringify({
        port: 43210,
        token: "sandbox-token",
        boot_id: "boot-1",
        engine_version: "0.1.0-alpha.20",
        pid: 4242,
      }),
      "",
    );
  };
  assert.equal(await plugin.runHandshake(), true);
  assert.equal(plugin.engine.port, 43210);
  assert.equal(plugin.engine.token, "sandbox-token");
  assert.equal(plugin.connectionStatus, "connected");
  const saved = [];
  plugin.saveData = async (data) => saved.push(data);
  await plugin.saveSettings();
  assert.ok(!JSON.stringify(saved).includes("sandbox-token"), "token must never be persisted");
  assert.ok(!("serverUrl" in plugin.settings));
  assert.ok(!("hasToken" in plugin.settings));
  assert.equal(plugin.settings.engineCommand, "memoria");

  // 2) Authenticated requests use the handshake coordinates + Bearer token.
  const summary = await plugin.authedJson("/v1/views/attention?summary=true");
  assert.equal(summary.ok, true);
  assert.equal(requests[0].url, "http://127.0.0.1:43210/v1/views/attention?summary=true");
  assert.deepEqual(requests[0].headers, { Authorization: "Bearer sandbox-token" });

  await plugin.postOperation("demo-operation", { ok: true }, "demo-key");
  assert.equal(requests[1].url, "http://127.0.0.1:43210/operation/run");
  assert.equal(requests[1].method, "POST");
  assert.equal(requests[1].contentType, "application/json");
  assert.deepEqual(requests[1].headers, { Authorization: "Bearer sandbox-token" });
  // Exact keys: the HTTP door alone assigns authority, so no `actor` is sent.
  assert.deepEqual(JSON.parse(requests[1].body), {
    operation_id: "demo-operation",
    payload: { ok: true },
    idempotency_key: "demo-key",
  });

  // 3) Poll updates pill inputs from the summary payload.
  await plugin.poll();
  assert.equal(plugin.openCount, 2);
  assert.deepEqual(plugin.linkRelations, [
    "contradicts",
    "extends",
    "qualifier",
    "rebuttal",
    "supports",
    "warrant",
  ]);
  assert.ok(plugin.lastPollAt > 0);
  assert.equal(plugin.pillState, "connected");
  assert.ok(plugin.statusBar.children.some((child) => child.text === "Memoria · 2 open"));

  // 4) ENOENT spawn renders engine-missing.
  const plugin2 = new PluginClass();
  await plugin2.onload();
  plugin2._execFile = (command, args, options, callback) => {
    callback(Object.assign(new Error("spawn memoria ENOENT"), { code: "ENOENT" }), "", "");
  };
  assert.equal(await plugin2.runHandshake(), false);
  assert.equal(plugin2.connectionStatus, "engine-missing");
  assert.equal(plugin2.pillState, "engine-missing");
  // No stderr on an ENOENT, so the message is the only diagnostic there is —
  // and it is shown as itself, not as a stringified Error object.
  assert.equal(plugin2.lastHandshakeError, "spawn memoria ENOENT");

  // 5) Persistent handshake failure exhausts the gate into server-down.
  const plugin3 = new PluginClass();
  await plugin3.onload();
  plugin3._execFile = (command, args, options, callback) => {
    const error = new Error("exit 1");
    callback(error, "", "handshake failed; see /tmp/state/serve.log");
  };
  // A spawn failure with the gate still open is `stale`, not `server-down`:
  // the two are different pills and different remediations.
  assert.equal(await plugin3.runHandshake(), false);
  assert.equal(plugin3.connectionStatus, "stale");
  assert.equal(plugin3.pillState, "stale");
  await plugin3.runHandshake();
  await plugin3.runHandshake();
  assert.equal(await plugin3.runHandshake(), false);
  assert.equal(plugin3.connectionStatus, "server-down");
  assert.ok(plugin3.lastHandshakeError.includes("serve.log"));

  // 6) The 401 ladder, all three exits. Nothing above reaches it: the mock
  // answers 200, so every branch below would otherwise ship unexercised.

  // 6a) 401 -> wipe -> re-handshake -> retry succeeds.
  const ladderOk = new PluginClass();
  await ladderOk.onload();
  let ladderOkSpawns = 0;
  ladderOk._execFile = (command, args, options, callback) => {
    ladderOkSpawns += 1;
    okHandshake(`token-${ladderOkSpawns}`)(command, args, options, callback);
  };
  assert.equal(await ladderOk.runHandshake(), true);
  const ladderOkFrom = requests.length;
  let firstCall = true;
  respond = () => {
    if (firstCall) {
      firstCall = false;
      return { status: 401, json: { ok: false, error: "unauthorized" } };
    }
    return { status: 200, json: SUMMARY_JSON };
  };
  const recovered = await ladderOk.authedJson("/v1/views/attention?summary=true");
  assert.equal(recovered.ok, true);
  assert.equal(ladderOkSpawns, 2, "a 401 must trigger exactly one re-handshake");
  assert.equal(ladderOk.engine.token, "token-2", "the retry must carry the new token");
  assert.deepEqual(
    requests.slice(ladderOkFrom).map((request) => request.headers),
    [{ Authorization: "Bearer token-1" }, { Authorization: "Bearer token-2" }],
    "no /v1/status probe when the retry succeeds",
  );

  // 6b) Second 401 with the server answering /v1/status -> token-invalid.
  const ladderToken = new PluginClass();
  await ladderToken.onload();
  ladderToken._execFile = okHandshake();
  assert.equal(await ladderToken.runHandshake(), true);
  const ladderTokenFrom = requests.length;
  respond = (options) =>
    options.url.endsWith("/v1/status")
      ? { status: 200, json: { ok: true } }
      : { status: 401, json: { ok: false, error: "unauthorized" } };
  await assert.rejects(
    ladderToken.authedJson("/v1/views/attention?summary=true"),
    /token invalid/,
  );
  assert.equal(ladderToken.connectionStatus, "token-invalid");
  assert.equal(ladderToken.pillState, "token-invalid");
  const ladderTokenRequests = requests.slice(ladderTokenFrom);
  assert.deepEqual(
    ladderTokenRequests.map((request) => request.url),
    [
      "http://127.0.0.1:43210/v1/views/attention?summary=true",
      "http://127.0.0.1:43210/v1/views/attention?summary=true",
      "http://127.0.0.1:43210/v1/status",
    ],
  );
  // U3 section 5: the liveness probe is unauthenticated. Sending the bearer
  // there would make a revoked token look like a dead server.
  assert.equal(ladderTokenRequests[2].headers, undefined);

  // 6c) Second 401 with /v1/status dead -> server-down, not token-invalid.
  const ladderDown = new PluginClass();
  await ladderDown.onload();
  ladderDown._execFile = okHandshake();
  assert.equal(await ladderDown.runHandshake(), true);
  respond = (options) => {
    if (options.url.endsWith("/v1/status")) {
      throw new Error("ECONNREFUSED");
    }
    return { status: 401, json: { ok: false, error: "unauthorized" } };
  };
  await assert.rejects(ladderDown.authedJson("/v1/views/attention?summary=true"), /token invalid/);
  assert.equal(ladderDown.connectionStatus, "server-down");
  assert.equal(ladderDown.pillState, "server-down");
  assert.equal(await ladderDown.probeStatus(), false, "a throwing probe is not a live server");

  // 6d) A 401 whose re-handshake also fails must leave nothing behind: the
  // rejected token is dead, and holding it would send it on the next request.
  const ladderWiped = new PluginClass();
  await ladderWiped.onload();
  ladderWiped._execFile = okHandshake("doomed-token");
  assert.equal(await ladderWiped.runHandshake(), true);
  ladderWiped._execFile = (command, args, options, callback) => {
    callback(Object.assign(new Error("spawn memoria ENOENT"), { code: "ENOENT" }), "", "");
  };
  respond = () => ({ status: 401, json: { ok: false, error: "unauthorized" } });
  await assert.rejects(
    ladderWiped.authedJson("/v1/views/attention?summary=true"),
    /engine-missing/,
  );
  assert.deepEqual(
    { port: ladderWiped.engine.port, token: ladderWiped.engine.token },
    { port: 0, token: "" },
  );

  // 7) Non-401 failures surface the server's own message, then fall back.
  const failing = new PluginClass();
  await failing.onload();
  failing._execFile = okHandshake();
  assert.equal(await failing.runHandshake(), true);
  respond = () => ({ status: 200, json: { ok: false, error: "operation refused" } });
  await assert.rejects(failing.authedJson("/v1/views/attention"), /operation refused/);
  respond = () => ({ status: 503, json: { ok: true } });
  await assert.rejects(failing.authedJson("/v1/views/attention"), /HTTP 503/);

  // 8) Poll failure degrades a live connection to stale — and only a live one.
  respond = null;
  const polling = new PluginClass();
  await polling.onload();
  polling._execFile = okHandshake();
  assert.equal(await polling.runHandshake(), true);
  await polling.poll();
  assert.equal(polling.connectionStatus, "connected");
  respond = () => ({ status: 503, json: { ok: true } });
  await polling.poll();
  assert.equal(polling.connectionStatus, "stale");
  assert.equal(polling.pillState, "stale");
  assert.ok(
    polling.statusBar.children.some((child) =>
      String(child.text).startsWith("Memoria · 2 open · as of "),
    ),
    "a stale pill keeps the last good count and says when it was taken",
  );
  // A worse status must not be laundered into `stale` by a failed poll.
  polling.connectionStatus = "engine-missing";
  await polling.poll();
  assert.equal(polling.connectionStatus, "engine-missing");

  // 9) Credential and roster mapping out of the summary payload.
  const keyed = new PluginClass();
  await keyed.onload();
  keyed._execFile = okHandshake();
  assert.equal(await keyed.runHandshake(), true);
  respond = () => ({
    status: 200,
    json: {
      ...SUMMARY_JSON,
      // Two names, so "first" is a real choice rather than the only one.
      missing_required_credentials: ["ANTHROPIC_API_KEY", "OPENALEX_MAILTO"],
      link_relations: "not-a-list",
    },
  });
  await keyed.poll();
  assert.equal(keyed.missingCredential, "ANTHROPIC_API_KEY");
  assert.deepEqual(keyed.linkRelations, [], "a non-list roster is dropped, never rendered");
  assert.equal(keyed.pillState, "key-needed");
  assert.ok(keyed.statusBar.children.some((child) => child.text === "Memoria · 2 open · key needed"));
  respond = null;
  await keyed.poll();
  assert.equal(keyed.missingCredential, "", "a resolved credential clears the nag");
  assert.equal(keyed.pillState, "connected");
  // An engine older than this contract answers 200 without `open` at all. The
  // pill must read 0, never the string NaN.
  respond = () => ({ status: 200, json: { ok: true, api_version: "engine-read-api.v1" } });
  await keyed.poll();
  assert.equal(keyed.openCount, 0);
  assert.ok(keyed.statusBar.children.some((child) => child.text === "Memoria · 0 open"));

  // 10) vaultPath: the adapter's method wins over its property, and a missing
  // adapter is "" rather than a crash on the first handshake.
  const pathed = new PluginClass();
  await pathed.onload();
  pathed.app.vault.adapter = {
    getBasePath: () => "/tmp/from-get-base-path",
    basePath: "/tmp/from-property",
  };
  assert.equal(pathed.vaultPath(), "/tmp/from-get-base-path");
  const spawnArgs = [];
  pathed._execFile = (command, args, options, callback) => {
    spawnArgs.push(args);
    okHandshake()(command, args, options, callback);
  };
  assert.equal(await pathed.runHandshake(), true);
  assert.deepEqual(spawnArgs[0], [
    "handshake",
    "--vault",
    "/tmp/from-get-base-path",
    "--spawn",
    "--json",
  ]);
  pathed.app.vault.adapter = null;
  assert.equal(pathed.vaultPath(), "");

  // 11) Poll cadence is wired to window focus, not hardcoded.
  globalThis.setTimeout = (handler, delay) => {
    scheduledDelays.push(delay);
    return realSetTimeout(handler, delay);
  };
  const cadence = new PluginClass();
  await cadence.onload();
  const idleFrom = scheduledDelays.length;
  cadence.schedulePoll();
  globalThis.document = { hasFocus: () => true };
  cadence.schedulePoll();
  // Obsidian always has a `document`; only the focus answer changes. Without
  // this third case a cadence that ignored `hasFocus()` would still pass.
  globalThis.document = { hasFocus: () => false };
  cadence.schedulePoll();
  delete globalThis.document;
  assert.deepEqual(scheduledDelays.slice(idleFrom), [120000, 30000, 120000]);
  globalThis.setTimeout = realSetTimeout;

  // 12) Status bars without `empty()` still get the pill text.
  const legacy = new PluginClass();
  await legacy.onload();
  delete legacy.statusBar.empty;
  legacy.connectionStatus = "connected";
  legacy.openCount = 7;
  legacy.renderPill();
  assert.equal(legacy.statusBar.textContent, "Memoria · 7 open");

  // 13) Pill clicks: every state's remediation, worded as U3 section 3 fixes it.
  const clicker = new PluginClass();
  await clicker.onload();
  clicker._execFile = okHandshake();
  let activated = 0;
  clicker.activateAttentionView = async () => {
    activated += 1;
  };
  const noticesFrom = () => notices.length;

  clicker.connectionStatus = "connected";
  clicker.renderPill();
  clicker.onPillClick();
  assert.equal(activated, 1, "a connected pill opens the pane");

  clicker.missingCredential = "ANTHROPIC_API_KEY";
  clicker.renderPill();
  let mark = noticesFrom();
  clicker.onPillClick();
  assert.equal(activated, 2, "a key-needed pill still opens the pane");
  assert.deepEqual(notices.slice(mark), [
    "Memoria: credential needed — run: memoria secrets set ANTHROPIC_API_KEY",
  ]);

  clicker.missingCredential = "";
  clicker.connectionStatus = "stale";
  clicker.renderPill();
  const staleRequests = requests.length;
  clicker.onPillClick();
  await settle();
  assert.ok(requests.length > staleRequests, "a stale pill polls immediately");
  assert.equal(activated, 2, "a stale pill does not open the pane");

  // An engine-missing pill is the "click to retry" state, so exhaust the gate
  // first: only a fresh gate plus a real retry can reconnect from here.
  const missing = new PluginClass();
  await missing.onload();
  missing._execFile = (command, args, options, callback) => {
    callback(Object.assign(new Error("spawn memoria ENOENT"), { code: "ENOENT" }), "", "");
  };
  await missing.runHandshake();
  await missing.runHandshake();
  await missing.runHandshake();
  assert.equal(missing.pillState, "engine-missing");
  assert.equal(missing.respawnGate.exhausted(), true);
  mark = noticesFrom();
  missing._execFile = okHandshake();
  missing.onPillClick();
  await settle();
  assert.deepEqual(notices.slice(mark, mark + 1), [
    "Engine missing — the Memoria CLI was not found (tried: `memoria`). " +
      "Install it: pipx install memoria, then click to retry. " +
      "This vault remains fully readable and editable without it.",
  ]);
  assert.equal(missing.connectionStatus, "connected", "the click actually retries the spawn");

  // server-down and token-invalid both promise a *fresh* gate: exhaust it
  // first, so a click that reused the old gate could never reconnect.
  const downed = new PluginClass();
  await downed.onload();
  downed._execFile = (command, args, options, callback) => {
    callback(new Error("exit 1"), "", "handshake failed; see /tmp/state/serve.log");
  };
  await downed.runHandshake();
  await downed.runHandshake();
  await downed.runHandshake();
  assert.equal(downed.pillState, "server-down");
  assert.equal(downed.respawnGate.exhausted(), true);
  mark = noticesFrom();
  downed._execFile = okHandshake();
  downed.onPillClick();
  await settle();
  assert.deepEqual(notices.slice(mark, mark + 1), [
    "Memoria server down after 3 spawn attempts. handshake failed; see /tmp/state/serve.log — " +
      "Start it manually: memoria serve --workspace /tmp/mock-vault — then click to retry.",
  ]);
  assert.equal(downed.connectionStatus, "connected", "a fresh gate lets the retry through");

  respond = null;
  const invalid = new PluginClass();
  await invalid.onload();
  invalid._execFile = okHandshake();
  await invalid.runHandshake();
  invalid.connectionStatus = "token-invalid";
  invalid.renderPill();
  invalid.respawnGate.tryAcquire();
  invalid.respawnGate.tryAcquire();
  invalid.respawnGate.tryAcquire();
  assert.equal(invalid.respawnGate.exhausted(), true);
  mark = noticesFrom();
  invalid.onPillClick();
  assert.equal(invalid.engine.port, 0, "a token-invalid click wipes the coordinates first");
  await settle();
  assert.deepEqual(notices.slice(mark, mark + 1), [
    "Memoria token invalid — restart the server: memoria serve --stop " +
      "--workspace /tmp/mock-vault, then click to reconnect.",
  ]);
  assert.equal(invalid.connectionStatus, "connected");
  assert.equal(invalid.engine.token, "sandbox-token");

  // 14) `connect` reports both outcomes and only records when collection is on.
  const connectOk = new PluginClass();
  await connectOk.onload();
  connectOk._execFile = okHandshake();
  mark = noticesFrom();
  await connectOk.connect();
  assert.deepEqual(notices.slice(mark), ["Memoria connected: engine 0.1.0-alpha.20"]);
  // Connecting also fills the pill: a connect that skipped its first poll would
  // leave the user looking at "Memoria · 0 open" on a queue of 2.
  assert.equal(connectOk.openCount, 2);
  assert.equal(connectOk.pillState, "connected");
  const connectBad = new PluginClass();
  await connectBad.onload();
  connectBad._execFile = (command, args, options, callback) => {
    callback(Object.assign(new Error("spawn memoria ENOENT"), { code: "ENOENT" }), "", "");
  };
  mark = noticesFrom();
  await connectBad.connect();
  assert.deepEqual(notices.slice(mark), ["Memoria: engine missing"]);

  // 15) Desktop wiring: the pill is clickable and focus changes reschedule.
  globalThis.window = {};
  const wired = new PluginClass();
  await wired.onload();
  delete globalThis.window;
  assert.deepEqual(
    wired.domEvents.map((entry) => entry.event),
    ["focus", "blur", "click"],
  );
  assert.equal(wired.domEvents[2].target, wired.statusBar, "the click handler is on the pill");
  let clicked = 0;
  wired.onPillClick = () => {
    clicked += 1;
  };
  wired.domEvents[2].handler();
  assert.equal(clicked, 1);

  // 16) Saved settings survive the reload that adds new defaults. Every other
  // fixture loads an empty vault, where dropping the persisted values entirely
  // is indistinguishable from merging them.
  const reloaded = new PluginClass();
  reloaded.persistedData = { engineCommand: "wsl memoria", retentionDays: 7, enabled: true };
  await reloaded.onload();
  assert.equal(reloaded.settings.engineCommand, "wsl memoria");
  assert.equal(reloaded.settings.retentionDays, 7);
  assert.equal(reloaded.settings.enabled, true);
  assert.equal(reloaded.settings.showPrivacyPreview, true, "unsaved defaults still apply");
  const wslArgs = [];
  reloaded._execFile = (command, args, options, callback) => {
    wslArgs.push([command, ...args]);
    okHandshake()(command, args, options, callback);
  };
  assert.equal(await reloaded.runHandshake(), true);
  assert.deepEqual(wslArgs[0], [
    "wsl",
    "memoria",
    "handshake",
    "--vault",
    "/tmp/mock-vault",
    "--spawn",
    "--json",
  ]);
  // A vault that has never saved settings returns null, not {}, and must still
  // load every default rather than throwing on the merge.
  const virgin = new PluginClass();
  virgin.loadData = async () => null;
  await virgin.onload();
  assert.equal(virgin.settings.engineCommand, "memoria");
  assert.equal(virgin.settings.retentionDays, 30);

  // 17) When the workspace announces layout readiness, the first poll waits.
  const deferred = new PluginClass();
  let layoutReady = null;
  deferred.app.workspace.onLayoutReady = (callback) => {
    layoutReady = callback;
  };
  await deferred.onload();
  deferred._execFile = okHandshake();
  assert.equal(typeof layoutReady, "function", "the first poll is deferred to layout-ready");
  const deferredFrom = requests.length;
  await layoutReady();
  await settle();
  assert.ok(requests.length > deferredFrom, "layout-ready runs the first poll");

  // 18) Attention pane registration + enqueue toast naming the request id.
  assert.ok(plugin.views && plugin.views["memoria-attention"], "attention view registered");
  const view = plugin.views["memoria-attention"]({});
  assert.equal(view.getViewType(), "memoria-attention");
  assert.equal(view.getDisplayText(), "Memoria Attention");
  assert.equal(view.getIcon(), "bell");
  assert.ok(plugin.commands.includes("open-attention"));
  const openCommand = plugin.commandRoster.find((command) => command.id === "open-attention");
  assert.equal(openCommand.name, "Memoria: Open attention pane");
  let opens = 0;
  plugin.activateAttentionView = async () => {
    opens += 1;
  };
  openCommand.callback();
  assert.equal(opens, 1, "the command opens the pane");
  mark = noticesFrom();
  const result = await plugin.enqueueNamedOperation("resolve-attention", {
    target_id: "inbox/x.md",
  });
  const operationBodies = requests
    .filter((request) => request.url.endsWith("/operation/run"))
    .map((request) => JSON.parse(request.body));
  assert.deepEqual(
    operationBodies.slice(-2).map((body) => body.operation_id),
    ["resolve-attention", "empirical-event-record"],
  );
  assert.deepEqual(operationBodies.at(-2).payload, { target_id: "inbox/x.md" });
  // No idempotency key: two Resolve clicks on the same card are two requests,
  // and the engine's own dedupe is the one that decides, not the pane's.
  assert.equal(operationBodies.at(-2).idempotency_key, "");
  assert.ok(result);
  // The toast names the id the server handed back; an enqueue the PI cannot
  // trace to a request is the failure this wording exists to prevent.
  assert.deepEqual(notices.slice(mark, mark + 1), ["Memoria queued resolve-attention: req-123"]);

  // 19) A refused enqueue says so and returns nothing, so a card button (and
  // U3-PLUG.8's modal) cannot treat a refusal as queued.
  respond = () => ({ status: 200, json: { ok: false, error: "operation refused" } });
  mark = noticesFrom();
  assert.equal(await plugin.enqueueNamedOperation("resolve-attention", {}), null);
  assert.deepEqual(notices.slice(mark), ["Memoria enqueue failed: operation refused"]);

  // 20) The pane draws the served view: rank order, the header instant, and the
  // unknown block as a labeled box.
  respond = (options) =>
    options.url.endsWith("/v1/views/attention")
      ? { status: 200, json: ATTENTION_VIEW_JSON }
      : { status: 200, json: SUMMARY_JSON };
  plugin.openCount = 7;
  plugin.lastPollAt = Date.UTC(2026, 0, 2, 3, 35); // 09:05 in the pinned zone
  const viewFrom = requests.length;
  await view.onOpen();
  const root = view.contentEl;
  assert.ok(root.hasClass("memoria-attention"));
  assert.equal(root.tabIndex, 0);
  assert.deepEqual(
    view.domEvents.map((entry) => entry.event),
    ["keydown", "click"],
  );
  assert.ok(view.domEvents.every((entry) => entry.target === root));
  assert.deepEqual(
    requests.slice(viewFrom).map((request) => request.url),
    ["http://127.0.0.1:43210/v1/views/attention"],
    "the pane reads the full view, never the summary",
  );
  assert.deepEqual(
    withClass(root, "memoria-attention-header")[0].children.map((child) => child.text),
    ["ATTENTION", "7 open · as of 09:05", "Relate…"],
  );
  const rowTitles = () => withClass(root, "memoria-row-title").map((node) => node.text);
  const cardTitles = () => withClass(root, "memoria-card-title").map((node) => node.text);
  const selectedTitles = () =>
    withClass(root, "is-selected")
      .flatMap((row) => withClass(row, "memoria-row-title"))
      .map((node) => node.text);
  // The payload lists the `notice` card first; the pane draws `block` first.
  assert.deepEqual(rowTitles(), ["Broken citation", "Capture Smith 2024"]);
  assert.deepEqual(
    withClass(root, "memoria-row-age").map((node) => node.text),
    ["0d", "3d"],
  );
  assert.deepEqual(
    withClass(root, "memoria-loudness-dot").map((node) => node.cls),
    [
      "memoria-loudness-dot memoria-loudness-block",
      "memoria-loudness-dot memoria-loudness-notice",
    ],
  );
  assert.deepEqual(
    withClass(root, "memoria-row").map((node) => node.getAttribute("data-row-index")),
    ["0", "1"],
  );
  assert.deepEqual(
    withClass(root, "memoria-block-unknown").map((node) => node.text),
    ["Unknown block type: sparkline"],
    "an additive block is drawn labeled, never dropped",
  );

  // 21) j/k/Enter: selection moves and clamps, Enter expands in place, and any
  // other key is left to Obsidian.
  assert.deepEqual(selectedTitles(), ["Broken citation"]);
  view.onKey({ key: "j", preventDefault() {} });
  assert.deepEqual(selectedTitles(), ["Capture Smith 2024"]);
  view.onKey({ key: "j", preventDefault() {} });
  assert.deepEqual(selectedTitles(), ["Capture Smith 2024"], "j stops at the last row");
  view.onKey({ key: "k", preventDefault() {} });
  assert.deepEqual(selectedTitles(), ["Broken citation"]);
  let prevented = 0;
  // j/k are the pane's own keys: leaving the default would also scroll the leaf.
  view.onKey({
    key: "j",
    preventDefault() {
      prevented += 1;
    },
  });
  assert.equal(prevented, 1, "a handled key is taken from Obsidian");
  view.onKey({ key: "k", preventDefault() {} });
  view.onKey({
    key: "x",
    preventDefault() {
      prevented += 1;
    },
  });
  assert.equal(prevented, 1, "an unhandled key keeps its default");
  assert.deepEqual(selectedTitles(), ["Broken citation"]);
  assert.deepEqual(cardTitles(), [], "nothing is expanded until Enter");
  view.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(cardTitles(), ["Broken citation"]);
  view.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(cardTitles(), [], "Enter on the expanded row collapses it");
  view.onKey({ key: "j", preventDefault() {} });
  view.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(cardTitles(), ["Capture Smith 2024"]);

  // 22) Clicks: an evidence link opens the note, an action button enqueues and
  // re-reads, a row toggles, and a click on nothing does nothing.
  const link = withClass(root, "memoria-evidence-link")[0];
  assert.equal(link.getAttribute("data-ref"), "notes/alpha.md");
  await view.onClick(clickOn(link));
  assert.deepEqual(opened.slice(-1), [["notes/alpha.md", "", false]]);
  // The header's `Relate…` shares the button class, so the card's action is
  // taken by the attribute that makes it one.
  const button = withClass(root, "memoria-action").find((node) =>
    node.getAttribute("data-operation-id"),
  );
  assert.equal(button.getAttribute("data-operation-id"), "resolve-attention");
  const postedFrom = requests.length;
  mark = noticesFrom();
  await view.onClick(clickOn(button));
  const posted = requests
    .slice(postedFrom)
    .filter((request) => request.url.endsWith("/operation/run"))
    .map((request) => JSON.parse(request.body));
  assert.deepEqual(
    posted.map((body) => body.operation_id),
    ["resolve-attention", "empirical-event-record"],
  );
  // The payload travels from the button's `data-payload`, parsed, not rebuilt.
  assert.deepEqual(posted[0].payload, { target_id: "inbox/candidate.md" });
  assert.deepEqual(notices.slice(mark, mark + 1), ["Memoria queued resolve-attention: req-123"]);
  assert.ok(
    requests.slice(postedFrom).some((request) => request.url.endsWith("/v1/views/attention")),
    "a queued action re-reads the view rather than leaving a stale row",
  );
  await view.onClick(clickOn(withClass(root, "memoria-row-title")[0]));
  assert.deepEqual(selectedTitles(), ["Broken citation"]);
  assert.deepEqual(cardTitles(), ["Broken citation"], "clicking a row expands it");
  // The second row, so the row a click lands on comes from `data-row-index`
  // rather than from a default of 0 that only the first row can hide.
  await view.onClick(clickOn(withClass(root, "memoria-row-title")[1]));
  assert.deepEqual(selectedTitles(), ["Capture Smith 2024"]);
  assert.deepEqual(cardTitles(), ["Capture Smith 2024"]);
  await view.onClick(clickOn(root));
  assert.deepEqual(cardTitles(), ["Capture Smith 2024"], "a click on no control changes nothing");

  // 23) A refresh that fails says why, in place of the rows.
  respond = () => ({ status: 503, json: { ok: true } });
  await view.refresh();
  assert.deepEqual(
    withClass(root, "memoria-block-unknown").map((node) => node.text),
    ["Memoria attention unavailable: HTTP 503"],
  );
  assert.deepEqual(withClass(root, "memoria-row"), [], "a failed refresh draws no stale rows");

  // 24) A view-spec version the pane cannot read is a labeled box, not a blank
  // pane: the header still says what the count was and when.
  respond = () => ({
    status: 200,
    json: { ok: true, view: { version: "view-spec.v2", blocks: [{ kind: "card", ref: "x" }] } },
  });
  await view.refresh();
  assert.deepEqual(
    withClass(root, "memoria-block-unknown").map((node) => node.text),
    ["Unknown view-spec version: view-spec.v2"],
  );
  assert.deepEqual(withClass(root, "memoria-row"), []);
  assert.equal(withClass(root, "memoria-attention-header").length, 1);
  // The same box for a payload carrying no `view` at all -- what an engine that
  // answers this path with a summary-shaped body sends, and what a mis-wired
  // caller would produce. It is labeled `null`, not `undefined`, because the
  // pane normalizes an absent view before it renders one.
  respond = () => ({ status: 200, json: { ok: true, api_version: "engine-read-api.v1" } });
  await view.refresh();
  assert.deepEqual(
    withClass(root, "memoria-block-unknown").map((node) => node.text),
    ["Unknown view-spec version: null"],
  );

  // 25) The queue shrinks under a selection. A stale index would select a row
  // that is no longer there, or none at all.
  respond = () => ({ status: 200, json: ATTENTION_VIEW_JSON });
  await view.refresh();
  view.onKey({ key: "j", preventDefault() {} });
  assert.deepEqual(selectedTitles(), ["Capture Smith 2024"]);
  respond = () => ({
    status: 200,
    json: {
      ok: true,
      view: { version: "view-spec.v1", blocks: [ATTENTION_VIEW_JSON.view.blocks[1]] },
    },
  });
  await view.refresh();
  assert.deepEqual(selectedTitles(), ["Broken citation"]);
  respond = () => ({
    status: 200,
    json: { ok: true, view: { version: "view-spec.v1", blocks: [] } },
  });
  await view.refresh();
  prevented = 0;
  view.onKey({
    key: "Enter",
    preventDefault() {
      prevented += 1;
    },
  });
  assert.equal(view.selected, 0, "an empty queue selects nothing");
  // Nothing to expand means the keystroke is not the pane's to swallow.
  assert.equal(prevented, 0, "Enter on an empty queue keeps its default");
  assert.deepEqual(withClass(root, "memoria-row"), []);

  // 26) A successful poll re-reads every open pane; a failed one leaves them
  // alone, and neither trips over a leaf that is not the pane.
  respond = null;
  const polled = new PluginClass();
  await polled.onload();
  polled._execFile = okHandshake();
  assert.equal(await polled.runHandshake(), true);
  let refreshed = 0;
  polled.app.workspace.getLeavesOfType = (type) =>
    type === "memoria-attention"
      ? [
          {
            view: {
              refresh: () => {
                refreshed += 1;
              },
            },
          },
          { view: {} },
          {},
        ]
      : [];
  await polled.poll();
  assert.equal(refreshed, 1, "a successful poll re-reads the open pane");
  // The refresh runs inside the poll's `try`, so a leaf it cannot refresh would
  // be swallowed as a failed poll and shown as a stale pill on a live server.
  assert.equal(polled.connectionStatus, "connected", "a foreign leaf is not a poll failure");
  respond = () => ({ status: 503, json: { ok: true } });
  await polled.poll();
  assert.equal(refreshed, 1, "a failed poll leaves the pane showing its last good rows");
  // A workspace that predates `getLeavesOfType` must still poll.
  respond = null;
  delete polled.app.workspace.getLeavesOfType;
  await polled.poll();
  assert.equal(polled.connectionStatus, "connected");

  // 27) The relate modal (U3 section 4). One form, the served roster rendered
  // verbatim, and the body it queues -- Warrant text included, which is the hop
  // nothing proved before this task.
  respond = null;
  assert.ok(plugin.commands.includes("relate"));
  const relateCommand = plugin.commandRoster.find((command) => command.id === "relate");
  assert.equal(relateCommand.name, "Memoria: Relate…");

  // 27a) Before the first poll there is no roster, so the modal says so and
  // queues nothing: the control is inert rather than inventing three verbs.
  plugin.linkRelations = [];
  plugin.app.workspace.getActiveFile = () => ({ path: "notes/active.md" });
  relateCommand.callback();
  let modal = modals.at(-1);
  assert.ok(modal.contentEl.hasClass("memoria-relate-modal"));
  assert.deepEqual(
    withClass(modal.contentEl, "memoria-setting-warning").map((node) => node.text),
    [
      "Relation roster not loaded yet — it comes from the server payload. " +
        "Retry after the next poll (click the status pill).",
    ],
  );
  assert.deepEqual(withClass(modal.contentEl, "memoria-relation-option"), []);
  let queuedFrom = requests.length;
  mark = noticesFrom();
  await buttonLabeled(modal, "Queue edge").click();
  assert.deepEqual(notices.slice(mark), [
    "relate: relation roster unavailable — retry after the next poll",
  ]);
  assert.equal(requests.length, queuedFrom, "a refused build queues nothing");
  assert.equal(modal.closed, 0, "a refused build leaves the form open to fix");

  // 27b) With a roster: rendered verbatim, in the served order, and the one the
  // builder validates against.
  const servedRoster = [
    "contradicts",
    "extends",
    "qualifier",
    "rebuttal",
    "supports",
    "warrant",
  ];
  plugin.linkRelations = servedRoster;
  plugin.app.vault.getMarkdownFiles = () => [
    { path: "notes/active.md" },
    { path: "notes/Target-Note.md" },
    { path: "inbox/other.md" },
  ];
  relateCommand.callback();
  modal = modals.at(-1);
  assert.deepEqual(withClass(modal.contentEl, "memoria-setting-warning"), []);
  const relationOptions = withClass(modal.contentEl, "memoria-relation-option");
  assert.deepEqual(
    relationOptions.map((node) => node.text),
    servedRoster,
    "the relation control is the served roster verbatim -- no local relation list",
  );
  // The From field opens on the note the PI is reading, which is the whole
  // reason the modal asks the workspace for it.
  assert.equal(controlNamed(modal, "From").value, "notes/active.md");
  assert.equal(controlNamed(modal, "To").value, "");
  assert.equal(
    settingNamed(modal, "Warrant (optional)").desc,
    "A `warrant` relation links a license note; Warrant text annotates the selected edge.",
  );

  // Both endpoints filled but no relation picked: the refusal names the served
  // roster, so a modal validating against a local list could not word it this
  // way. Both endpoints, because U3-PLUG.5 left the order of two simultaneous
  // refusals deliberately unpinned and this must not pin it by the back door.
  controlNamed(modal, "To").type("notes/typed-then-replaced.md");
  queuedFrom = requests.length;
  mark = noticesFrom();
  await buttonLabeled(modal, "Queue edge").click();
  assert.deepEqual(notices.slice(mark), [
    "relate: relation must be one of contradicts, extends, qualifier, rebuttal, supports, warrant",
  ]);
  assert.equal(requests.length, queuedFrom);

  const pick = (label) => fireClick(relationOptions.find((node) => node.text === label));
  const active = () =>
    relationOptions.filter((node) => node.hasClass("is-active")).map((node) => node.text);
  pick("supports");
  assert.deepEqual(active(), ["supports"]);
  pick("rebuttal");
  assert.deepEqual(active(), ["rebuttal"], "one relation at a time, not an accumulating set");

  // 27c) The pickers offer vault paths. Two suggesters, each on its own input:
  // one bound to the wrong control would rewrite the wrong endpoint.
  const [fromSuggest, toSuggest] = suggests.slice(-2);
  assert.equal(fromSuggest.inputEl, controlNamed(modal, "From").inputEl);
  assert.equal(toSuggest.inputEl, controlNamed(modal, "To").inputEl);
  assert.deepEqual(toSuggest.getSuggestions("target-note"), ["notes/Target-Note.md"]);
  assert.deepEqual(
    toSuggest.getSuggestions("").length,
    3,
    "an empty query offers every note rather than none",
  );
  plugin.app.vault.getMarkdownFiles = () =>
    Array.from({ length: 25 }, (_, index) => ({ path: `notes/bulk-${index}.md` }));
  assert.equal(toSuggest.getSuggestions("bulk").length, 20, "the list is capped at 20");
  plugin.app.vault.getMarkdownFiles = () => [
    { path: "notes/active.md" },
    { path: "notes/other-source.md" },
    { path: "notes/Target-Note.md" },
  ];

  // A picked suggestion fills the field *and* the control the PI is looking at,
  // replacing what was typed above. The From pick comes second and lands on a
  // third path, so a picker wired to the other endpoint would be visible in the
  // submitted body rather than hidden by the pick that follows it.
  toSuggest.selectSuggestion("notes/Target-Note.md");
  assert.equal(controlNamed(modal, "To").value, "notes/Target-Note.md");
  assert.equal(toSuggest.closed, 1, "picking closes the suggester");
  fromSuggest.selectSuggestion("notes/other-source.md");
  assert.equal(controlNamed(modal, "From").value, "notes/other-source.md");
  assert.equal(controlNamed(modal, "To").value, "notes/Target-Note.md", "one field per picker");
  // The host draws each row through this, so a picker that renders nothing is a
  // dropdown of blank lines -- unpickable, and silent about why.
  const suggestionEl = {
    text: "",
    setText(value) {
      this.text = value;
    },
  };
  toSuggest.renderSuggestion("notes/Target-Note.md", suggestionEl);
  assert.equal(suggestionEl.text, "notes/Target-Note.md");

  // 27d) Warrant text rides the same submission. The body is asserted whole:
  // the legacy `reason` alias, a dropped `warrant`, and a client-supplied
  // `actor` are each one extra or missing key away.
  controlNamed(modal, "Warrant (optional)").type("  RCTs in this population license it  ");
  queuedFrom = requests.length;
  mark = noticesFrom();
  await buttonLabeled(modal, "Queue edge").click();
  const relateBodies = requests
    .slice(queuedFrom)
    .filter((request) => request.url.endsWith("/operation/run"))
    .map((request) => JSON.parse(request.body));
  assert.deepEqual(relateBodies[0], {
    operation_id: "curate-note-link",
    payload: {
      source_note_path: "notes/other-source.md",
      link_type: "rebuttal",
      target_path: "notes/Target-Note.md",
      warrant: "RCTs in this population license it",
    },
    idempotency_key: "",
  });
  assert.deepEqual(notices.slice(mark, mark + 1), ["Memoria queued curate-note-link: req-123"]);
  assert.equal(modal.closed, 1, "a queued edge closes the form");

  // 27e) A blank Warrant omits the key entirely rather than sending "": the
  // `warrant` *relation* is an edge in the frontmatter graph, and Warrant
  // *text* is an annotation on it. This form sends one without the other.
  const openRelateModal = (relation) => {
    relateCommand.callback();
    const form = modals.at(-1);
    fireClick(
      withClass(form.contentEl, "memoria-relation-option").find((node) => node.text === relation),
    );
    controlNamed(form, "To").type("notes/Target-Note.md");
    return form;
  };
  modal = openRelateModal("warrant");
  queuedFrom = requests.length;
  await buttonLabeled(modal, "Queue edge").click();
  assert.deepEqual(
    requests
      .slice(queuedFrom)
      .filter((request) => request.url.endsWith("/operation/run"))
      .map((request) => JSON.parse(request.body).payload)[0],
    {
      source_note_path: "notes/active.md",
      link_type: "warrant",
      target_path: "notes/Target-Note.md",
    },
  );

  // 27f) A refused enqueue keeps the form open, so the PI retries the edge
  // instead of retyping it. This is what U3-PLUG.7's `null` return is for.
  respond = () => ({ status: 200, json: { ok: false, error: "operation refused" } });
  modal = openRelateModal("extends");
  mark = noticesFrom();
  await buttonLabeled(modal, "Queue edge").click();
  assert.deepEqual(notices.slice(mark, mark + 1), ["Memoria enqueue failed: operation refused"]);
  assert.equal(modal.closed, 0, "a refused enqueue leaves the typed form standing");
  respond = null;
  await buttonLabeled(modal, "Queue edge").click();
  assert.equal(modal.closed, 1, "and the same form queues once the server answers");

  // 27g) The pane header opens the same modal, so the PI never has to leave the
  // queue to write an edge about what is in it.
  respond = (options) =>
    options.url.endsWith("/v1/views/attention")
      ? { status: 200, json: ATTENTION_VIEW_JSON }
      : { status: 200, json: SUMMARY_JSON };
  await view.refresh();
  const relateButton = withClass(withClass(root, "memoria-attention-header")[0], "memoria-action")[0];
  assert.equal(relateButton.text, "Relate…");
  const modalsBefore = modals.length;
  fireClick(relateButton);
  assert.equal(modals.length, modalsBefore + 1, "the header button opens the relate modal");
  assert.deepEqual(
    withClass(modals.at(-1).contentEl, "memoria-relation-option").map((node) => node.text),
    servedRoster,
    "the header's modal is wired to the same plugin, roster and all",
  );

  // 28) Evidence-review pane (V2 spec sections 1-3): a second view on the same
  // infrastructure, reading its own path, keeping the server's queue order, and
  // putting the machine's analysis behind a disclosure the PI has to open.
  respond = (options) =>
    options.url.includes("/v1/views/evidence-review")
      ? { status: 200, json: EVIDENCE_REVIEW_VIEW_JSON }
      : { status: 200, json: SUMMARY_JSON };
  assert.ok(plugin.views["memoria-evidence-review"], "evidence review view registered");
  const reviewView = plugin.views["memoria-evidence-review"]({});
  assert.equal(reviewView.getViewType(), "memoria-evidence-review");
  assert.equal(reviewView.getDisplayText(), "Memoria Evidence Review");
  assert.ok(plugin.commands.includes("open-evidence-review"));
  const reviewCommand = plugin.commandRoster.find((command) => command.id === "open-evidence-review");
  assert.equal(reviewCommand.name, "Memoria: Open evidence review");
  let reviewOpens = 0;
  plugin.activateEvidenceReviewView = async () => {
    reviewOpens += 1;
  };
  reviewCommand.callback();
  assert.equal(reviewOpens, 1, "the command opens the evidence-review pane");
  // The attention command must still open the attention pane: two panes wired
  // to one activator is exactly what a copy-paste second view produces.
  assert.equal(opens, 1, "the review command does not open the attention pane");

  plugin.lastPollAt = Date.UTC(2026, 0, 2, 3, 35); // 09:05 in the pinned zone
  const reviewFrom = requests.length;
  await reviewView.onOpen();
  const reviewRoot = reviewView.contentEl;
  assert.ok(reviewRoot.hasClass("memoria-evidence-review"));
  assert.deepEqual(
    requests.slice(reviewFrom).map((request) => request.url),
    ["http://127.0.0.1:43210/v1/views/evidence-review"],
    "the pane reads its own view, unfiltered, and nothing else",
  );
  const reviewRowTitles = () =>
    withClass(reviewRoot, "memoria-row-title").map((node) => node.text);
  const reviewCardTitles = () =>
    withClass(reviewRoot, "memoria-card-title").map((node) => node.text);
  // Spec section 6: the batch order *is* the review order. The payload lists the
  // 0d row first and the 9d row second, which is the order `sortCards` would
  // reverse — so a pane that sorted like the attention pane fails here.
  assert.deepEqual(reviewRowTitles(), ["Implicit synthesis claim", "Drifted claim text"]);
  assert.deepEqual(
    withClass(reviewRoot, "memoria-row-age").map((node) => node.text),
    ["0d", "9d"],
  );
  // The SRD-gap card is not an evidence row: it stays a whole card, drawn after
  // the queue, with no row of its own to select or expand.
  assert.deepEqual(reviewCardTitles(), ["SRD gap: no falsifier recorded"]);
  assert.deepEqual(
    withClass(reviewRoot, "memoria-card-kind").map((node) => node.text),
    ["srd-gap"],
  );
  assert.deepEqual(
    withClass(reviewRoot, "memoria-block-unknown").map((node) => node.text),
    ["Unknown block type: null"],
    "a malformed block is drawn labeled, never dropped and never fatal",
  );
  assert.deepEqual(
    withClass(reviewRoot, "memoria-attention-header")[0].children.map((child) => child.text),
    ["EVIDENCE REVIEW", "routing: all", "as of 09:05"],
  );

  // 28a) Expanding a reviewable row: evidence, routing, and the four actions
  // render before a collapsed analysis disclosure. Nothing about the machine's
  // opinion is visible until the PI asks for it.
  reviewView.onKey({ key: "Enter", preventDefault() {} });
  const expandedClasses = () =>
    withClass(reviewRoot, "memoria-card")[0].children.map((node) => node.cls);
  assert.deepEqual(expandedClasses(), [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
    "memoria-action-row",
    "memoria-analysis-toggle",
    "memoria-analysis is-collapsed",
  ]);
  const actionButtons = () =>
    withClass(reviewRoot, "memoria-action").filter((node) => node.getAttribute("data-operation-id"));
  assert.deepEqual(
    actionButtons().map((node) => [
      node.text,
      node.getAttribute("data-operation-id"),
      JSON.parse(node.getAttribute("data-payload")).decision,
    ]),
    [
      ["Accept", "resolve-evidence", "accept"],
      ["Reject", "resolve-evidence", "reject"],
      ["Edit", "resolve-evidence", "edit"],
      ["Defer", "resolve-evidence", "defer"],
    ],
  );
  // Spec section 2 field 7: four equals. A pre-selected action is a verdict.
  assert.deepEqual(
    actionButtons().map((node) => node.cls),
    ["memoria-action", "memoria-action", "memoria-action", "memoria-action"],
  );

  // 28b) The disclosure opens and closes on its own control, and a fresh expand
  // re-collapses it — independence-first by construction, not by habit.
  const analysisToggle = () => withClass(reviewRoot, "memoria-analysis-toggle")[0];
  assert.equal(analysisToggle().text, "Show analysis (machine)");
  await reviewView.onClick(clickOn(analysisToggle()));
  assert.deepEqual(expandedClasses().slice(-2), ["memoria-analysis-toggle", "memoria-analysis"]);
  assert.equal(analysisToggle().text, "Hide analysis");
  assert.deepEqual(
    withClass(reviewRoot, "memoria-card-tipped")[0].children.map((node) => node.text),
    ["tipped by: implicit derivation", "possible"],
  );
  // The same control closes it: a disclosure that only opens is a one-way
  // door, and the PI cannot put the machine's opinion back out of view.
  await reviewView.onClick(clickOn(analysisToggle()));
  assert.deepEqual(
    expandedClasses().slice(-2),
    ["memoria-analysis-toggle", "memoria-analysis is-collapsed"],
  );
  assert.equal(analysisToggle().text, "Show analysis (machine)");
  await reviewView.onClick(clickOn(analysisToggle()));
  reviewView.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(reviewCardTitles(), ["SRD gap: no falsifier recorded"], "Enter collapses");
  reviewView.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(
    expandedClasses().slice(-2),
    ["memoria-analysis-toggle", "memoria-analysis is-collapsed"],
    "re-expanding a row re-collapses its analysis",
  );

  // 28c) An action enqueues the payload the server serialized, then re-reads.
  const acceptButton = actionButtons()[0];
  let reviewPostedFrom = requests.length;
  await reviewView.onClick(clickOn(acceptButton));
  const reviewPosted = requests
    .slice(reviewPostedFrom)
    .filter((request) => request.url.endsWith("/operation/run"))
    .map((request) => JSON.parse(request.body));
  assert.deepEqual(
    reviewPosted.map((body) => body.operation_id),
    ["resolve-evidence", "empirical-event-record"],
  );
  assert.deepEqual(reviewPosted[0].payload, { evidence_id: "ev-0011aabb", decision: "accept" });
  assert.ok(
    requests
      .slice(reviewPostedFrom)
      .some((request) => request.url.includes("/v1/views/evidence-review")),
    "a disposition re-reads the queue rather than leaving a decided row standing",
  );

  // The re-read keeps the row open, so the PI sees what the decision did to the
  // row they were reading rather than losing their place in the queue.
  assert.deepEqual(actionButtons().length, 4, "the decided row stays expanded");

  // 28d) Edit is the one action that also takes the PI to the draft block: the
  // decision it records is "I will fix the marker", which needs the marker.
  const openedFrom = opened.length;
  await reviewView.onClick(clickOn(actionButtons()[0]));
  assert.deepEqual(opened.slice(openedFrom), [], "Accept does not navigate away from the queue");
  await reviewView.onClick(clickOn(actionButtons()[2]));
  assert.deepEqual(opened.slice(openedFrom), [
    ["projects/project-alpha/draft.md#^blk-a1b2", "", false],
  ]);

  // 28e) The permanently blocked row is read-only: no actions to press and no
  // analysis to open, so the pane cannot invite a decision that cannot be made.
  reviewView.onKey({ key: "j", preventDefault() {} });
  reviewView.onKey({ key: "Enter", preventDefault() {} });
  assert.deepEqual(expandedClasses(), [
    "memoria-card-kind",
    "memoria-card-title",
    "memoria-evidence",
    "memoria-block-text",
  ]);
  assert.deepEqual(actionButtons(), []);
  assert.deepEqual(withClass(reviewRoot, "memoria-analysis-toggle"), []);

  // 28f) The routing facet cycles through the queue's three routing types and
  // back to the unfiltered queue, carrying the canonical `routing_type` key.
  const facetButton = () =>
    withClass(withClass(reviewRoot, "memoria-attention-header")[0], "memoria-action")[0];
  const facetUrls = [];
  for (const expected of ["implicit", "multi-hop", "incomplete", "all"]) {
    reviewPostedFrom = requests.length;
    await reviewView.onClick(clickOn(facetButton()));
    facetUrls.push(requests.slice(reviewPostedFrom).at(-1).url);
    assert.equal(facetButton().text, `routing: ${expected}`);
  }
  assert.deepEqual(facetUrls, [
    "http://127.0.0.1:43210/v1/views/evidence-review?routing_type=implicit",
    "http://127.0.0.1:43210/v1/views/evidence-review?routing_type=multi-hop",
    "http://127.0.0.1:43210/v1/views/evidence-review?routing_type=incomplete",
    "http://127.0.0.1:43210/v1/views/evidence-review",
  ]);

  // 28g) A failed read says why, in place of the rows, naming this pane.
  respond = () => ({ status: 503, json: { ok: true } });
  await reviewView.refresh();
  assert.deepEqual(
    withClass(reviewRoot, "memoria-block-unknown").map((node) => node.text),
    ["Memoria evidence review unavailable: HTTP 503"],
  );
  assert.deepEqual(withClass(reviewRoot, "memoria-row"), []);

  // 28i) The same three claims the attention pane makes about its rows, made
  // again here: a copied render loop inherits none of them. A row click reaches
  // the row its `data-row-index` names, a shrinking queue clamps the selection
  // rather than pointing past the end, and a key the pane does not own keeps
  // its default.
  respond = (options) =>
    options.url.includes("/v1/views/evidence-review")
      ? { status: 200, json: EVIDENCE_REVIEW_VIEW_JSON }
      : { status: 200, json: SUMMARY_JSON };
  await reviewView.refresh();
  let reviewPrevented = 0;
  reviewView.onKey({
    key: "x",
    preventDefault() {
      reviewPrevented += 1;
    },
  });
  assert.equal(reviewPrevented, 0, "an unhandled key keeps its default");
  reviewView.onKey({
    key: "j",
    preventDefault() {
      reviewPrevented += 1;
    },
  });
  reviewView.onKey({
    key: "k",
    preventDefault() {
      reviewPrevented += 1;
    },
  });
  assert.equal(reviewPrevented, 2, "j/k are the pane's own keys, taken from Obsidian");
  // 28e left the second row expanded, so the first click on it collapses; the
  // second re-expands it. Index 1 both times, because a handler that ignored
  // `data-row-index` and defaulted to 0 would satisfy a click on the first row.
  await reviewView.onClick(clickOn(withClass(reviewRoot, "memoria-row-title")[1]));
  assert.deepEqual(reviewCardTitles(), ["SRD gap: no falsifier recorded"]);
  await reviewView.onClick(clickOn(withClass(reviewRoot, "memoria-row-title")[1]));
  assert.deepEqual(reviewCardTitles(), ["Drifted claim text", "SRD gap: no falsifier recorded"]);
  assert.deepEqual(
    withClass(reviewRoot, "is-selected").flatMap((row) =>
      withClass(row, "memoria-row-title").map((node) => node.text),
    ),
    ["Drifted claim text"],
  );
  respond = () => ({
    status: 200,
    json: {
      ok: true,
      view: {
        version: "view-spec.v1",
        kind: "evidence-review",
        blocks: [EVIDENCE_REVIEW_VIEW_JSON.view.blocks[0]],
      },
    },
  });
  await reviewView.refresh();
  assert.deepEqual(
    withClass(reviewRoot, "is-selected").flatMap((row) =>
      withClass(row, "memoria-row-title").map((node) => node.text),
    ),
    ["Implicit synthesis claim"],
    "a queue that shrank under the selection re-selects a row that exists",
  );
  // A payload carrying no `view` at all — what an engine answering this path
  // with a summary-shaped body sends. It is labeled `null`, not `undefined`,
  // because the pane normalizes an absent view before it renders one.
  respond = () => ({ status: 200, json: { ok: true, api_version: "engine-read-api.v1" } });
  await reviewView.refresh();
  assert.deepEqual(
    withClass(reviewRoot, "memoria-block-unknown").map((node) => node.text),
    ["Unknown view-spec version: null"],
  );
  assert.deepEqual(withClass(reviewRoot, "memoria-row"), []);
  respond = () => ({
    status: 200,
    json: { ok: true, view: { version: "view-spec.v1", kind: "evidence-review", blocks: [] } },
  });
  await reviewView.refresh();
  reviewPrevented = 0;
  reviewView.onKey({
    key: "Enter",
    preventDefault() {
      reviewPrevented += 1;
    },
  });
  assert.equal(reviewView.selected, 0, "an empty queue selects nothing");
  // Nothing to expand means the keystroke is not the pane's to swallow.
  assert.equal(reviewPrevented, 0, "Enter on an empty queue keeps its default");
  assert.deepEqual(withClass(reviewRoot, "memoria-row"), []);

  // 28j) Both activators really open their own view type. Every assertion
  // above about the two commands runs against a stubbed activator, so the one
  // line that names a view type in each is otherwise unproven — and a second
  // pane copied from the first is exactly where that line goes wrong.
  const opener = new PluginClass();
  await opener.onload();
  const viewStates = [];
  const revealed = [];
  const fakeLeaf = {
    async setViewState(state) {
      viewStates.push(state);
    },
  };
  opener.app.workspace.getRightLeaf = () => fakeLeaf;
  opener.app.workspace.revealLeaf = (leaf) => revealed.push(leaf);
  await opener.activateAttentionView();
  await opener.activateEvidenceReviewView();
  assert.deepEqual(viewStates, [
    { type: "memoria-attention", active: true },
    { type: "memoria-evidence-review", active: true },
  ]);
  assert.deepEqual(revealed, [fakeLeaf, fakeLeaf]);
  // A workspace with nowhere to put the leaf is not a crash.
  opener.app.workspace.getRightLeaf = () => null;
  await opener.activateEvidenceReviewView();
  assert.equal(viewStates.length, 2);

  // 28h) The poll refreshes both panes. A refresh loop pinned to the attention
  // view alone leaves an open review queue showing decided rows forever.
  respond = null;
  const bothPanes = new PluginClass();
  await bothPanes.onload();
  bothPanes._execFile = okHandshake();
  assert.equal(await bothPanes.runHandshake(), true);
  const refreshedTypes = [];
  bothPanes.app.workspace.getLeavesOfType = (type) => [
    { view: { refresh: () => refreshedTypes.push(type) } },
  ];
  await bothPanes.poll();
  assert.deepEqual(refreshedTypes, ["memoria-attention", "memoria-evidence-review"]);

  // 29) The canvas surface (U3 section 6). Fork is an enqueue, the badge is a
  // read on the active scratch file, graduation is one enqueue per added edge.
  // None of the three touches the vault: the engine owns every byte written.
  respond = null;
  assert.ok(plugin.commands.includes("fork-canvas"));
  assert.ok(plugin.commands.includes("graduate-scratch-edges"));
  const forkCommand = plugin.commandRoster.find((command) => command.id === "fork-canvas");
  const graduateCommand = plugin.commandRoster.find(
    (command) => command.id === "graduate-scratch-edges",
  );
  assert.equal(forkCommand.name, "Memoria: Fork canvas to scratch");
  assert.equal(graduateCommand.name, "Memoria: Graduate scratch canvas edges");

  const postBodiesSince = (from) =>
    requests
      .slice(from)
      .filter((request) => request.method === "POST")
      .map((request) => JSON.parse(request.body));

  // 29a) Off a generated canvas the fork command explains itself and opens no
  // form: a fork of the wrong file is a scratch canvas nothing can diff.
  plugin.app.workspace.getActiveFile = () => ({ path: "notes/active.md" });
  mark = noticesFrom();
  let formsBefore = modals.length;
  queuedFrom = requests.length;
  await forkCommand.callback();
  assert.deepEqual(notices.slice(mark), ["Open a generated argument.canvas to fork it."]);
  assert.equal(modals.length, formsBefore, "no form opens off a generated canvas");
  assert.deepEqual(postBodiesSince(queuedFrom), []);

  // A scratch canvas is not a fork source either -- forking a fork would copy
  // the PI's hand edits into a second file with no way back to the render.
  plugin.app.workspace.getActiveFile = () => ({ path: "projects/alpha/scratch-review.canvas" });
  formsBefore = modals.length;
  await forkCommand.callback();
  assert.equal(modals.length, formsBefore, "a scratch canvas is not a fork source");

  // 29b) On a generated canvas it queues the fork against the *project*, which
  // is derived from the canvas path rather than sent as the canvas path.
  plugin.app.workspace.getActiveFile = () => ({ path: "projects/alpha/argument.canvas" });
  await forkCommand.callback();
  const forkModal = modals.at(-1);
  queuedFrom = requests.length;
  controlNamed(forkModal, "Scratch name").type("  Try Layout!  ");
  await buttonLabeled(forkModal, "Queue fork").click();
  assert.deepEqual(postBodiesSince(queuedFrom).map((body) => body.operation_id), [
    "fork-project-canvas",
    "empirical-event-record",
  ]);
  assert.deepEqual(postBodiesSince(queuedFrom)[0], {
    operation_id: "fork-project-canvas",
    payload: { project_path: "projects/alpha/project.md", name: "Try Layout!" },
    idempotency_key: "",
  });
  assert.equal(forkModal.closed, 1, "a queued fork closes the form");

  // An untouched form keeps the default name, which is the one the engine's
  // own default produces -- so the two cannot drift apart unnoticed.
  await forkCommand.callback();
  const defaultForkModal = modals.at(-1);
  queuedFrom = requests.length;
  await buttonLabeled(defaultForkModal, "Queue fork").click();
  assert.equal(postBodiesSince(queuedFrom)[0].payload.name, "scratch");

  // A name typed as whitespace trims to "", which is the one input the form's
  // own default cannot cover: the field was edited, so the initial value is
  // gone. What goes on the wire is still a usable name, never an empty one.
  await forkCommand.callback();
  const blankForkModal = modals.at(-1);
  controlNamed(blankForkModal, "Scratch name").type("   ");
  queuedFrom = requests.length;
  await buttonLabeled(blankForkModal, "Queue fork").click();
  assert.equal(postBodiesSince(queuedFrom)[0].payload.name, "scratch");

  // 29c) The badge rides `active-leaf-change`, registered for teardown, and
  // reads the row for *this* file rather than the first row served.
  const leafChange = workspaceEvents.find(
    (entry) => entry.plugin === plugin && entry.name === "active-leaf-change",
  );
  assert.ok(leafChange, "the plugin subscribes to active-leaf-change");
  assert.ok(
    (plugin.registeredEvents || []).some((entry) => entry && entry.name === "active-leaf-change"),
    "the subscription is registered so the host can tear it down",
  );
  const forkRow = {
    path: "projects/alpha/scratch-review.canvas",
    added: [
      {
        source_note_path: "notes/support.md",
        link_type: "contradicts",
        target_path: "notes/thesis.md",
      },
      {
        source_note_path: "notes/extra.md",
        link_type: "extends",
        target_path: "notes/thesis.md",
      },
    ],
    removed_count: 1,
    diff_count: 3,
    unresolved: [{ edge_id: "e9", reason: "unknown relation label" }],
  };
  const serveForks = (forks) => (options) =>
    options.url.includes("/project/canvas/forks")
      ? {
          status: 200,
          json: {
            ok: true,
            api_version: "engine-read-api.v1",
            canvas_forks: {
              project_path: "projects/alpha/project.md",
              canvas_path: "projects/alpha/argument.canvas",
              forks,
            },
          },
        }
      : { status: 200, json: SUMMARY_JSON };
  // The decoy row is another fork of the same project with a louder number: a
  // badge reading `forks[0]` would say 9 for a file it is not describing.
  const decoy = {
    path: "projects/alpha/scratch-other.canvas",
    added: [],
    removed_count: 9,
    diff_count: 9,
    unresolved: [],
  };
  plugin.app.workspace.getActiveFile = () => ({ path: "projects/alpha/scratch-review.canvas" });
  respond = serveForks([decoy, forkRow]);
  queuedFrom = requests.length;
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "Memoria fork: 3 edge(s) diverged");
  assert.equal(
    requests[queuedFrom].url,
    "http://127.0.0.1:43210/project/canvas/forks?project_path=projects%2Falpha%2Fproject.md",
  );
  assert.equal(requests[queuedFrom].method, "GET");
  // Rendered beside the connection pill, never in place of it.
  assert.equal(plugin.statusBar.children.length, 3);
  assert.ok(plugin.statusBar.children[1].text.startsWith("Memoria · "));
  assert.deepEqual(plugin.statusBar.children.at(-1), {
    tag: "span",
    cls: "memoria-pill-text",
    text: " · Memoria fork: 3 edge(s) diverged",
  });

  // 29d) The other three badge states, each a different sentence.
  respond = serveForks([{ ...forkRow, added: [], removed_count: 0, diff_count: 0 }]);
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "Memoria fork: in sync");
  respond = serveForks([{ path: forkRow.path, error: "unreadable scratch canvas" }]);
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "Memoria fork: unreadable");
  // A project whose fork list omits this file leaves no stale badge behind.
  respond = serveForks([decoy]);
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "");
  assert.equal(plugin.statusBar.children.length, 2, "a cleared badge draws nothing");
  // Nor does a leaf change onto an ordinary note issue a read at all.
  respond = serveForks([decoy, forkRow]);
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "Memoria fork: 3 edge(s) diverged");
  plugin.app.workspace.getActiveFile = () => ({ path: "notes/active.md" });
  queuedFrom = requests.length;
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "");
  assert.deepEqual(requests.slice(queuedFrom), []);
  // A dead engine clears the badge instead of freezing yesterday's number.
  plugin.app.workspace.getActiveFile = () => ({ path: "projects/alpha/scratch-review.canvas" });
  respond = serveForks([decoy, forkRow]);
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "Memoria fork: 3 edge(s) diverged");
  respond = () => ({ status: 503, json: { ok: true } });
  await leafChange.handler();
  assert.equal(plugin.forkBadge, "");

  // 29e) Graduation queues one `curate-note-link` per added edge, each under a
  // key naming the edge, so re-running after a partial failure coalesces
  // instead of writing the same relation twice.
  respond = serveForks([decoy, forkRow]);
  queuedFrom = requests.length;
  mark = noticesFrom();
  await graduateCommand.callback();
  assert.deepEqual(postBodiesSince(queuedFrom), [
    {
      operation_id: "curate-note-link",
      payload: {
        source_note_path: "notes/support.md",
        link_type: "contradicts",
        target_path: "notes/thesis.md",
        reason: "graduated from projects/alpha/scratch-review.canvas",
      },
      idempotency_key:
        "graduate:projects/alpha/scratch-review.canvas:notes/support.md:contradicts:notes/thesis.md",
    },
    {
      operation_id: "curate-note-link",
      payload: {
        source_note_path: "notes/extra.md",
        link_type: "extends",
        target_path: "notes/thesis.md",
        reason: "graduated from projects/alpha/scratch-review.canvas",
      },
      idempotency_key:
        "graduate:projects/alpha/scratch-review.canvas:notes/extra.md:extends:notes/thesis.md",
    },
  ]);
  // The unresolved rows are counted out loud: an edge the engine could not
  // read is a relation that silently did not happen.
  assert.deepEqual(notices.slice(mark), [
    "Memoria queued 2 link edge(s); skipped 1 unresolved.",
  ]);

  // 29f) Nothing graduates off an unreadable fork or off a non-scratch file.
  respond = serveForks([{ path: forkRow.path, error: "unreadable scratch canvas" }]);
  queuedFrom = requests.length;
  mark = noticesFrom();
  await graduateCommand.callback();
  assert.deepEqual(notices.slice(mark), ["Memoria could not read this scratch canvas."]);
  assert.deepEqual(postBodiesSince(queuedFrom), []);

  plugin.app.workspace.getActiveFile = () => ({ path: "projects/alpha/argument.canvas" });
  queuedFrom = requests.length;
  mark = noticesFrom();
  await graduateCommand.callback();
  assert.deepEqual(notices.slice(mark), ["Open a scratch-*.canvas to graduate its edges."]);
  assert.deepEqual(postBodiesSince(queuedFrom), []);
  respond = null;
} finally {
  globalThis.setTimeout = realSetTimeout;
  delete globalThis.document;
  delete globalThis.window;
  Module._load = originalLoad;
}
