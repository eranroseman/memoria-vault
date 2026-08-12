import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

// The pill states an "as of" in the PI's local time (U3 section 3). Under CI's
// TZ=UTC the local and UTC clocks coincide and every local-vs-UTC assertion
// below loses its power, so pin a zone that is neither: the half-hour offset
// moves the hour *and* the minute, so a UTC read shows up in both fields.
process.env.TZ = "Asia/Kolkata";
assert.equal(new Date(0).getHours(), 5, "TZ pin did not take effect");

const require = createRequire(import.meta.url);
const { PILL_STATES, computeNextPollDelay, computePill, formatAsOf } = require("../src/pill.js");

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
    computePill({
      connection: "token-invalid",
      openCount: 0,
      lastPollAt: 0,
      missingCredential: "",
    }),
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
  // The instant is stated in UTC and the expectation in local time, so the test
  // cannot be satisfied by the same UTC call it is meant to reject: 03:35Z is
  // 09:05 in the pinned zone, and both fields need their zero pad.
  assert.equal(formatAsOf(Date.UTC(2026, 0, 2, 3, 35)), "09:05");
});

test("poll cadence is 30s active / 2m idle", () => {
  assert.equal(computeNextPollDelay(true), 30000);
  assert.equal(computeNextPollDelay(false), 120000);
});
