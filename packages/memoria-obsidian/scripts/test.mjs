import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { sanitizeItemId, validateEvent } = require("../src/schema.js");

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
