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
const opened = [];

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
            on: () => ({}),
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

      registerEvent() {}

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
    return {
      AbstractInputSuggest: Base,
      ItemView: ItemViewStub,
      Modal: Base,
      Notice,
      Plugin,
      PluginSettingTab: Base,
      Setting: Base,
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
    ["ATTENTION", "7 open · as of 09:05"],
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
  const button = withClass(root, "memoria-action")[0];
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
} finally {
  globalThis.setTimeout = realSetTimeout;
  delete globalThis.document;
  delete globalThis.window;
  Module._load = originalLoad;
}
