import assert from "node:assert/strict";
import { createRequire } from "node:module";
import Module from "node:module";

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
};

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
    class Notice {
      constructor(message) {
        notices.push(String(message));
      }
    }
    return {
      AbstractInputSuggest: Base,
      ItemView: Base,
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
} finally {
  globalThis.setTimeout = realSetTimeout;
  delete globalThis.document;
  delete globalThis.window;
  Module._load = originalLoad;
}
