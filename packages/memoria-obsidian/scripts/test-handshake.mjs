import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const {
  HANDSHAKE_TIMEOUT_MS,
  RESPAWN_LIMIT,
  buildHandshakeArgv,
  classifySpawnError,
  createRespawnGate,
  parseHandshake,
} = require("../../../src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/handshake.js");

const COORDINATES = {
  port: 1,
  token: "t",
  boot_id: "b",
  engine_version: "0.1.0-alpha.21",
  pid: 4242,
};

test("buildHandshakeArgv splits multi-word engine commands", () => {
  assert.deepEqual(buildHandshakeArgv("memoria", "/v"), {
    command: "memoria",
    args: ["handshake", "--vault", "/v", "--spawn", "--json"],
  });
  assert.deepEqual(buildHandshakeArgv("wsl memoria", "/v"), {
    command: "wsl",
    args: ["memoria", "handshake", "--vault", "/v", "--spawn", "--json"],
  });
});

// Producer state: settings persisted before this plan added the engine-command
// field (contract 8 migrates nothing), so the first handshake reads `undefined`;
// a user who blanks the field produces the whitespace case.
test("buildHandshakeArgv falls back to bare `memoria` when the setting is absent or blank", () => {
  assert.deepEqual(buildHandshakeArgv(undefined, "/v"), {
    command: "memoria",
    args: ["handshake", "--vault", "/v", "--spawn", "--json"],
  });
  assert.equal(buildHandshakeArgv("", "/v").command, "memoria");
  assert.equal(buildHandshakeArgv("  ", "/v").command, "memoria");
});

test("parseHandshake returns coordinates and rejects partial payloads", () => {
  const stdout = JSON.stringify({
    schema: 1,
    port: 43210,
    token: "tok",
    boot_id: "boot-1",
    engine_version: "0.1.0-alpha.21",
    pid: 4242,
  });
  assert.deepEqual(parseHandshake(stdout), {
    port: 43210,
    token: "tok",
    bootId: "boot-1",
    engineVersion: "0.1.0-alpha.21",
    pid: 4242,
  });
  assert.throws(() => parseHandshake("not json"), /handshake: stdout is not JSON/);
  assert.throws(() => parseHandshake("{}"), /handshake: missing port/);
  assert.throws(
    () => parseHandshake(JSON.stringify({ port: 1 })),
    /handshake: missing token/,
  );
  assert.throws(
    () => parseHandshake(JSON.stringify({ port: 1, token: "t" })),
    /handshake: missing boot_id/,
  );
  assert.throws(
    () => parseHandshake(JSON.stringify({ port: 1, token: "t", boot_id: "b" })),
    /handshake: missing engine_version/,
  );
  // Producer state: an engine older than BOOT-A.8, which printed the handshake
  // object without `pid`. No plugin action may use a PID before this rejection.
  assert.throws(
    () =>
      parseHandshake(
        JSON.stringify({
          port: 1,
          token: "t",
          boot_id: "b",
          engine_version: "0.1.0-alpha.21",
        }),
      ),
    /handshake: missing pid/,
  );
  for (const pid of [0, -1, 1.5]) {
    assert.throws(
      () => parseHandshake(JSON.stringify({ ...COORDINATES, pid })),
      /handshake: missing pid/,
    );
  }
});

// Producer state: a corrupt or truncated runtime.json surfaces a port that is
// not a usable TCP port; the plugin must refuse it rather than dial it.
test("parseHandshake rejects a nonpositive or fractional port", () => {
  for (const port of [0, -1, 1.5]) {
    assert.throws(
      () => parseHandshake(JSON.stringify({ ...COORDINATES, port })),
      /handshake: missing port/,
    );
  }
});

// Producer state: the spawned engine exited before printing anything, so the
// collected stdout is empty (or was never assigned at all).
test("parseHandshake refuses empty stdout instead of dereferencing it", () => {
  assert.throws(() => parseHandshake(""), /handshake: stdout is not JSON/);
  assert.throws(() => parseHandshake(null), /handshake: stdout is not JSON/);
  assert.throws(() => parseHandshake(undefined), /handshake: stdout is not JSON/);
});

// Producer state: main.js arms this timeout on the spawned handshake. Nothing
// else pins it, so a drift to 100ms or 100s would otherwise ship unnoticed.
test("the handshake spawn timeout is 10 seconds", () => {
  assert.equal(HANDSHAKE_TIMEOUT_MS, 10000);
});

test("classifySpawnError maps ENOENT to engine-missing", () => {
  const enoent = Object.assign(new Error("spawn memoria ENOENT"), { code: "ENOENT" });
  assert.equal(classifySpawnError(enoent), "engine-missing");
  assert.equal(classifySpawnError(new Error("exit 1")), "spawn-failed");
  assert.equal(classifySpawnError(null), "spawn-failed");
});

test("respawn gate allows 3 attempts in 3 minutes, then reopens as the window slides", () => {
  let clock = 0;
  const gate = createRespawnGate(() => clock);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), false);
  assert.equal(gate.exhausted(), true);
  clock = 180001;
  assert.equal(gate.exhausted(), false);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(RESPAWN_LIMIT, 3);
});

// A crash-loop throttle is only a throttle for as long as its window lasts, and
// a single reopening clock past the end cannot tell three minutes from one
// millisecond. Pin both sides of the boundary instead.
test("respawn gate holds the full window and reopens exactly at its end", () => {
  let clock = 0;
  const gate = createRespawnGate(() => clock);
  gate.tryAcquire();
  gate.tryAcquire();
  gate.tryAcquire();
  clock = 179999;
  assert.equal(gate.exhausted(), true);
  assert.equal(gate.tryAcquire(), false);
  clock = 180000;
  assert.equal(gate.exhausted(), false);
});

// Producer state: the respawn path calls tryAcquire on every failed poll while
// only the pill calls exhausted(), so the window must slide for a caller that
// never asks whether the gate is exhausted.
test("respawn gate reopens for a caller that only calls tryAcquire", () => {
  let clock = 0;
  const gate = createRespawnGate(() => clock);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), false);
  clock = 180001;
  assert.equal(gate.tryAcquire(), true);
});

// Producer state: main.js constructs the gate with no argument, so the default
// clock is the one that runs in the plugin.
test("respawn gate runs on a real clock when none is injected", () => {
  const gate = createRespawnGate();
  assert.equal(gate.exhausted(), false);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), true);
  assert.equal(gate.tryAcquire(), false);
  assert.equal(gate.exhausted(), true);
});
