import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { PILL_STATES, computeNextPollDelay, computePill, formatAsOf } = require("../pill.js");

const at = new Date(2026, 6, 15, 14, 2).getTime(); // local 14:02

test("all six pill states are reachable and worded per the U3 table", () => {
  assert.deepEqual(PILL_STATES, [
    "connected",
    "stale",
    "server-down",
    "token-invalid",
    "engine-missing",
    "key-needed",
  ]);
  assert.deepEqual(
    computePill({ connection: "connected", openCount: 4, lastPollAt: at, missingCredential: "" }),
    { state: "connected", text: "Memoria · 4 open", tone: "green" },
  );
  assert.deepEqual(
    computePill({ connection: "stale", openCount: 4, lastPollAt: at, missingCredential: "" }),
    { state: "stale", text: "Memoria · 4 open · as of 14:02", tone: "amber" },
  );
  assert.deepEqual(
    computePill({ connection: "server-down", openCount: 0, lastPollAt: 0, missingCredential: "" }),
    { state: "server-down", text: "Memoria · server down", tone: "red" },
  );
  assert.deepEqual(
    computePill({ connection: "token-invalid", openCount: 0, lastPollAt: 0, missingCredential: "" }),
    { state: "token-invalid", text: "Memoria · token invalid", tone: "red" },
  );
  assert.deepEqual(
    computePill({
      connection: "engine-missing",
      openCount: 0,
      lastPollAt: 0,
      missingCredential: "",
    }),
    { state: "engine-missing", text: "Memoria · engine missing", tone: "gray" },
  );
  assert.deepEqual(
    computePill({
      connection: "connected",
      openCount: 4,
      lastPollAt: at,
      missingCredential: "KILOCODE_API_KEY",
    }),
    { state: "key-needed", text: "Memoria · 4 open · key needed", tone: "accent" },
  );
  assert.deepEqual(
    computePill({ connection: "stale", openCount: 0, lastPollAt: 0, missingCredential: "" }),
    { state: "stale", text: "Memoria · connecting…", tone: "amber" },
  );
});

// Producer state: the last successful summary named a missing required
// credential and a later poll then failed, so the pill holds a retained
// credential name together with a broken connection. The connection fault wins:
// the count beside the key nag would otherwise read as current.
test("a retained missing credential never masks a connection fault", () => {
  for (const connection of ["server-down", "token-invalid", "engine-missing", "stale"]) {
    assert.equal(
      computePill({
        connection,
        openCount: 4,
        lastPollAt: at,
        missingCredential: "KILOCODE_API_KEY",
      }).state,
      connection,
    );
  }
});

test("formatAsOf zero-pads local HH:MM", () => {
  assert.equal(formatAsOf(new Date(2026, 0, 2, 9, 5).getTime()), "09:05");
});

test("poll cadence is 30s active / 2m idle", () => {
  assert.equal(computeNextPollDelay(true), 30000);
  assert.equal(computeNextPollDelay(false), 120000);
});
