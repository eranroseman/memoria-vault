const SURFACES = new Set(["obsidian"]);
const WORKFLOWS = new Set([
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
  "operation",
]);
const DECISIONS = new Set(["accept", "reject", "edit", "defer", "override", "abandon"]);
const OUTCOMES = new Set([
  "connected",
  "queued",
  "flushed",
  "kept-artifact",
  "fallback",
  "exported",
  "blocked",
  "failed",
  "stopped",
]);
const REASON_CODES = new Set([
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
  "other",
]);
const BASE_REQUIRED_FIELDS = new Set([
  "event_id",
  "event_type",
  "timestamp",
  "session_id",
  "surface",
]);
const EVENT_REQUIRED_FIELDS = {
  "session.started": new Set(["workflow"]),
  "session.stopped": new Set(["workflow", "outcome", "duration_s"]),
  "http.connected": new Set(["workflow", "outcome"]),
  "view.opened": new Set(["workflow"]),
  "operation.queued": new Set(["workflow", "outcome"]),
  "disposition.recorded": new Set(["workflow", "decision", "reason_code"]),
  "fallback.recorded": new Set(["workflow", "outcome", "reason_code"]),
  "export.attempted": new Set(["workflow", "variant", "outcome", "reason_code"]),
};
const ALLOWED_FIELDS = new Set([
  ...BASE_REQUIRED_FIELDS,
  "workflow",
  "decision",
  "outcome",
  "reason_code",
  "duration_s",
  "project_id",
  "item_type",
  "item_id",
  "variant",
]);
const ENUMS = {
  surface: SURFACES,
  workflow: WORKFLOWS,
  decision: DECISIONS,
  outcome: OUTCOMES,
  reason_code: REASON_CODES,
};
const OPAQUE_ID_FIELDS = new Set(["session_id", "project_id", "item_id"]);

function validateEvent(payload) {
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
    throw new Error(`event_type must be one of: ${Object.keys(EVENT_REQUIRED_FIELDS).sort().join(", ")}`);
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
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(event.event_id)) {
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

function sanitizeItemId(value) {
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
  return value === undefined || value === null || (typeof value === "string" && !value.trim());
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
  return (
    value.includes("/") ||
    value.includes("\\") ||
    value.includes("..") ||
    value.includes("://") ||
    value.startsWith("~") ||
    value.startsWith(".") ||
    value.startsWith("file:")
  );
}

function hash64(value) {
  let hash = 0xcbf29ce484222325n;
  for (const char of value) {
    hash ^= BigInt(char.codePointAt(0));
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, "0");
}

module.exports = { sanitizeItemId, validateEvent };
