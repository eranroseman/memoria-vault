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
const secrets = new Map();
const originalLoad = Module._load;
Module._load = function load(request, parent, isMain) {
  if (request === "obsidian") {
    class Plugin {
      constructor() {
        this.app = {
          secretStorage: {
            setSecret: (id, secret) => secrets.set(id, secret),
            getSecret: (id) => secrets.get(id) || null,
          },
        };
      }

      async loadData() {
        return {};
      }

      async saveData() {}

      addStatusBarItem() {
        return { setText() {} };
      }

      addSettingTab() {}

      addCommand() {}
    }
    class Base {
      constructor() {}
    }
    class Setting {}
    return {
      Modal: Base,
      Notice: Base,
      Plugin,
      PluginSettingTab: Base,
      Setting,
      requestUrl: async (requestUrl) => {
        requests.push(requestUrl);
        return { status: 200, json: { ok: true, api_version: "test" } };
      },
    };
  }
  return originalLoad.call(this, request, parent, isMain);
};

try {
  const PluginClass = require("../main.js");
  const plugin = new PluginClass();
  await plugin.onload();
  plugin.settings.enabled = true;
  await plugin.setToken("sandbox-token");

  assert.equal(plugin.settings.hasToken, true);
  assert.equal(await plugin.token(), "sandbox-token");

  await plugin.getJson("/status");
  assert.deepEqual(requests[0], {
    url: "http://127.0.0.1:8765/status",
    method: "GET",
    headers: { Authorization: "Bearer sandbox-token" },
    throw: false,
  });

  await plugin.postOperation("demo-operation", { ok: true }, "demo-key");
  assert.equal(requests[1].url, "http://127.0.0.1:8765/operation/run");
  assert.equal(requests[1].method, "POST");
  assert.equal(requests[1].contentType, "application/json");
  assert.deepEqual(requests[1].headers, { Authorization: "Bearer sandbox-token" });
  assert.deepEqual(JSON.parse(requests[1].body), {
    operation_id: "demo-operation",
    payload: { ok: true },
    idempotency_key: "demo-key",
    actor: "agent",
  });
} finally {
  Module._load = originalLoad;
}
